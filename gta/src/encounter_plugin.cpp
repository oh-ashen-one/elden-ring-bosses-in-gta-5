#include <atomic>
#include <array>
#include <cstdio>
#include <cwchar>
#include <cstring>
#include "scripthook.hpp"
#include "combat.hpp"

extern "C" __declspec(dllimport) int ergt_runtime_dependency();

namespace {
ergt::ScriptHook hook;
HMODULE module_handle = nullptr;
FILE* log_file = nullptr;
bool registered = false;
std::atomic<unsigned> commands{0};
enum : unsigned { select_next=1, spawn=2, clear_all=4, toggle_combat=8, loadout=16, helicopter=32, import_diagnostics=64 };
int selected = 0;
bool fighting = false;
constexpr char controls[] = "1 select | 2 spawn | 3 clear | 4 combat | 5 loadout | 6 helicopter | 7 import check";
char notice[192] = "Choose a creature with 1, then press 2 to spawn. Combat starts OFF.";

struct Actor {
    int entity = 0;
    const ergt::CreatureSpec* spec = nullptr;
    ergt::Combat combat;
    ergt::CombatState previous_state = ergt::CombatState::idle;
    int native_health = 0;
    std::uint32_t last_fallback = 0;
    std::uint32_t last_log = 0;
    float damage_since_log = 0;
    bool animation_failed = false;
};
std::array<Actor, 3> actors;
std::array<bool, ergt::creatures.size()> failed_creatures{};
struct Pending {
    bool active = false;
    bool vehicle = false;
    int preset = 0;
    std::uint32_t hash = 0;
    std::uint32_t started = 0;
    bool model_ready = false;
} pending;
int owned_helicopter = 0;
bool reference_probe_used = false;
bool reference_probe_active = false;
std::uint32_t reference_probe_hash = 0;
std::uint32_t reference_probe_started = 0;
constexpr std::array<const char*,6> diagnostic_models={"prop_box_wood01a","ergt_malenia","ergt_test_sta","ergt_test_dyn","ergt_test_nocol","ergt_test_rigid"};
int diagnostic_index=-1;
std::uint32_t diagnostic_hash=0,diagnostic_started=0;
wchar_t diagnostic_request_path[32768]{};
std::uint32_t last_request_check=0;

bool exists(int entity) { return entity && hook.invoke<int>(0x7239B21A38F536BAULL, entity); }
ergt::Vec3 coords(int entity) {
    auto p = hook.invoke<ergt::NativeVector>(0x3FEF770D40960D5AULL, entity, true);
    return {p.x,p.y,p.z};
}
bool finite(ergt::Vec3 p) { return std::isfinite(p.x) && std::isfinite(p.y) && std::isfinite(p.z); }
std::uint32_t hash(const char* name) { return hook.invoke<std::uint32_t>(0xD24D37CC275948CCULL, name); }

void record(const char* event, int entity=0, float value=0) {
    if (!log_file) return;
    std::fprintf(log_file, "tick=%llu event=%s entity=%d value=%.2f\n",
                 static_cast<unsigned long long>(GetTickCount64()),event,entity,value);
    std::fflush(log_file);
}
void initialize_log() {
    wchar_t path[32768]{};
    auto length=GetModuleFileNameW(module_handle,path,32768);
    if (!length || length>=32768) return;
    auto slash=std::wcsrchr(path,L'\\');
    if (!slash || slash-path>32700) return;
    std::wcscpy(slash+1,L"EldenLosSantos.log");
    log_file=_wfopen(path,L"a");
    std::wcscpy(slash+1,L"EldenLosSantos.import-check.request");
    std::wcscpy(diagnostic_request_path,path);
    record("loaded_import_diagnostics_v6_owner_verification_pending");
}
void text(float x,float y,const char* line,float scale=0.32f) {
    hook.invoke(0x66E0276CC5F6B9DAULL,0);
    hook.invoke(0x07C837F9A01C34C9ULL,0.0f,scale);
    hook.invoke(0xBE6B23FFA53FB442ULL,255,255,255,235);
    hook.invoke(0xC02F4DBFB51D988BULL,false);
    hook.invoke(0x2513DFB0FB8400FEULL);
    hook.invoke(0x25FBB336DF1804CBULL,"STRING");
    hook.invoke(0x6C188BE134E074AAULL,line);
    hook.invoke(0xCD015E5BB0D96A57ULL,x,y,0);
}
void marker(ergt::Vec3 p) {
    hook.invoke(0x28477EC23D892089ULL,28,p.x,p.y,p.z,
                0.0f,0.0f,0.0f,0.0f,0.0f,0.0f,3.5f,3.5f,3.5f,
                255,55,40,90,false,false,2,false,static_cast<const char*>(nullptr),static_cast<const char*>(nullptr),false);
}
void animate(Actor& actor,const char* clip,bool loop) {
    if (!hook.invoke<int>(0xD031A9162D01088CULL,actor.spec->dictionary)) return;
    if (!hook.invoke<int>(0x7FB218262B810701ULL,actor.entity,clip,actor.spec->dictionary,4.0f,loop,true,false,0.0f,0)) {
        if (!actor.animation_failed) record("animation_call_failed",actor.entity);
        actor.animation_failed=true;
    }
}
void remove_actor(Actor& actor) {
    if (exists(actor.entity) && actor.spec &&
        hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.entity)==hash(actor.spec->model)) {
        int entity=actor.entity;
        hook.invoke(0x539E0AE3E6634B9FULL,&entity);
    }
    actor=Actor{};
}
void clear() {
    if (pending.active) { hook.invoke(0xE532F5D78798DAABULL,pending.hash); pending={}; }
    if (diagnostic_index>=0) {
        if (diagnostic_hash) hook.invoke(0xE532F5D78798DAABULL,diagnostic_hash);
        diagnostic_hash=0;diagnostic_index=-1;record("import_diagnostics_cancelled");
    }
    if (reference_probe_active) {
        hook.invoke(0xE532F5D78798DAABULL,reference_probe_hash); reference_probe_active=false;
    }
    for (auto& actor:actors) remove_actor(actor);
    std::snprintf(notice,sizeof(notice),"Creatures cleared. Your helicopter is kept.");
    record("clear_creatures");
}
void begin_spawn(bool vehicle,std::uint32_t now) {
    if (pending.active || diagnostic_index>=0) return;
    if (!vehicle && failed_creatures[selected]) {
        std::snprintf(notice,sizeof(notice),"This creature failed. Retry is locked for this session; its error is in the log.");
        return;
    }
    if (vehicle && exists(owned_helicopter)) {
        std::snprintf(notice,sizeof(notice),"Your helicopter already exists nearby."); return;
    }
    if (!vehicle && std::all_of(actors.begin(),actors.end(),[](const Actor& a){return a.entity!=0;})) {
        std::snprintf(notice,sizeof(notice),"Three creatures are active. 3 clears them."); return;
    }
    const auto& spec=ergt::creatures[selected];
    const auto model_hash=hash(vehicle?"buzzard":spec.model);
    if (!hook.invoke<int>(0xC0296A2EDF545E92ULL,model_hash) || !hook.invoke<int>(0x35B9E0803292B641ULL,model_hash)) {
        std::snprintf(notice,sizeof(notice),"Model %s unavailable. Check the ERGT DLC installation.",vehicle?"buzzard":spec.model);
        record("model_unavailable",0,static_cast<float>(selected)); return;
    }
    pending={true,vehicle,selected,model_hash,now};
    if (log_file) {
        std::fprintf(log_file,"event=spawn_requested model=%s hash=%08x preset=%d\n",vehicle?"buzzard":spec.model,model_hash,selected);
        std::fflush(log_file);
    }
    record("request_model_begin",0,static_cast<float>(selected));
    hook.invoke(0x963D27A58DF860ACULL,model_hash);
    record("request_model_returned");
    // Stage animation loading after model streaming, to localize loading faults.
    std::snprintf(notice,sizeof(notice),"Loading %s...",vehicle?"helicopter":spec.label);
}
void finish_spawn(int player,std::uint32_t now) {
    if (!pending.active) return;
    const auto& spec=ergt::creatures[pending.preset];
    if (now-pending.started>12000) {
        if (!pending.vehicle) failed_creatures[pending.preset]=true;
        record(pending.model_ready?"animation_streaming_timeout":"model_streaming_timeout",0,static_cast<float>(pending.preset));
        hook.invoke(0xE532F5D78798DAABULL,pending.hash); pending={};
        std::snprintf(notice,sizeof(notice),"Asset streaming timed out. See EldenLosSantos.log."); record("streaming_timeout"); return;
    }
    if (!hook.invoke<int>(0x98A4EB5D89A0C952ULL,pending.hash)) return;
    if (!pending.model_ready) {
        pending.model_ready=true;
        record("model_streaming_ready",0,static_cast<float>(pending.preset));
        if (!pending.vehicle) {
            record("request_animation_begin",0,static_cast<float>(pending.preset));
            hook.invoke(0xD3BD40951412FEF6ULL,spec.dictionary);
            record("request_animation_returned");
        }
    }
    if (!pending.vehicle && !hook.invoke<int>(0xD031A9162D01088CULL,spec.dictionary)) return;
    auto p=hook.invoke<ergt::NativeVector>(0x1899F328B0E12848ULL,player,pending.vehicle?12.0f:0.0f,18.0f,0.0f);
    if (!finite({p.x,p.y,p.z})) {
        record("invalid_spawn_position");
        hook.invoke(0xE532F5D78798DAABULL,pending.hash); pending={};
        std::snprintf(notice,sizeof(notice),"Invalid spawn position. Move outdoors and retry."); return;
    }
    float ground=0;
    if (!hook.invoke<int>(0xC906A7DAB05C8D2BULL,p.x,p.y,p.z+100.0f,&ground,false,false) || !std::isfinite(ground)) {
        hook.invoke(0xE532F5D78798DAABULL,pending.hash); pending={};
        std::snprintf(notice,sizeof(notice),"No ground found. Move to a clear outdoor area."); return;
    }
    if (pending.vehicle) {
        owned_helicopter=hook.invoke<int>(0xAF35D0D2583051B0ULL,pending.hash,p.x,p.y,ground+1.0f,0.0f,false,true,false);
        if (exists(owned_helicopter)) hook.invoke(0xAD738C3085FE7E11ULL,owned_helicopter,true,true);
        std::snprintf(notice,sizeof(notice),exists(owned_helicopter)?"Armed helicopter placed nearby.":"GTA could not create the helicopter. See the log.");
        record(exists(owned_helicopter)?"helicopter_created":"helicopter_create_failed",owned_helicopter);
    } else {
        auto slot=std::find_if(actors.begin(),actors.end(),[](const Actor& a){return a.entity==0;});
        if (slot!=actors.end()) {
            const float z=ground-spec.minimum_z+0.05f;
            // These are local drawable objects, not networked door entities.
            record("create_object_begin",0,static_cast<float>(pending.preset));
            int entity=hook.invoke<int>(0x9A294B2138ABB884ULL,pending.hash,p.x,p.y,z,false,true,false,0);
            record("create_object_no_offset_result",entity,static_cast<float>(pending.preset));
            if (log_file) {
                const int loaded=hook.invoke<int>(0x98A4EB5D89A0C952ULL,pending.hash);
                const int ped=hook.invoke<int>(0x75816577FEA6DAD5ULL,pending.hash);
                const int vehicle_model=hook.invoke<int>(0x19AAC8F07BFEC53EULL,pending.hash);
                std::fprintf(log_file,"event=spawn_result model=%s hash=%08x entity=%d model_loaded=%d is_ped=%d is_vehicle=%d xyz=%.3f,%.3f,%.3f\n",
                    spec.model,pending.hash,entity,loaded,ped,vehicle_model,p.x,p.y,z);
                std::fflush(log_file);
            }
            if (exists(entity)) {
                slot->entity=entity; slot->spec=&spec; slot->combat.reset(&spec);
                hook.invoke(0xAD738C3085FE7E11ULL,entity,true,true);
                hook.invoke(0x1A9205C1B9EE827FULL,entity,true,true);
                hook.invoke(0x1718DE8E3F2823CAULL,entity,true);
                hook.invoke(0x4A4722448F18EEF5ULL,entity,true);
                hook.invoke(0x3882114BDE571AD4ULL,entity,false,false);
                hook.invoke(0x1760FFA8AB074D66ULL,entity,true);
                hook.invoke(0x166E7CF68597D8B5ULL,entity,10000);
                hook.invoke(0x6B76DC1F3AE6E6A3ULL,entity,10000,0,0u);
                slot->native_health=hook.invoke<int>(0xEEF059FAD016D209ULL,entity);
                animate(*slot,spec.idle_clip,true);
                std::snprintf(notice,sizeof(notice),"%s spawned. Combat %s (4).",spec.label,fighting?"ON":"OFF");
                record("creature_created",entity,slot->native_health);
            } else {
                failed_creatures[pending.preset]=true;
                std::snprintf(notice,sizeof(notice),"Could not create %s. Retry locked; details in EldenLosSantos.log.",spec.label);
                record("create_object_failed",entity,static_cast<float>(pending.preset));
                // A one-time A/B diagnostic after an OWNER-triggered failure.
                // Use the same stock prop as universal-modder's working bridge;
                // remove it immediately, and never present it as a creature.
                if (!reference_probe_used) {
                    reference_probe_used=true; reference_probe_active=true; reference_probe_started=now;
                    reference_probe_hash=hash("prop_box_wood01a");
                    hook.invoke(0x963D27A58DF860ACULL,reference_probe_hash);
                    record("reference_object_probe_requested");
                }
            }
        }
    }
    hook.invoke(0xE532F5D78798DAABULL,pending.hash); pending={};
}

