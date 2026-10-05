#include <atomic>
#include <array>
#include <cstdio>
#include <cwchar>
#include <cstring>
#include "scripthook.hpp"
#include "combat.hpp"
#include "motion.hpp"

extern "C" __declspec(dllimport) int ergt_runtime_dependency();

namespace {
ergt::ScriptHook hook;
HMODULE module_handle = nullptr;
FILE* log_file = nullptr;
bool registered = false;
std::atomic<unsigned> commands{0};
enum : unsigned { select_next=1, spawn=2, clear_all=4, toggle_combat=8, loadout=16, helicopter=32 };
int selected = 0;
bool fighting = true;
constexpr char controls[] = "1 select | 2 spawn | 3 clear | 4 combat | 5 loadout | 6 helicopter";
char notice[192] = "Choose a creature with 1, then press 2 to spawn. Creatures spawn aggressive. 4 pauses combat.";

struct Actor {
    int entity = 0, visual_child = 0;
    const ergt::CreatureSpec* spec = nullptr;
    ergt::Combat combat;
    ergt::CombatState previous_state = ergt::CombatState::idle;
    int native_health = 0;
    std::uint32_t last_fallback = 0;
    std::uint32_t last_log = 0;
    float damage_since_log = 0;
    bool animation_failed = false;
    bool animation_accepted = false;
    const char* active_clip = nullptr;
    bool clip_loop = false;
    int target = 0;
    std::uint32_t target_scan = 0, last_impact = 0, last_attacked = 0;
    std::uint32_t animation_started = 0, animation_sample = 0;
    float previous_phase = -1, trail_health = 1;
    int animation_samples = 0;
    bool playback_repaired = false;
    const ergt::MotionTrack* motion = nullptr;
    ergt::MotionCursor motion_cursor;
    float playback_rate = 1, blade_phase = -1;
    bool melee_clip = false, cleanup_requested = false, cleanup_failed = false;
    unsigned played_reaction = 0;
    bool pose_transition_required = false;
    bool corpse_settled = false;
    float committed_heading = 0;
    ergt::Vec3 blade_origin{}, queued_movement{}, sweep_from{}, sweep_to{};
    std::array<int,3> sweep_handles{};
    bool sweep_blocked = false;
    std::uint32_t sweep_started = 0, sweep_animation = 0;
    std::array<int,513> blade_victims{};
    int blade_victim_count = 0;
    int blade_window = -1;
    float motion_heading = 0;
};
// Initial owner validation uses one large boss at a time. The selector offers
// four choices; concurrent giant encounters need measured streaming/perf work.
std::array<Actor, 1> actors;
std::array<int, 512> nearby_peds{};
int nearby_ped_count = 0;
struct VehicleSample { int entity=0; float speed=0, prior_speed=0; };
std::array<VehicleSample, 128> nearby_vehicles{};
int nearby_vehicle_count = 0;
std::uint32_t last_pool_scan = 0;
std::uint32_t hud_until = 0;

void scan_world(int player, std::uint32_t now) {
    if (now-last_pool_scan<200) return;
    last_pool_scan=now;
    nearby_ped_count=hook.get_all_peds?std::clamp(hook.get_all_peds(nearby_peds.data(),static_cast<int>(nearby_peds.size())),0,512):0;
    if (nearby_ped_count==0) { nearby_peds[0]=player;nearby_ped_count=1; }
    auto old=nearby_vehicles;
    const int old_count=nearby_vehicle_count;
    std::array<int,512> vehicles{};
    int count=hook.get_all_vehicles?std::clamp(hook.get_all_vehicles(vehicles.data(),512),0,512):0;
    nearby_vehicle_count=0;
    const auto centre=hook.invoke<ergt::NativeVector>(0x3FEF770D40960D5AULL,player,true);
    for(int i=0;i<count && nearby_vehicle_count<128;i++) {
        const int e=vehicles[i];
        if(!e || !hook.invoke<int>(0x7239B21A38F536BAULL,e)) continue;
        const auto v=hook.invoke<ergt::NativeVector>(0x3FEF770D40960D5AULL,e,true);
        if(ergt::horizontal_distance({centre.x,centre.y,centre.z},{v.x,v.y,v.z})>100) continue;
        float speed=hook.invoke<float>(0xD5037BA82E12416FULL,e);
        if(!std::isfinite(speed)) continue;
        float previous=speed;
        for(int j=0;j<old_count;j++) if(old[j].entity==e) {previous=old[j].speed;break;}
        nearby_vehicles[nearby_vehicle_count++]={e,speed,previous};
    }
}
std::array<bool, ergt::creatures.size()> failed_creatures{};
struct Pending {
    bool active = false;
    bool vehicle = false;
    int preset = 0;
    std::uint32_t hash = 0;
    std::uint32_t started = 0;
    bool model_ready = false;
    std::uint32_t child_hash=0;
} pending;
void release_pending() {
    if(pending.hash)hook.invoke(0xE532F5D78798DAABULL,pending.hash);
    if(pending.child_hash)hook.invoke(0xE532F5D78798DAABULL,pending.child_hash);
    pending={};
}
int owned_helicopter = 0;
bool reference_probe_used = false;
bool reference_probe_active = false;
std::uint32_t reference_probe_hash = 0;
std::uint32_t reference_probe_started = 0;
constexpr std::array<const char*,5> diagnostic_models={"prop_box_wood01a","ergt_malenia","ergt_radahn","ergt_firegiant","ergt_godfrey"};
int diagnostic_index=-1;
int diagnostic_failures=0;
std::uint32_t diagnostic_hash=0,diagnostic_started=0;
wchar_t diagnostic_request_path[32768]{};
std::uint32_t last_request_check=0;
int review_camera=0,review_view=0,review_weapon_target=0;
std::uint32_t review_weapon_hash=0,review_weapon_deadline=0;
std::uint32_t review_until=0;
void end_review() {
    if(review_weapon_hash)hook.invoke(0xAA08EF13F341C8FCULL,review_weapon_hash);
    review_weapon_hash=0;review_weapon_target=0;
    if(review_camera){
        hook.invoke(0x07E5B515DB0636FCULL,false,false,0,true,false,0);
        hook.invoke(0x865908C81A2C22E9ULL,review_camera,true);
    }
    review_camera=0;review_until=0;
}

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
    record("loaded_encounter_vehicle_review_20261005");
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
    actor.animation_accepted=false;
    if (!hook.invoke<int>(0xD031A9162D01088CULL,actor.spec->dictionary)) {
        record("animation_dictionary_unavailable",actor.entity);return;
    }
    actor.active_clip=clip;actor.clip_loop=loop;
    actor.motion=ergt::find_motion(actor.spec->model,clip);actor.motion_cursor={};
    actor.blade_phase=-1;actor.blade_victim_count=0;actor.queued_movement={};
    actor.blade_window=-1;actor.motion_heading=hook.invoke<float>(0xE83D4F9BA2A38914ULL,actor.entity);
    actor.playback_rate=1;
    if(actor.motion && std::strcmp(clip,actor.spec->move_clip)==0) {
        const float speed=ergt::length(ergt::subtract(actor.motion->samples[actor.motion->count-1].root,actor.motion->samples[0].root))/actor.motion->duration;
        if(speed>0.01f)actor.playback_rate=std::clamp(actor.spec->speed*(actor.combat.enraged()?1.25f:1.0f)/speed,0.25f,2.0f);
    }
    actor.animation_started=hook.invoke<std::uint32_t>(0x9CD27B0045628463ULL);
    actor.animation_sample=actor.animation_started;actor.animation_samples=0;actor.previous_phase=-1;
    actor.playback_repaired=false;
    // Objects need their animated transform updated even when physics sleeps.
    hook.invoke(0xACAD101E1FB66689ULL,actor.entity,true);
    bool accepted=hook.invoke<int>(0x7FB218262B810701ULL,actor.entity,clip,actor.spec->dictionary,4.0f,loop,!loop,false,0.0f,0)!=0;
    hook.invoke(0x28D1A16553C51776ULL,actor.entity,actor.spec->dictionary,clip,actor.playback_rate);
    if(actor.visual_child){
        hook.invoke(0xACAD101E1FB66689ULL,actor.visual_child,true);
        const bool child_ok=hook.invoke<int>(0x7FB218262B810701ULL,actor.visual_child,clip,actor.spec->dictionary,4.0f,loop,!loop,false,0.0f,0)!=0;
        hook.invoke(0x28D1A16553C51776ULL,actor.visual_child,actor.spec->dictionary,clip,actor.playback_rate);
        accepted=accepted&&child_ok;
    }
    actor.animation_accepted=accepted;actor.animation_failed=!accepted;
    if (!accepted) record("animation_call_failed",actor.entity);
    if(log_file) {
        std::fprintf(log_file,"event=animation_started entity=%d clip=%s accepted=%d loop=%d\n",actor.entity,clip,accepted,loop);
        std::fflush(log_file);
    }
}
void observe_animation(Actor& actor,std::uint32_t now) {
    if(!actor.active_clip) return;
    hook.invoke(0x40FDEDB72F8293B2ULL,actor.entity);
    if(actor.animation_samples>=3 || now-actor.animation_sample<350) return;
    actor.animation_sample=now;
    const int playing=hook.invoke<int>(0x1F0B79228E461EC9ULL,actor.entity,actor.spec->dictionary,actor.active_clip,3);
    const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
    if(log_file) {
        const auto p=coords(actor.entity);
        std::fprintf(log_file,"event=animation_sample entity=%d clip=%s playing=%d phase=%.5f sample=%d root_track=%d rate=%.3f xyz=%.3f,%.3f,%.3f\n",actor.entity,actor.active_clip,playing,phase,actor.animation_samples,actor.motion!=nullptr,actor.playback_rate,p.x,p.y,p.z);
        std::fflush(log_file);
    }
    // One bounded recovery only, never restart a healthy looping clip each tick.
    if(actor.clip_loop && actor.animation_samples==1 && (!playing || phase==actor.previous_phase) && !actor.playback_repaired) {
        hook.invoke(0x7FB218262B810701ULL,actor.entity,actor.active_clip,actor.spec->dictionary,4.0f,true,false,false,0.0f,0);
        hook.invoke(0x28D1A16553C51776ULL,actor.entity,actor.spec->dictionary,actor.active_clip,actor.playback_rate);
        actor.motion_cursor={};actor.queued_movement={};
        actor.playback_repaired=true;record("animation_recovery_once",actor.entity);
    }
    actor.previous_phase=phase;actor.animation_samples++;
}
void remove_actor(Actor& actor) {
    actor.cleanup_requested=true;
    // Poll owned async casts to completion before releasing the Actor slot.
    // Repeated clear/reset cannot leak shape-test handles.
    bool pending_cast=false;
    for(auto& handle:actor.sweep_handles)if(handle){
        int hit=0,entity=0;ergt::NativeVector end{},normal{};
        if(hook.invoke<int>(0x3D87450E15D98694ULL,handle,&hit,&end,&normal,&entity)==1)pending_cast=true;
        else handle=0;
    }
    if(pending_cast)return;
    if(actor.visual_child && exists(actor.visual_child) && actor.spec && actor.spec->visual_child && hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.visual_child)==hash(actor.spec->visual_child)){
        int child=actor.visual_child;hook.invoke(0x539E0AE3E6634B9FULL,&child);
        if(exists(actor.visual_child)){actor.cleanup_failed=true;record("visual_child_cleanup_failed",actor.visual_child);return;}
    }
    actor.visual_child=0;
    if (exists(actor.entity) && actor.spec &&
        hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.entity)==hash(actor.spec->model)) {
        int entity=actor.entity;
        hook.invoke(0x539E0AE3E6634B9FULL,&entity);
        if(exists(actor.entity)){record("creature_cleanup_failed",actor.entity);actor.cleanup_failed=true;return;}
        record("creature_removed",actor.entity);
    }
    actor=Actor{};
}
void clear() {
    end_review();
    if (pending.active) { release_pending(); }
    if (diagnostic_index>=0) {
        if (diagnostic_hash) hook.invoke(0xE532F5D78798DAABULL,diagnostic_hash);
        diagnostic_hash=0;diagnostic_index=-1;record("import_diagnostics_cancelled");
    }
    if (reference_probe_active) {
        hook.invoke(0xE532F5D78798DAABULL,reference_probe_hash); reference_probe_active=false;
    }
    for (auto& actor:actors) {actor.cleanup_failed=false;remove_actor(actor);}
    std::snprintf(notice,sizeof(notice),"Clearing creatures. Your helicopter is kept.");
    record("clear_creatures");
}
bool prepare_helicopter_spawn() {
    if(!exists(owned_helicopter)) {owned_helicopter=0;return true;}
    // A stale/reused handle must never delete an unrelated entity.
    if(hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,owned_helicopter)!=hash("buzzard")) {
        record("helicopter_handle_not_owned_model",owned_helicopter);owned_helicopter=0;return true;
    }
    if(hook.invoke<int>(0x4C241E39B23DF959ULL,owned_helicopter,false)) {
        std::snprintf(notice,sizeof(notice),"Your usable helicopter already exists nearby.");return false;
    }
    const int wreck=owned_helicopter;
    hook.invoke(0xAD738C3085FE7E11ULL,wreck,true,true);
    hook.invoke(0xEA386986E786A54FULL,&owned_helicopter);
    if(exists(wreck)) {
        owned_helicopter=wreck;
        std::snprintf(notice,sizeof(notice),"Could not clear the owned helicopter wreck. See the log.");
        record("helicopter_wreck_cleanup_failed",wreck);return false;
    }
    owned_helicopter=0;record("helicopter_wreck_cleared",wreck);return true;
}