void tick_reference_probe(int player,std::uint32_t now) {
    if (!reference_probe_active) return;
    if (hook.invoke<int>(0x98A4EB5D89A0C952ULL,reference_probe_hash)) {
        const auto p=coords(player);
        if (finite(p)) {
            // Below the player, deleted in the same script tick before physics.
            int entity=hook.invoke<int>(0x9A294B2138ABB884ULL,reference_probe_hash,p.x,p.y,p.z-5.0f,false,true,false,0);
            record("reference_object_creation_result",entity);
            if (exists(entity)) hook.invoke(0x539E0AE3E6634B9FULL,&entity);
        }
    } else if (now-reference_probe_started<=3000) return;
    else record("reference_object_streaming_timeout");
    hook.invoke(0xE532F5D78798DAABULL,reference_probe_hash);
    reference_probe_active=false;
}

void diagnostic_next(std::uint32_t now) {
    if (diagnostic_hash) hook.invoke(0xE532F5D78798DAABULL,diagnostic_hash);
    diagnostic_hash=0;
    if (++diagnostic_index>=static_cast<int>(diagnostic_models.size())) {
        diagnostic_index=-1;record("import_diagnostics_complete");
        std::snprintf(notice,sizeof(notice),"Import checks complete. Results saved in EldenLosSantos.log.");return;
    }
    diagnostic_hash=hash(diagnostic_models[diagnostic_index]);diagnostic_started=now;
    hook.invoke(0x963D27A58DF860ACULL,diagnostic_hash);
    std::snprintf(notice,sizeof(notice),"Checking import %d/%zu...",diagnostic_index+1,diagnostic_models.size());
}
void begin_diagnostics(std::uint32_t now) {
    if (diagnostic_index>=0 || pending.active || reference_probe_active || fighting) return;
    if (std::any_of(actors.begin(),actors.end(),[](const Actor& a){return a.entity!=0;})) return;
    diagnostic_index=-1;diagnostic_hash=0;record("import_diagnostics_begin");diagnostic_next(now);
}
void tick_diagnostics(int player,std::uint32_t now) {
    if (diagnostic_index<0) return;
    const char* name=diagnostic_models[diagnostic_index];
    if (!hook.invoke<int>(0x98A4EB5D89A0C952ULL,diagnostic_hash)) {
        if (now-diagnostic_started<5000) return;
        if (log_file) {std::fprintf(log_file,"event=import_check model=%s result=stream_timeout\n",name);std::fflush(log_file);}
        diagnostic_next(now);return;
    }
    const auto p=coords(player);
    if (finite(p)) for (const bool dynamic:{false,true}) {
        int entity=hook.invoke<int>(0x9A294B2138ABB884ULL,diagnostic_hash,p.x,p.y,p.z-5.0f,false,true,dynamic,0);
        const bool valid=exists(entity);
        if (log_file) {
            std::fprintf(log_file,"event=import_check model=%s dynamic=%d entity=%d exists=%d\n",name,dynamic,entity,valid);
            std::fflush(log_file);
        }
        // No animation, combat or persistent actor: remove it within this tick.
        if (valid) hook.invoke(0x539E0AE3E6634B9FULL,&entity);
    }
    diagnostic_next(now);
}
void read_diagnostic_request(std::uint32_t now) {
    if (now-last_request_check<500 || !diagnostic_request_path[0]) return;
    last_request_check=now;
    FILE* request=_wfopen(diagnostic_request_path,L"rb");
    if (!request) return;
    char token[32]{};std::fgets(token,sizeof(token),request);std::fclose(request);
    // A file-only, fixed-command technical test; no listener or arbitrary code.
    if (std::strcmp(token,"CHECK_IMPORTS_ONCE\n")==0 && _wremove(diagnostic_request_path)==0)
        begin_diagnostics(now);
}