void begin_spawn(bool vehicle,std::uint32_t now) {
    if (pending.active || diagnostic_index>=0) return;
    if(!vehicle && !ergt::find_motion(ergt::creatures[selected].model,ergt::creatures[selected].attack_clip)) {
        std::snprintf(notice,sizeof(notice),"This boss requires the locally generated motion build. See the setup guide.");
        record("owned_motion_missing");return;
    }
    if (!vehicle && failed_creatures[selected]) {
        std::snprintf(notice,sizeof(notice),"This creature failed. Retry is locked for this session; its error is in the log.");
        return;
    }
    if (vehicle && !prepare_helicopter_spawn()) return;
    if (!vehicle && std::all_of(actors.begin(),actors.end(),[](const Actor& a){return a.entity!=0;})) {
        std::snprintf(notice,sizeof(notice),"One boss is active. Press 3 to clear it before spawning another."); return;
    }
    const auto& spec=ergt::creatures[selected];
    const auto model_hash=hash(vehicle?"buzzard":spec.model);
    if (!hook.invoke<int>(0xC0296A2EDF545E92ULL,model_hash) || !hook.invoke<int>(0x35B9E0803292B641ULL,model_hash)) {
        std::snprintf(notice,sizeof(notice),"Model %s unavailable. Check the ERGT DLC installation.",vehicle?"buzzard":spec.model);
        record("model_unavailable",0,static_cast<float>(selected)); return;
    }
    const auto child_hash=(!vehicle && spec.visual_child)?hash(spec.visual_child):0u;
    if(child_hash && (!hook.invoke<int>(0xC0296A2EDF545E92ULL,child_hash)||!hook.invoke<int>(0x35B9E0803292B641ULL,child_hash))){
        std::snprintf(notice,sizeof(notice),"Boss visual part is unavailable. Check the full DLC install.");record("visual_child_model_unavailable");return;
    }
    pending={true,vehicle,selected,model_hash,now};pending.child_hash=child_hash;
    if(child_hash)hook.invoke(0x963D27A58DF860ACULL,child_hash);
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
        release_pending();
        std::snprintf(notice,sizeof(notice),"Asset streaming timed out. See EldenLosSantos.log."); record("streaming_timeout"); return;
    }
    if (!hook.invoke<int>(0x98A4EB5D89A0C952ULL,pending.hash) || (pending.child_hash && !hook.invoke<int>(0x98A4EB5D89A0C952ULL,pending.child_hash))) return;
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
    auto p=hook.invoke<ergt::NativeVector>(0x1899F328B0E12848ULL,player,pending.vehicle?12.0f:0.0f,pending.vehicle?18.0f:std::max(18.0f,spec.body_radius*5.0f),0.0f);
    if (!finite({p.x,p.y,p.z})) {
        record("invalid_spawn_position");
        release_pending();
        std::snprintf(notice,sizeof(notice),"Invalid spawn position. Move outdoors and retry."); return;
    }
    float ground=0;
    if (!hook.invoke<int>(0xC906A7DAB05C8D2BULL,p.x,p.y,p.z+100.0f,&ground,false,false) || !std::isfinite(ground)) {
        release_pending();
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
                slot->last_impact=now-1000;
                if(pending.child_hash){
                    slot->visual_child=hook.invoke<int>(0x9A294B2138ABB884ULL,pending.child_hash,p.x,p.y,z,false,true,false,0);
                    if(!exists(slot->visual_child)){
                        failed_creatures[pending.preset]=true;remove_actor(*slot);release_pending();record("visual_child_create_failed");
                        std::snprintf(notice,sizeof(notice),"Boss visual part failed; incomplete spawn removed.");return;
                    }
                    const int child=slot->visual_child;
                    hook.invoke(0xAD738C3085FE7E11ULL,child,true,true);hook.invoke(0x5927F96A78577363ULL,child,250);
                    hook.invoke(0x1A9205C1B9EE827FULL,child,false,false);hook.invoke(0x1760FFA8AB074D66ULL,child,false);
                    hook.invoke(0x1718DE8E3F2823CAULL,child,false);hook.invoke(0x406137F8EF90EAF5ULL,child,true);
                    hook.invoke(0x6B9BBD38AB0796DFULL,child,entity,-1,0.f,0.f,0.f,0.f,0.f,0.f,false,false,false,false,2,true,0);
                    record("visual_child_created",child);
                }
                hook.invoke(0x5927F96A78577363ULL,entity,250);
                hook.invoke(0x406137F8EF90EAF5ULL,entity,true);
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
    release_pending();
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
        diagnostic_index=-1;record("import_diagnostics_complete",0,static_cast<float>(diagnostic_failures));
        std::snprintf(notice,sizeof(notice),diagnostic_failures?"Import check failed. Results saved in EldenLosSantos.log.":"Object creation checks passed. Press 2 to spawn a creature.");return;
    }
    diagnostic_hash=hash(diagnostic_models[diagnostic_index]);diagnostic_started=now;
    hook.invoke(0x963D27A58DF860ACULL,diagnostic_hash);
    std::snprintf(notice,sizeof(notice),"Checking import %d/%zu...",diagnostic_index+1,diagnostic_models.size());
}
void begin_diagnostics(std::uint32_t now) {
    if (diagnostic_index>=0 || pending.active || reference_probe_active || fighting) return;
    if (std::any_of(actors.begin(),actors.end(),[](const Actor& a){return a.entity!=0;})) return;
    diagnostic_index=-1;diagnostic_hash=0;diagnostic_failures=0;record("import_diagnostics_begin");diagnostic_next(now);
}
void tick_diagnostics(int player,std::uint32_t now) {
    if (diagnostic_index<0) return;
    const char* name=diagnostic_models[diagnostic_index];
    if (!hook.invoke<int>(0x98A4EB5D89A0C952ULL,diagnostic_hash)) {
        if (now-diagnostic_started<5000) return;
        if (log_file) {std::fprintf(log_file,"event=import_check model=%s result=stream_timeout\n",name);std::fflush(log_file);}
        diagnostic_failures++;
        diagnostic_next(now);return;
    }
    const auto p=coords(player);
    if (finite(p)) for (const bool dynamic:{false,true}) {
        int entity=hook.invoke<int>(0x9A294B2138ABB884ULL,diagnostic_hash,p.x,p.y,p.z-5.0f,false,true,dynamic,0);
        const bool valid=exists(entity);
        if (!dynamic && !valid) diagnostic_failures++;
        if (log_file) {
            std::fprintf(log_file,"event=import_check model=%s dynamic=%d entity=%d exists=%d\n",name,dynamic,entity,valid);
            std::fflush(log_file);
        }
        // No animation, combat or persistent actor: remove it within this tick.
        if (valid) hook.invoke(0x539E0AE3E6634B9FULL,&entity);
    }
    diagnostic_next(now);
}
void sync_visual_child(Actor& actor) {
    if(!actor.visual_child||!actor.spec||!actor.active_clip||actor.cleanup_requested)return;
    if(!exists(actor.entity)||!exists(actor.visual_child)||hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.visual_child)!=hash(actor.spec->visual_child)){
        actor.cleanup_requested=true;record("visual_child_lost",actor.entity);return;
    }
    const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
    if(std::isfinite(phase)&&phase>=0&&phase<=1){
        hook.invoke(0x4487C259F0F70977ULL,actor.visual_child,actor.spec->dictionary,actor.active_clip,phase);
        hook.invoke(0x40FDEDB72F8293B2ULL,actor.visual_child);
    }
}
// Fixed native-projectile diagnostic. It exercises actual engine collision
// and damage from an elevated firing point; it is not a manual flight test.
void tick_review_weapon(int player,std::uint32_t now) {
    if(!review_weapon_hash)return;
    auto& actor=actors[0];
    const bool valid=actor.entity==review_weapon_target && actor.spec && exists(actor.entity) && !actor.cleanup_requested &&
        hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.entity)==hash(actor.spec->model);
    if(!valid || static_cast<std::int32_t>(review_weapon_deadline-now)<=0){
        hook.invoke(0xAA08EF13F341C8FCULL,review_weapon_hash);review_weapon_hash=0;return;
    }
    if(!hook.invoke<int>(0x36E353271F0E90EEULL,review_weapon_hash))return;
    const auto base=coords(actor.entity);const float height=actor.spec->body_height*.8f;
    const float heading=hook.invoke<float>(0xE83D4F9BA2A38914ULL,actor.entity);
    const auto from=ergt::add(base,ergt::rotate_heading({0,-std::max(15.f,actor.spec->body_radius*5.f),height},heading));
    const auto to=ergt::add(base,{0,0,height});
    if(finite(from)&&finite(to)){
        const int damage=review_weapon_hash==hash("WEAPON_RPG")?300:30;
        hook.invoke(0x867654CBC7606F2CULL,from.x,from.y,from.z,to.x,to.y,to.z,damage,true,review_weapon_hash,player,true,false,-1.f);
        if(log_file){std::fprintf(log_file,"event=technical_native_projectile entity=%d weapon=%08x target_height=%.3f damage_argument=%d\n",actor.entity,review_weapon_hash,height,damage);std::fflush(log_file);}
    }
    hook.invoke(0xAA08EF13F341C8FCULL,review_weapon_hash);review_weapon_hash=0;
}
// Owner-authorized technical view only: local fixed commands, no listener,
// no arbitrary scripts or persistent gameplay changes. Expires after 45s and
// immediately yields back on normal mod controls/network/actor removal.
void tick_review(std::uint32_t now) {
    if(!review_until)return;
    if(static_cast<std::int32_t>(review_until-now)<=0){end_review();return;}
    auto& actor=actors[0];
    if(!exists(actor.entity)||!actor.spec){if(!pending.active)end_review();return;}
    if(hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.entity)!=hash(actor.spec->model)){end_review();return;}
    const auto origin=coords(actor.entity);const float h=actor.spec->body_height;
    const float heading=hook.invoke<float>(0xE83D4F9BA2A38914ULL,actor.entity);
    const float distance=review_view==2?h*.7f:h*1.35f;
    const auto offset=ergt::rotate_heading(review_view==1?ergt::Vec3{distance,0,h*.58f}:ergt::Vec3{0,-distance,h*(review_view==2?.82f:.58f)},heading);
    const auto camera=ergt::add(origin,offset);const auto target=ergt::add(origin,{0,0,h*(review_view==2?.8f:.5f)});
    if(!finite(camera)||!finite(target)){end_review();return;}
    if(!review_camera){
        review_camera=hook.invoke<int>(0xB51194800B257161ULL,"DEFAULT_SCRIPTED_CAMERA",camera.x,camera.y,camera.z,0.f,0.f,0.f,45.f,true,2);
        if(!review_camera){end_review();return;}
        hook.invoke(0x07E5B515DB0636FCULL,true,false,0,true,false,0);
        record("technical_review_camera_started",actor.entity,static_cast<float>(review_view));
    }
    hook.invoke(0x4D41783FB745E42EULL,review_camera,camera.x,camera.y,camera.z);
    hook.invoke(0xF75497BB865F0803ULL,review_camera,target.x,target.y,target.z);
}
#include "encounter_review.hpp"

void read_diagnostic_request(std::uint32_t now) {
    if (now-last_request_check<500 || !diagnostic_request_path[0]) return;
    last_request_check=now;
    FILE* request=_wfopen(diagnostic_request_path,L"rb");
    if (!request) return;
    char token[32]{};std::fgets(token,sizeof(token),request);std::fclose(request);
    const std::array<const char*,11> encounter_tokens={"REVIEW_RETURN\n","REVIEW_AIRFIELD\n","REVIEW_METRICS\n","REVIEW_CAR\n","REVIEW_PARK\n","REVIEW_HELI\n","REVIEW_HELI_GUN\n","REVIEW_HELI_ROCKET\n","REVIEW_PLAYER_BACK\n","REVIEW_FOOT_GUN\n","REVIEW_FOOT_RPG\n"};
    for(const char* allowed:encounter_tokens)if(std::strcmp(token,allowed)==0&&_wremove(diagnostic_request_path)==0){encounter_review_command(token,now);return;}
    // A file-only, fixed-command technical test; no listener or arbitrary code.
    if (std::strcmp(token,"CHECK_IMPORTS_ONCE\n")==0 && _wremove(diagnostic_request_path)==0)
        begin_diagnostics(now);
    else if(std::strcmp(token,"REVIEW_FIGHT\n")==0 && _wremove(diagnostic_request_path)==0){
        end_review();fighting=true;review_view=0;review_until=now+45000;record("technical_combat_review_enabled");
    }
    else if((std::strcmp(token,"REVIEW_HEADSHOT\n")==0 || std::strcmp(token,"REVIEW_ROCKET\n")==0) && _wremove(diagnostic_request_path)==0){
        if(!review_weapon_hash && actors[0].entity && exists(actors[0].entity)){
            review_weapon_hash=hash(token[7]=='H'?"WEAPON_CARBINERIFLE":"WEAPON_RPG");review_weapon_target=actors[0].entity;review_weapon_deadline=now+5000;
            hook.invoke(0x5443438F033E29C3ULL,review_weapon_hash,31,0);
        }
    }
    else if(std::strcmp(token,"REVIEW_STOP\n")==0 && _wremove(diagnostic_request_path)==0)end_review();
    else if(std::strcmp(token,"REVIEW_CLEAR\n")==0 && _wremove(diagnostic_request_path)==0)clear();
    else if((std::strcmp(token,"REVIEW_FRONT\n")==0 || std::strcmp(token,"REVIEW_SIDE\n")==0 || std::strcmp(token,"REVIEW_DETAIL\n")==0) && _wremove(diagnostic_request_path)==0){
        end_review();fighting=false;review_view=token[7]=='S'?1:token[7]=='D'?2:0;review_until=now+45000;
    }
    else if(std::strncmp(token,"REVIEW_SPAWN_",13)==0 && token[13]>='0' && token[13]<'0'+static_cast<int>(ergt::creatures.size()) && token[14]=='\n' && token[15]==0 && _wremove(diagnostic_request_path)==0){
        end_review();selected=token[13]-'0';fighting=false;begin_spawn(false,now);review_view=0;review_until=now+45000;
    }
}