void observe_damage(Actor& actor,int player,std::uint32_t now) {
    int health=hook.invoke<int>(0xEEF059FAD016D209ULL,actor.entity);
    float loss=static_cast<float>(std::max(0,actor.native_health-health));
    const bool weapon=hook.invoke<int>(0x131D401334815E94ULL,actor.entity,0u,2)!=0;
    const bool vehicle=hook.invoke<int>(0xDFD5033FDBA0A9C8ULL,actor.entity)!=0;
    if (loss<=0 && (weapon || vehicle) && now-actor.last_fallback>=80) {
        // Some drawable objects report hit flags without reducing native HP.
        // Keep this explicitly logged fallback distinct from measured HP loss.
        if (weapon) {
            auto weapon_hash=hook.invoke<std::uint32_t>(0x0A6DB4965674D243ULL,player);
            std::uint32_t vehicle_weapon=0;
            if (hook.invoke<int>(0x1017582BCD3832DCULL,player,&vehicle_weapon) && vehicle_weapon) weapon_hash=vehicle_weapon;
            loss=hook.invoke<float>(0x3133B907D8B32053ULL,weapon_hash,0u);
            if (!std::isfinite(loss) || loss<=0) loss=200.0f;
        } else loss=180.0f;
        actor.last_fallback=now;
        record(weapon?"weapon_hit_fallback":"vehicle_hit_fallback",actor.entity,loss);
    }
    if (std::isfinite(loss) && loss>0) {
        const float applied=std::min(loss,900.0f);
        actor.combat.damage(applied); actor.damage_since_log+=applied;
        if (now-actor.last_log>=200) {
            record("damage_applied",actor.entity,actor.damage_since_log);
            actor.damage_since_log=0; actor.last_log=now;
        }
    }
    hook.invoke(0xAC678E40BE7C74D2ULL,actor.entity);
    hook.invoke(0xA72CD9CA74A5ECBAULL,actor.entity);
    if (actor.native_health>0 && actor.combat.state()!=ergt::CombatState::defeated)
        hook.invoke(0x6B76DC1F3AE6E6A3ULL,actor.entity,actor.native_health,0,0u);
}
void update_actor(Actor& actor,int player,int vehicle,std::uint32_t now,int dt) {
    if (!actor.entity) return;
    if (!exists(actor.entity)) {
        record("actor_lost_not_a_confirmed_kill",actor.entity); actor=Actor{};
        std::snprintf(notice,sizeof(notice),"A creature disappeared. See the log, then respawn."); return;
    }
    const auto position=coords(actor.entity),target=coords(player);
    if (!finite(position) || !finite(target)) { record("invalid_native_position",actor.entity); return; }
    if (ergt::horizontal_distance(position,target)>500) { remove_actor(actor); return; }
    if (actor.combat.state()!=ergt::CombatState::defeated) observe_damage(actor,player,now);
    const bool alive=!hook.invoke<int>(0x3317DEDB88C95038ULL,player,true);
    const bool clear_sight=hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,vehicle?vehicle:player,17)!=0;
    const bool airborne=hook.invoke<int>(0x298B91AE825E5705ULL,player)!=0;
    auto decision=actor.combat.tick(dt,{position,target,alive,clear_sight,fighting,airborne});
    auto state=actor.combat.state();
    if (state!=actor.previous_state) {
        if (state==ergt::CombatState::chasing) animate(actor,actor.spec->move_clip,true);
        else if (state==ergt::CombatState::melee_windup || state==ergt::CombatState::ranged_windup) animate(actor,actor.spec->attack_clip,false);
        else if (state==ergt::CombatState::idle || state==ergt::CombatState::recovering) animate(actor,actor.spec->idle_clip,true);
        else if (state==ergt::CombatState::defeated) {
            animate(actor,actor.spec->death_clip,false);
            hook.invoke(0x428CA6DBD1094446ULL,actor.entity,true);
            hook.invoke(0x1A9205C1B9EE827FULL,actor.entity,false,false);
            std::snprintf(notice,sizeof(notice),"%s defeated. 3 clears the arena.",actor.spec->label);
            record("defeated",actor.entity);
        }
        actor.previous_state=state;
    }
    if (fighting && state!=ergt::CombatState::defeated && alive) {
        float heading=std::atan2(position.x-target.x,target.y-position.y)*57.2957795f;
        hook.invoke(0x8E2530AA8ADA980EULL,actor.entity,heading);
    }
    if (decision.movement.x!=0 || decision.movement.y!=0) {
        const float x=position.x+decision.movement.x,y=position.y+decision.movement.y;
        float ground=0;
        if (hook.invoke<int>(0xC906A7DAB05C8D2BULL,x,y,position.z+4.0f,&ground,false,false)) {
            const float z=ground-actor.spec->minimum_z+0.05f;
            if (std::abs(z-position.z)<1.5f)
                hook.invoke(0x239A3351AC1DA385ULL,actor.entity,x,y,z,true,true,false);
        }
    }
    if (decision.telegraph) { marker(decision.aim); text(0.35f,0.65f,"Incoming blast - move!",0.5f); }
    if (decision.melee_strike) {
        if (vehicle) {
            const float engine=hook.invoke<float>(0xC45D23BAF168AAB8ULL,vehicle);
            hook.invoke(0x45F6D8EEF34ABEF1ULL,vehicle,engine-actor.spec->melee_damage*5.0f);
        } else hook.invoke(0x697157CED63F18D4ULL,player,actor.spec->melee_damage,true,0,0u);
        record("melee_strike",actor.entity);
    }
    if (decision.ranged_strike) {
        // GTA effect/area damage; original ER projectile/VFX behavior is not ported.
        const auto p=decision.aim;
        hook.invoke(0xE3AD2BDBAEE269ACULL,p.x,p.y,p.z,0,0.35f,true,false,0.15f,false);
        record("ranged_strike",actor.entity);
    }
}