void observe_damage(Actor& actor,int player,std::uint32_t now) {
    const int health=hook.invoke<int>(0xEEF059FAD016D209ULL,actor.entity);
    float loss=static_cast<float>(std::max(0,actor.native_health-health));
    const bool weapon=hook.invoke<int>(0x131D401334815E94ULL,actor.entity,0u,2)!=0;
    const bool vehicle=hook.invoke<int>(0xDFD5033FDBA0A9C8ULL,actor.entity)!=0;
    const bool player_hit=hook.invoke<int>(0xC86D67D52A707CF8ULL,actor.entity,player,true)!=0;
    if(player_hit) actor.last_attacked=now;
    // Small native collision/settling losses must not bleed an idle boss dry.
    if(!weapon && !vehicle && loss<80) loss=0;
    if(vehicle && now-actor.last_impact>=650) {
        float impact=0;
        for(int i=0;i<nearby_vehicle_count;i++) {
            const auto& v=nearby_vehicles[i];
            if(exists(v.entity) && hook.invoke<int>(0xC86D67D52A707CF8ULL,actor.entity,v.entity,true))
                impact=std::max(impact,ergt::impact_damage(std::max(v.speed,v.prior_speed)));
        }
        if(impact>0) { loss=std::max(loss,impact);actor.last_impact=now;record("vehicle_impact",actor.entity,impact); }
        else if(!weapon) loss=0; // A stationary/unattributed vehicle contact is not an impact.
    } else if(vehicle && !weapon) loss=0;
    if(loss<=0 && weapon && now-actor.last_fallback>=80) {
        // Fallback is explicitly player-attributed; NPC hits use actual HP loss.
        if(player_hit) {
            auto weapon_hash=hook.invoke<std::uint32_t>(0x0A6DB4965674D243ULL,player);
            std::uint32_t vehicle_weapon=0;
            if(hook.invoke<int>(0x1017582BCD3832DCULL,player,&vehicle_weapon) && vehicle_weapon) weapon_hash=vehicle_weapon;
            loss=hook.invoke<float>(0x3133B907D8B32053ULL,weapon_hash,0u);
            if(!std::isfinite(loss) || loss<=0) loss=32;
            record("player_weapon_hit_fallback",actor.entity,loss);
        }
        actor.last_fallback=now;
    }
    if(std::isfinite(loss) && loss>0) {
        const float applied=std::min(loss,1600.0f);
        actor.combat.damage(applied);actor.damage_since_log+=applied;
        if(now-actor.last_log>=200) {record("damage_applied",actor.entity,actor.damage_since_log);actor.damage_since_log=0;actor.last_log=now;}
    }
    hook.invoke(0xAC678E40BE7C74D2ULL,actor.entity);
    hook.invoke(0xA72CD9CA74A5ECBAULL,actor.entity);
    if(actor.native_health>0 && actor.combat.state()!=ergt::CombatState::defeated)
        hook.invoke(0x6B76DC1F3AE6E6A3ULL,actor.entity,actor.native_health,0,0u);
}
int choose_target(Actor& actor,int player,std::uint32_t now) {
    auto valid=[](int e){return exists(e) && !hook.invoke<int>(0x3317DEDB88C95038ULL,e,true);};
    if(now-actor.target_scan<500 && valid(actor.target)) return actor.target;
    actor.target_scan=now;
    const auto origin=coords(actor.entity);
    int best=0;float best_score=150;
    auto consider=[&](int e){
        if(!valid(e)) return;
        const auto p=coords(e);
        if(!finite(p)) return;
        const float distance=ergt::horizontal_distance(origin,p);
        if(distance>90 || std::abs(p.z-origin.z)>100) return;
        const float score=ergt::target_score(distance,e==actor.target,e==player && actor.last_attacked && now-actor.last_attacked<10000);
        if(score>=best_score || !hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,e,17)) return;
        best=e;best_score=score;
    };
    consider(player);
    for(int i=0;i<nearby_ped_count;i++) consider(nearby_peds[i]);
    if(best!=actor.target) {actor.combat.cancel_attack();actor.pose_transition_required=actor.combat.state()!=ergt::CombatState::staggered;actor.target=best;record("target_changed",actor.entity,static_cast<float>(best));}
    return best;
}
void move_with_collision(Actor& actor,ergt::Vec3 desired,std::uint32_t now,bool enabled) {
    using namespace ergt;
    if(!finite_vec(desired))enabled=false;
    const auto origin=coords(actor.entity);
    const bool had_cast=std::any_of(actor.sweep_handles.begin(),actor.sweep_handles.end(),[](int x){return x!=0;});
    bool pending_cast=false;
    for(auto& handle:actor.sweep_handles)if(handle){
        int hit=0,entity=0;NativeVector end{},normal{};
        const int result=hook.invoke<int>(0x3D87450E15D98694ULL,handle,&hit,&end,&normal,&entity);
        if(result==1)pending_cast=true;
        else {handle=0;if(result!=2||hit)actor.sweep_blocked=true;}
    }
    if(had_cast && !pending_cast){
        const bool current=sweep_still_current(actor.sweep_from,origin,now-actor.sweep_started,actor.sweep_animation==actor.animation_started);
        if(enabled && current && !actor.sweep_blocked)
            hook.invoke(0x239A3351AC1DA385ULL,actor.entity,actor.sweep_to.x,actor.sweep_to.y,actor.sweep_to.z,true,true,false);
        else actor.queued_movement={};
    }
    if(!enabled){actor.queued_movement={};return;}
    actor.queued_movement=add(actor.queued_movement,desired);
    // Bound frame stalls and asynchronous backlog; never teleport to catch up.
    const float distance=length(actor.queued_movement);
    if(distance>0.75f)actor.queued_movement=scale(actor.queued_movement,0.75f/distance);
    if(pending_cast || length(actor.queued_movement)<0.001f)return;
    const auto from=coords(actor.entity);
    Vec3 step=actor.queued_movement;const float size=length(step);
    if(size>0.35f)step=scale(step,0.35f/size);
    auto to=add(from,step);float ground=0;
    if(!hook.invoke<int>(0xC906A7DAB05C8D2BULL,to.x,to.y,from.z+3.0f,&ground,false,false)){actor.queued_movement={};return;}
    to.z=ground-actor.spec->minimum_z+0.05f;
    if(!finite_vec(to)||std::abs(to.z-from.z)>0.35f){actor.queued_movement={};return;}
    actor.queued_movement=subtract(actor.queued_movement,step);
    actor.sweep_from=from;actor.sweep_to=to;actor.sweep_started=now;actor.sweep_animation=actor.animation_started;actor.sweep_blocked=false;
    // Three overlapping swept spheres cover Malenia's upright body. These are
    // GTA-side conservative movement probes, not imported Havok limb colliders.
    for(int i=0;i<3;i++){
        const float radius=actor.spec->body_radius;
        const float low=radius+.05f,high=std::max(low,actor.spec->body_height-radius);
        const float z=low+(high-low)*i/2.0f;
        actor.sweep_handles[i]=hook.invoke<int>(0x28579D1B8F8AAC80ULL,from.x,from.y,from.z+z,to.x,to.y,to.z+z,radius,31,actor.entity,7);
        if(!actor.sweep_handles[i])actor.sweep_blocked=true;
    }
    if(std::all_of(actor.sweep_handles.begin(),actor.sweep_handles.end(),[](int x){return x==0;}))actor.queued_movement={};
}

void blade_contacts(Actor& actor,int primary,std::uint32_t now,bool enabled) {
    using namespace ergt;
    if(!actor.motion || !actor.motion->has_blade || !actor.melee_clip || !actor.active_clip)return;
    const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
    const auto origin=coords(actor.entity);const float previous=actor.blade_phase;const auto previous_origin=actor.blade_origin;
    actor.blade_phase=phase;actor.blade_origin=origin;
    if(!enabled || !actor.animation_accepted || !std::isfinite(phase) || previous<0 || phase<=previous || phase>1 ||
       (phase-previous)*actor.motion->duration>0.30f || length(subtract(origin,previous_origin))>1.0f ||
       !hook.invoke<int>(0x1F0B79228E461EC9ULL,actor.entity,actor.spec->dictionary,actor.active_clip,3))return;
    // Original owned TAE AttackBehavior intervals, sampled against the actual
    // native playback phase. Missing event data fails closed.
    if(!actor.motion->contacts || actor.motion->contact_count<=0)return;
    for(int window=0;window<actor.motion->contact_count;window++){
    const auto contact=actor.motion->contacts[window];
    const float first=std::max(previous,contact.start),last=std::min(phase,contact.end);
    if(last<first)continue;
    if(actor.blade_window!=window){
        actor.blade_window=window;actor.blade_victim_count=0;
        if(log_file && exists(primary)){
            const auto v=coords(primary);const auto pose=sample_motion(*actor.motion,first);
            std::fprintf(log_file,"event=source_contact_window entity=%d phase=%.5f heading=%.3f origin=%.3f,%.3f,%.3f target=%.3f,%.3f,%.3f blade_model=%.3f,%.3f,%.3f:%.3f,%.3f,%.3f\n",actor.entity,phase,actor.motion_heading,origin.x,origin.y,origin.z,v.x,v.y,v.z,pose.blade_base.x,pose.blade_base.y,pose.blade_base.z,pose.blade_tip.x,pose.blade_tip.y,pose.blade_tip.z);std::fflush(log_file);
        }
    }
    const float heading=hook.invoke<float>(0xE83D4F9BA2A38914ULL,actor.entity);
    if(!std::isfinite(heading))return;
    std::array<int,513> victims{};int count=0;victims[count++]=primary;
    for(int i=0;i<nearby_ped_count;i++)if(nearby_peds[i]!=primary)victims[count++]=nearby_peds[i];
    for(int i=0;i<count;i++){
        const int ped=victims[i];
        if(!exists(ped)||hook.invoke<int>(0x3317DEDB88C95038ULL,ped,true))continue;
        const auto victim=coords(ped);
        if(!finite_vec(victim)||length(subtract(victim,origin))>actor.spec->melee_range+actor.spec->body_height+4.0f)continue;
        const int car=hook.invoke<int>(0x9A9112A0FE9A4713ULL,ped,false);
        const int id=exists(car)?car:ped;
        if(std::find(actor.blade_victims.begin(),actor.blade_victims.begin()+actor.blade_victim_count,id)!=actor.blade_victims.begin()+actor.blade_victim_count)continue;
        NativeVector minimum{},maximum{};
        if(id==car)hook.invoke(0x03E8D3D5F549087AULL,hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,car),&minimum,&maximum);
        bool hit=false;
        for(int sample=0;sample<=8&&!hit;sample++){
            const float t=first+(last-first)*sample/8;
            const auto pose=sample_motion(*actor.motion,t);
            const auto base=mix(previous_origin,origin,(t-previous)/(phase-previous));
            for(int weapon=0;weapon<(actor.motion->dual_blade?2:1)&&!hit;weapon++){
            const auto local_a=weapon?pose.second_base:pose.blade_base,local_b=weapon?pose.second_tip:pose.blade_tip;
            const float sample_heading=actor.motion_heading+pose.yaw*57.2957795f;
            const auto a=add(base,rotate_heading(local_a,sample_heading)),b=add(base,rotate_heading(local_b,sample_heading));
            if(id==car){
                const auto x=hook.invoke<NativeVector>(0x2274BC1C4885E333ULL,car,a.x,a.y,a.z);
                const auto y=hook.invoke<NativeVector>(0x2274BC1C4885E333ULL,car,b.x,b.y,b.z);
                const float radius=actor.spec->weapon_radius;
                hit=segment_box({x.x,x.y,x.z},{y.x,y.y,y.z},{minimum.x-radius,minimum.y-radius,minimum.z-radius},{maximum.x+radius,maximum.y+radius,maximum.z+radius});
            }else {const float radius=.3f+actor.spec->weapon_radius;hit=segment_distance_squared(a,b,add(victim,{0,0,-0.65f}),add(victim,{0,0,0.65f}))<=radius*radius;}
            }
        }
        if(!hit||!hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,ped,17))continue;
        if(actor.blade_victim_count>=static_cast<int>(actor.blade_victims.size()))return;
        actor.blade_victims[actor.blade_victim_count++]=id;
        if(id==car){
            const float hp=hook.invoke<float>(0xC45D23BAF168AAB8ULL,car);
            hook.invoke(0x45F6D8EEF34ABEF1ULL,car,hp-actor.spec->melee_damage*5.0f);
            const auto push=rotate_heading({0,-3.0f,1.2f},heading);
            hook.invoke(0x18FF00FC7EFF559EULL,car,1,push.x,push.y,push.z,false,false,true,false);
        }else hook.invoke(0x697157CED63F18D4ULL,ped,actor.spec->melee_damage,true,0,0u);
        if(log_file){std::fprintf(log_file,"event=blade_contact entity=%d victim=%d phase=%.5f tick=%u\n",actor.entity,id,phase,now);std::fflush(log_file);}
    }
    }
}