void keyboard(DWORD key,WORD,BYTE,BOOL,BOOL alt,BOOL repeated,BOOL up) {
    if (alt || repeated || up || (GetAsyncKeyState(VK_CONTROL)&0x8000) || (GetAsyncKeyState(VK_SHIFT)&0x8000)) return;
    unsigned flag=0;
    if (key=='1') flag=select_next;
    else if(key=='2') flag=spawn;
    else if(key=='3') flag=clear_all;
    else if(key=='4') flag=toggle_combat;
    else if(key=='5') flag=loadout;
    else if(key=='6') flag=helicopter;
    else if(key=='7') flag=import_diagnostics;
    commands.fetch_or(flag);
}
void run() {
    initialize_log();
    std::uint32_t last=hook.invoke<std::uint32_t>(0x9CD27B0045628463ULL);
    for (;;) {
        const auto now=hook.invoke<std::uint32_t>(0x9CD27B0045628463ULL);
        const int dt=static_cast<int>(std::min<std::uint32_t>(250,now-last)); last=now;
        if (hook.invoke<int>(0x9DE624D2FC4B603FULL) || hook.invoke<int>(0xB0034A223497FFCBULL) ||
            hook.invoke<int>(0x991251AFC3981F84ULL)) {
            commands.store(0); hook.wait(0); continue;
        }
        const int player=hook.invoke<int>(0xD80958FC74E988A6ULL);
        if (!exists(player)) { commands.store(0); hook.wait(0); continue; }
        // Reserve top-row 1-6 for the mod without also selecting GTA weapons.
        // The regular weapon wheel and controller bindings remain available.
        for (const int control:{157,158,160,164,165,159,161}) hook.invoke(0xFE99B66D079CF6BCULL,0,control,true);
        const unsigned command=commands.exchange(0);
        if (command&select_next) selected=(selected+1)%static_cast<int>(ergt::creatures.size());
        if (command&import_diagnostics) begin_diagnostics(now);
        read_diagnostic_request(now);
        if (command&clear_all) clear();
        else if (command&spawn) begin_spawn(false,now);
        if (command&toggle_combat) fighting=!fighting;
        if (command&helicopter) begin_spawn(true,now);
        if (command&loadout) {
            hook.invoke(0xBF0FD6E56C964FCBULL,player,hash("WEAPON_CARBINERIFLE"),360,false,true);
            hook.invoke(0xBF0FD6E56C964FCBULL,player,hash("WEAPON_RPG"),20,false,false);
            std::snprintf(notice,sizeof(notice),"Carbine and RPG supplied.");
        }
        finish_spawn(player,now);
        tick_reference_probe(player,now);
        tick_diagnostics(player,now);
        const int vehicle=hook.invoke<int>(0x9A9112A0FE9A4713ULL,player,false);
        for (auto& actor:actors) update_actor(actor,player,vehicle,now,dt);
        char title[160];
        std::snprintf(title,sizeof(title),"ELDEN LOS SANTOS | Selected: %s | Combat %s",ergt::creatures[selected].label,fighting?"ON":"OFF");
        text(0.02f,0.02f,title,0.4f); text(0.02f,0.057f,notice);
        text(0.02f,0.085f,controls,0.28f);
        int row=0;
        for (const auto& actor:actors) if (actor.entity) {
            float y=0.78f+row*0.06f;
            const char* phase=actor.combat.state()==ergt::CombatState::defeated?"  DEFEATED":actor.combat.enraged()?"  ENRAGED":"";
            char label[128];std::snprintf(label,sizeof(label),"%s  %.0f / %.0f%s",actor.spec->label,actor.combat.health(),actor.spec->maximum_health,phase);
            text(0.25f,y,label);
            hook.invoke(0x3A618A217E5154F0ULL,0.5f,y+0.038f,0.5f,0.009f,30,25,25,225,false);
            float width=0.5f*actor.combat.ratio();
            hook.invoke(0x3A618A217E5154F0ULL,0.25f+width/2,y+0.038f,width,0.009f,180,30,35,245,false);row++;
        }
        hook.wait(0);
    }
}
}

BOOL APIENTRY DllMain(HMODULE module,DWORD reason,LPVOID) {
    if (reason==DLL_PROCESS_ATTACH) {
        module_handle=module;
        if (ergt_runtime_dependency()<0 || !hook.bind()) return FALSE;
        hook.register_script(module,run);hook.register_keyboard(keyboard);registered=true;
    } else if (reason==DLL_PROCESS_DETACH && registered) {
        hook.unregister_keyboard(keyboard);hook.unregister_script(module);
        if(log_file) { std::fclose(log_file);log_file=nullptr; }
    }
    return TRUE;
}