bool attack_playback_ready(const Actor& actor,const char* kind,ergt::Vec3 origin,ergt::Vec3 target,std::uint32_t now) {
    const bool requested=actor.animation_accepted && actor.active_clip &&
        std::strcmp(actor.active_clip,actor.spec->attack_clip)==0;
    const float phase=requested?hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip):0.0f;
    const int playing=requested?hook.invoke<int>(0x1F0B79228E461EC9ULL,actor.entity,actor.spec->dictionary,actor.active_clip,3):0;
    if(log_file) {
        std::fprintf(log_file,"event=attack_contact entity=%d kind=%s requested=%d playing=%d phase=%.5f elapsed_ms=%u actor_xyz=%.3f,%.3f,%.3f target_xyz=%.3f,%.3f,%.3f\n",
            actor.entity,kind,requested,playing,phase,now-actor.animation_started,origin.x,origin.y,origin.z,target.x,target.y,target.z);
        std::fflush(log_file);
    }
    // A definite rejected animation cannot produce an invisible strike. Phase
    // telemetry is evidence for the owner test, not assumed object-task proof.
    if(!requested) record("attack_suppressed_animation_not_accepted",actor.entity);
    return requested;
}

void strike_nearby(Actor& actor,int primary,ergt::Vec3 origin,ergt::Vec3 target) {
    std::array<int,513> victims{};int count=0;
    victims[count++]=primary;
    for(int i=0;i<nearby_ped_count;i++) if(nearby_peds[i]!=primary) victims[count++]=nearby_peds[i];
    // A strike can visit every victim; retain every distinct vehicle handle.
    std::array<int,513> hit_cars{};int car_count=0;
    for(int i=0;i<count;i++) {
        const int ped=victims[i];
        if(!exists(ped) || hook.invoke<int>(0x3317DEDB88C95038ULL,ped,true)) continue;
        const auto p=coords(ped);const float range=ergt::horizontal_distance(origin,p);
        if(range>actor.spec->melee_range+0.5f || std::abs(p.z-origin.z)>4) continue;
        const float forward=(p.x-origin.x)*(target.x-origin.x)+(p.y-origin.y)*(target.y-origin.y);
        if(forward<0 || !hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,ped,17)) continue;
        const int car=hook.invoke<int>(0x9A9112A0FE9A4713ULL,ped,false);
        if(car && exists(car)) {
            if(std::find(hit_cars.begin(),hit_cars.begin()+car_count,car)!=hit_cars.begin()+car_count) continue;
            if(car_count<static_cast<int>(hit_cars.size())) hit_cars[car_count++]=car;
            const float hp=hook.invoke<float>(0xC45D23BAF168AAB8ULL,car);
            hook.invoke(0x45F6D8EEF34ABEF1ULL,car,hp-actor.spec->melee_damage*5.0f);
            const float length=std::max(1.0f,range);
            hook.invoke(0x18FF00FC7EFF559EULL,car,1,(p.x-origin.x)/length*3.0f,(p.y-origin.y)/length*3.0f,1.2f,false,false,true,false);
        } else hook.invoke(0x697157CED63F18D4ULL,ped,actor.spec->melee_damage,true,0,0u);
    }
    record("melee_strike",actor.entity);
}
void update_actor(Actor& actor,int player,int,std::uint32_t now,int dt) {
    if(!actor.entity) return;
    if(actor.cleanup_requested){if(!actor.cleanup_failed)remove_actor(actor);return;}
    if(!exists(actor.entity) || hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.entity)!=hash(actor.spec->model)) {
        record("actor_lost_not_a_confirmed_kill",actor.entity);remove_actor(actor);return;
    }
    const auto position=coords(actor.entity),owner=coords(player);
    if(!finite(position) || !finite(owner)) return;
    if(ergt::horizontal_distance(position,owner)>500) {remove_actor(actor);return;}
    if(actor.combat.state()!=ergt::CombatState::defeated) observe_damage(actor,player,now);
    const int target_entity=fighting && actor.combat.state()!=ergt::CombatState::defeated?choose_target(actor,player,now):0;
    const bool alive=exists(target_entity) && !hook.invoke<int>(0x3317DEDB88C95038ULL,target_entity,true);
    const auto target=alive?coords(target_entity):position;
    const bool sight=alive && hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,target_entity,17);
    const bool airborne=alive && hook.invoke<int>(0x298B91AE825E5705ULL,target_entity);
    const bool impact_recovery=now-actor.last_impact<700;
    auto decision=actor.combat.tick(dt,{position,target,alive,sight,fighting,airborne});
    const auto state=actor.combat.state();
    if(state!=actor.previous_state || actor.pose_transition_required || (state==ergt::CombatState::staggered && actor.played_reaction!=actor.combat.reaction_generation())) {
        actor.pose_transition_required=false;
        actor.played_reaction=actor.combat.reaction_generation();
        if(state==ergt::CombatState::melee_windup || state==ergt::CombatState::ranged_windup){
            actor.committed_heading=ergt::heading_to_target(position,target,actor.spec->model_heading_offset);
            hook.invoke(0x8E2530AA8ADA980EULL,actor.entity,actor.committed_heading);
        }
        if(state!=ergt::CombatState::recovering)actor.melee_clip=state==ergt::CombatState::melee_windup;
        const auto intent=ergt::animation_intent(state);
        if(intent==ergt::AnimationIntent::move) animate(actor,actor.spec->move_clip,true);
        else if(intent==ergt::AnimationIntent::attack) animate(actor,actor.spec->attack_clip,false);
        else if(intent==ergt::AnimationIntent::idle) animate(actor,actor.spec->idle_clip,true);
        else if(intent==ergt::AnimationIntent::stagger) animate(actor,actor.spec->stagger_clip?actor.spec->stagger_clip:actor.spec->idle_clip,actor.spec->stagger_clip==nullptr);
        else if(intent==ergt::AnimationIntent::death) {
            animate(actor,actor.spec->death_clip,false);
            std::snprintf(notice,sizeof(notice),"%s defeated. 3 clears creatures.",actor.spec->label);
            hud_until=now+6000;record("defeated",actor.entity);
        }
        actor.previous_state=state;
    }
    observe_animation(actor,now);
    const bool death_finished=!actor.animation_accepted || !actor.motion ||
        hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip)>=.98f ||
        now-actor.animation_started>static_cast<unsigned>(actor.motion->duration*1000)+1500;
    if(state==ergt::CombatState::defeated && death_finished && !actor.corpse_settled){
        // Let an airborne vehicle/explosion victim land before freezing the
        // final pose. Disabling collision in mid-air would remove ground contact.
        float ground=0;
        if(hook.invoke<int>(0xC906A7DAB05C8D2BULL,position.x,position.y,position.z+2.0f,&ground,false,false) &&
           std::abs(position.z-(ground-actor.spec->minimum_z+.05f))<.3f &&
           hook.invoke<float>(0xD5037BA82E12416FULL,actor.entity)<.5f){
            const float heading=hook.invoke<float>(0xE83D4F9BA2A38914ULL,actor.entity);
            hook.invoke(0x8524A8B0171D5E07ULL,actor.entity,0.0f,0.0f,heading,2,true);
            hook.invoke(0x239A3351AC1DA385ULL,actor.entity,position.x,position.y,ground-actor.spec->minimum_z+.05f,true,true,false);
            hook.invoke(0x428CA6DBD1094446ULL,actor.entity,true);
            hook.invoke(0x1A9205C1B9EE827FULL,actor.entity,false,false);
            actor.corpse_settled=true;record("corpse_settled",actor.entity);
        }
    }
    if(fighting && (state==ergt::CombatState::chasing || state==ergt::CombatState::idle) && alive && !impact_recovery) {
        const float heading=ergt::heading_to_target(position,target,actor.spec->model_heading_offset);
        hook.invoke(0x8E2530AA8ADA980EULL,actor.entity,heading);
        actor.motion_heading=heading;
    }
    if(actor.motion && !actor.corpse_settled && !impact_recovery){
        const float native_phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
        const float yaw=std::isfinite(native_phase)?ergt::sample_motion(*actor.motion,native_phase).yaw:0;
        const float heading=actor.motion_heading+yaw*57.2957795f;
        // Pose/root/blade math assumes an upright model; restore that exact
        // frame after physical impact recovery, preserving committed facing.
        if(std::isfinite(heading))hook.invoke(0x8524A8B0171D5E07ULL,actor.entity,0.0f,0.0f,heading,2,true);
    }
    if(actor.motion) {
        if(state==ergt::CombatState::chasing){
            const float speed=ergt::length(ergt::subtract(actor.motion->samples[actor.motion->count-1].root,actor.motion->samples[0].root))/actor.motion->duration;
            const float rate=speed>0.01f?std::clamp(actor.spec->speed*(actor.combat.enraged()?1.25f:1.0f)/speed,0.25f,2.0f):1.0f;
            if(std::abs(rate-actor.playback_rate)>0.001f){actor.playback_rate=rate;hook.invoke(0x28D1A16553C51776ULL,actor.entity,actor.spec->dictionary,actor.active_clip,rate);}
        }
        const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
        ergt::Vec3 root_delta{};
        const bool advancing=actor.motion_cursor.advance(*actor.motion,phase,actor.clip_loop,dt*0.001f*actor.playback_rate+0.08f,root_delta);
        const bool moving=state==ergt::CombatState::chasing || (actor.melee_clip && (state==ergt::CombatState::melee_windup || state==ergt::CombatState::recovering));
        const bool reacting=state==ergt::CombatState::staggered || state==ergt::CombatState::defeated;
        const bool enabled=(reacting || (moving && fighting && alive)) && !impact_recovery && !actor.corpse_settled && actor.animation_accepted;
        if(!advancing || !hook.invoke<int>(0x1F0B79228E461EC9ULL,actor.entity,actor.spec->dictionary,actor.active_clip,3))root_delta={};
        move_with_collision(actor,ergt::rotate_heading(root_delta,actor.motion_heading),now,enabled);
        blade_contacts(actor,target_entity,now,enabled && !reacting && sight);
    } else if(!impact_recovery && (decision.movement.x!=0 || decision.movement.y!=0)) {
        const float x=position.x+decision.movement.x,y=position.y+decision.movement.y;
        float ground=0;
        if(hook.invoke<int>(0xC906A7DAB05C8D2BULL,x,y,position.z+4.0f,&ground,false,false)) {
            const float z=ground-actor.spec->minimum_z+0.05f;
            if(std::abs(z-position.z)<1.5f) hook.invoke(0x239A3351AC1DA385ULL,actor.entity,x,y,z,true,true,false);
        }
    }
    if(decision.telegraph && target_entity==player) marker(decision.aim);
    if(decision.melee_strike && !actor.motion && !impact_recovery && attack_playback_ready(actor,"melee",position,target,now)) strike_nearby(actor,target_entity,position,target);
    if(decision.ranged_strike && !impact_recovery && attack_playback_ready(actor,"ranged_area",position,decision.aim,now)) {
        const auto p=decision.aim;
        hook.invoke(0xE3AD2BDBAEE269ACULL,p.x,p.y,p.z,0,0.35f,true,false,0.15f,false);
        record("ranged_strike",actor.entity);
    }
    const float ratio=actor.combat.ratio();
    actor.trail_health=std::max(ratio,actor.trail_health-dt*0.00015f);
}
void rect(float x,float y,float w,float h,int r,int g,int b,int a) {
    hook.invoke(0x3A618A217E5154F0ULL,x,y,w,h,r,g,b,a,false);
}
void boss_hud() {
    int count=0;for(const auto& actor:actors) if(actor.entity) count++;
    int row=0;
    for(const auto& actor:actors) if(actor.entity) {
        const float y=0.90f-(count-1-row)*0.062f;
        const float left=0.22f,width=0.56f;
        rect(0.5f,y+0.014f,width+0.018f,0.048f,8,7,6,155);
        text(left,y-0.012f,actor.spec->label,0.34f);
        rect(0.5f,y+0.028f,width+0.003f,0.014f,139,115,73,230);
        rect(0.5f,y+0.028f,width,0.010f,30,19,18,245);
        float trail=width*actor.trail_health,fill=width*actor.combat.ratio();
        if(trail>0) rect(left+trail/2,y+0.028f,trail,0.009f,178,135,78,240);
        if(fill>0) rect(left+fill/2,y+0.028f,fill,0.009f,126,25,29,255);
        if(actor.combat.state()==ergt::CombatState::defeated) text(0.68f,y-0.009f,"DEFEATED",0.25f);
        else if(actor.combat.enraged()) text(0.69f,y-0.009f,"ENRAGED",0.25f);
        row++;
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
    commands.fetch_or(flag);
}
void run() {
    initialize_log();
    std::uint32_t last=hook.invoke<std::uint32_t>(0x9CD27B0045628463ULL);
    hud_until=last+10000;
    for (;;) {
        const auto now=hook.invoke<std::uint32_t>(0x9CD27B0045628463ULL);
        const int dt=static_cast<int>(std::min<std::uint32_t>(250,now-last)); last=now;
        if (hook.invoke<int>(0x9DE624D2FC4B603FULL) || hook.invoke<int>(0xB0034A223497FFCBULL) ||
            hook.invoke<int>(0x991251AFC3981F84ULL)) {
            end_review(); commands.store(0); hook.wait(0); continue;
        }
        const int player=hook.invoke<int>(0xD80958FC74E988A6ULL);
        if (!exists(player)) { end_review(); commands.store(0); hook.wait(0); continue; }
        // Reserve top-row 1-6 for the mod without also selecting GTA weapons.
        // The regular weapon wheel and controller bindings remain available.
        for (const int control:{157,158,160,164,165,159}) hook.invoke(0xFE99B66D079CF6BCULL,0,control,true);
        const unsigned command=commands.exchange(0);
        if(command) {qa.fire_until=0;end_review();hud_until=now+6000;}
        scan_world(player,now);
        if (command&select_next) selected=(selected+1)%static_cast<int>(ergt::creatures.size());
        read_diagnostic_request(now);
        if (command&clear_all) clear();
        else if (command&spawn) begin_spawn(false,now);
        if (command&toggle_combat) {
            fighting=!fighting;
            std::snprintf(notice,sizeof(notice),fighting?"Creatures are aggressive.":"Combat paused. 4 resumes.");
            record(fighting?"combat_on":"combat_off");
        }
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
        if(now<hud_until || pending.active) {
            char title[160];
            std::snprintf(title,sizeof(title),"ELDEN LOS SANTOS   |   %s   |   %s",ergt::creatures[selected].label,fighting?"AGGRESSIVE":"COMBAT PAUSED");
            text(0.025f,0.025f,title,0.32f);text(0.025f,0.055f,notice,0.28f);
            text(0.025f,0.08f,controls,0.25f);
        }
        for(auto& actor:actors)sync_visual_child(actor);
        tick_encounter_review(player,now);
        tick_review_weapon(player,now);
        tick_review(now);
        boss_hud();
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
