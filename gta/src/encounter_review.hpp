// SPDX-License-Identifier: Apache-2.0
// Fixed, local Story Mode technical checks. Never included in normal inputs.
// Uses real native vehicles/weapons and collision; no synthetic boss damage.
struct EncounterReview {
    bool active=false;
    ergt::Vec3 return_position{};
    float return_heading=0;
    int return_wanted=0,vehicle=0,vehicle_kind=0,fire_mode=0;
    std::uint32_t vehicle_model=0,load_until=0,until=0,fire_until=0,last_sample=0;
    std::uint32_t selected_weapon=0,creep_until=0;
    std::array<float,4096> frame_ms{};
    int frames=0;
    std::uint32_t metrics_until=0;
} qa;

bool review_vehicle_owned() {
    return exists(qa.vehicle)&&hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,qa.vehicle)==qa.vehicle_model;
}
void review_delete_vehicle(int player) {
    if(review_vehicle_owned()) {
        if(hook.invoke<int>(0x9A9112A0FE9A4713ULL,player,false)==qa.vehicle) {
            hook.invoke(0xAAA34F8A7CB32098ULL,player);
            auto p=qa.return_position;
            if(exists(actors[0].entity)&&actors[0].spec){p=ergt::add(coords(actors[0].entity),{std::max(35.f,actors[0].spec->body_radius*7.f),0,1.f});}
            hook.invoke(0x239A3351AC1DA385ULL,player,p.x,p.y,p.z,false,false,true);
        }
        hook.invoke(0xEA386986E786A54FULL,&qa.vehicle);
        if(exists(qa.vehicle)){record("review_vehicle_cleanup_failed",qa.vehicle);return;}
    }
    qa.vehicle=0;
    if(qa.vehicle_model)hook.invoke(0xE532F5D78798DAABULL,qa.vehicle_model);
    qa.vehicle_model=0;qa.load_until=0;qa.fire_until=0;qa.creep_until=0;
}
void end_encounter_review(int player) {
    end_review();qa.fire_until=0;qa.metrics_until=0;
    review_delete_vehicle(player);
    if(qa.vehicle)return; // Preserve ownership so an explicit retry can clean up.
    if(qa.active&&exists(player)) {
        const auto p=qa.return_position;
        hook.invoke(0x239A3351AC1DA385ULL,player,p.x,p.y,p.z,false,false,true);
        hook.invoke(0x8E2530AA8ADA980EULL,player,qa.return_heading);
        const int id=hook.invoke<int>(0x4F8644AF03D0E0D6ULL);
        hook.invoke(0x39FF19C64EF7DA5BULL,id,qa.return_wanted,false);
        hook.invoke(0xE0A7D1E497FFCD6FULL,id,false);
        hook.invoke(0xD972DF67326F966EULL);
    }
    qa={};record("encounter_review_ended");
}
bool encounter_review_command(const char* token,std::uint32_t now) {
    const int player=hook.invoke<int>(0xD80958FC74E988A6ULL);
    if(std::strcmp(token,"REVIEW_RETURN\n")==0){clear();end_encounter_review(player);return true;}
    if(std::strcmp(token,"REVIEW_AIRFIELD\n")==0) {
        if(qa.active||hook.invoke<int>(0x9A9112A0FE9A4713ULL,player,false)){record("review_setup_refused");return true;}
        clear();qa.active=true;qa.return_position=coords(player);
        qa.return_heading=hook.invoke<float>(0xE83D4F9BA2A38914ULL,player);
        qa.return_wanted=hook.invoke<int>(0xE28E54788CE8F12DULL,hook.invoke<int>(0x4F8644AF03D0E0D6ULL));
        qa.until=now+600000;fighting=false;
        // Sandy Shores runway; source ground query is required before spawning.
        hook.invoke(0x07503F7948F491A7ULL,1740.f,3260.f,42.f);
        hook.invoke(0x239A3351AC1DA385ULL,player,1740.f,3260.f,42.f,false,false,true);
        hook.invoke(0x8E2530AA8ADA980EULL,player,90.f);
        hook.invoke(0xE679E3E06E363892ULL,12,0,0);
        record("encounter_review_airfield",player);return true;
    }
    if(!qa.active)return false;
    qa.until=now+600000;
    if(std::strcmp(token,"REVIEW_METRICS\n")==0){qa.frames=0;qa.metrics_until=now+30000;record("review_metrics_begin");return true;}
    auto& actor=actors[0];
    const bool actor_ok=exists(actor.entity)&&actor.spec&&!actor.cleanup_requested&&hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.entity)==hash(actor.spec->model);
    if(std::strcmp(token,"REVIEW_CAR\n")==0||std::strcmp(token,"REVIEW_PARK\n")==0||std::strcmp(token,"REVIEW_HELI\n")==0) {
        if(!actor_ok){record("review_no_actor");return true;}
        review_delete_vehicle(player);if(qa.vehicle)return true;
        qa.vehicle_kind=token[7]=='H'?3:token[7]=='P'?2:1;
        qa.vehicle_model=hash(qa.vehicle_kind==3?"buzzard":"sultan");qa.load_until=now+5000;
        hook.invoke(0x963D27A58DF860ACULL,qa.vehicle_model);
        if(qa.vehicle_kind==3)end_review();
        record("review_vehicle_requested",0,static_cast<float>(qa.vehicle_kind));return true;
    }
    if(std::strcmp(token,"REVIEW_HELI_GUN\n")==0||std::strcmp(token,"REVIEW_HELI_ROCKET\n")==0) {
        if(!actor_ok||!review_vehicle_owned()||qa.vehicle_kind!=3||hook.invoke<int>(0xBB40DD2270B65366ULL,qa.vehicle,-1,false)!=player){record("review_heli_fire_refused");return true;}
        qa.selected_weapon=hash(token[12]=='G'?"VEHICLE_WEAPON_PLAYER_BUZZARD":"VEHICLE_WEAPON_SPACE_ROCKET");
        const bool accepted=hook.invoke<int>(0x75C55983C2C39DAAULL,player,qa.selected_weapon)!=0;
        if(accepted){qa.fire_until=now+3000;qa.fire_mode=1;}
        if(log_file){std::fprintf(log_file,"event=review_heli_weapon accepted=%d hash=%08x\n",accepted,qa.selected_weapon);std::fflush(log_file);}return true;
    }
    if(std::strcmp(token,"REVIEW_FOOT_GUN\n")==0||std::strcmp(token,"REVIEW_FOOT_RPG\n")==0) {
        if(!actor_ok||hook.invoke<int>(0x9A9112A0FE9A4713ULL,player,false)){record("review_foot_fire_refused");return true;}
        qa.selected_weapon=hash(token[12]=='G'?"WEAPON_CARBINERIFLE":"WEAPON_RPG");
        hook.invoke(0xBF0FD6E56C964FCBULL,player,qa.selected_weapon,100,false,true);
        hook.invoke(0xADF692B254977C0CULL,player,qa.selected_weapon,true);
        qa.fire_until=now+3000;qa.fire_mode=2;record("review_foot_fire_started",player);return true;
    }
    if(std::strcmp(token,"REVIEW_CREEP\n")==0) {
        if(review_vehicle_owned() && qa.vehicle_kind==2){qa.creep_until=now+5000;record("review_creep_started",qa.vehicle);}
        return true;
    }
    if(std::strcmp(token,"REVIEW_PLAYER_BACK\n")==0) {
        review_delete_vehicle(player);const auto p=coords(actor.entity);
        if(actor_ok){hook.invoke(0x239A3351AC1DA385ULL,player,p.x+35.f,p.y,p.z+1.f,false,false,true);record("review_player_repositioned",player);}return true;
    }
    return false;
}
void tick_encounter_review(int player,std::uint32_t now) {
    if(!qa.active)return;
    if(static_cast<std::int32_t>(qa.until-now)<=0||hook.invoke<int>(0x3317DEDB88C95038ULL,player,true)) {clear();end_encounter_review(player);return;}
    hook.invoke(0xB302540597885499ULL,hook.invoke<int>(0x4F8644AF03D0E0D6ULL));
    auto& actor=actors[0];const bool actor_ok=exists(actor.entity)&&actor.spec&&!actor.cleanup_requested&&hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,actor.entity)==hash(actor.spec->model);
    if(qa.load_until) {
        if(!actor_ok||static_cast<std::int32_t>(qa.load_until-now)<=0){review_delete_vehicle(player);record("review_vehicle_load_failed");}
        else if(hook.invoke<int>(0x98A4EB5D89A0C952ULL,qa.vehicle_model)) {
            const auto b=coords(actor.entity);const bool heli=qa.vehicle_kind==3;
            const float distance=heli?std::max(50.f,actor.spec->body_radius*6.f):qa.vehicle_kind==2?2.2f+actor.spec->body_radius:25.f+actor.spec->body_radius;
            const auto p=ergt::add(b,{distance,0,heli?actor.spec->body_height*.55f:0.f});float ground=0;
            if(!hook.invoke<int>(0xC906A7DAB05C8D2BULL,p.x,p.y,p.z+100.f,&ground,false,false))return;
            qa.vehicle=hook.invoke<int>(0xAF35D0D2583051B0ULL,qa.vehicle_model,p.x,p.y,heli?p.z:ground+1.f,90.f,false,true,false);qa.load_until=0;
            if(review_vehicle_owned()) {
                hook.invoke(0xAD738C3085FE7E11ULL,qa.vehicle,true,true);
                hook.invoke(0x2497C4717C8B881EULL,qa.vehicle,true,true,false);
                if(heli) {
                    hook.invoke(0xA178472EBB8AE60DULL,qa.vehicle);
                    hook.invoke(0xF75B0D629E1C063DULL,player,qa.vehicle,-1);
                    hook.invoke(0x1C99BB7B6E96D16FULL,qa.vehicle,0.f,0.f,0.f);
                } else {
                    // Keep the test driver out of the vehicle's impact lane.
                    hook.invoke(0x239A3351AC1DA385ULL,player,b.x+35.f,b.y+8.f,b.z+1.f,false,false,true);
                    hook.invoke<int>(0x49733E92263139D1ULL,qa.vehicle,5.f);
                    hook.invoke(0xE4E2FD323574965CULL,qa.vehicle,qa.vehicle_kind==2);
                    if(qa.vehicle_kind==1)hook.invoke(0xAB54A438726D25D5ULL,qa.vehicle,20.f);
                }
                record("review_vehicle_created",qa.vehicle,static_cast<float>(qa.vehicle_kind));
            } else record("review_vehicle_create_failed");
        }
    }
    if(qa.creep_until) {
        if(!review_vehicle_owned()||qa.vehicle_kind!=2)qa.creep_until=0;
        else if(static_cast<std::int32_t>(qa.creep_until-now)<=0){
            hook.invoke(0xAB54A438726D25D5ULL,qa.vehicle,0.f);hook.invoke(0xE4E2FD323574965CULL,qa.vehicle,true);qa.creep_until=0;record("review_creep_stopped",qa.vehicle);
        } else {
            hook.invoke(0xE4E2FD323574965CULL,qa.vehicle,false);hook.invoke(0xAB54A438726D25D5ULL,qa.vehicle,.65f);
        }
    }
    if(qa.fire_until) {
        if(!actor_ok||(qa.fire_mode==1&&!review_vehicle_owned())||static_cast<std::int32_t>(qa.fire_until-now)<=0||actor.combat.state()==ergt::CombatState::defeated)qa.fire_until=0;
        else {
            const auto p=coords(actor.entity);
            if(qa.fire_mode==1)hook.invoke(0x74CD9A9327A282EAULL,player,actor.entity,p.x,p.y,p.z+actor.spec->body_height*.55f);
            else hook.invoke(0x96A05E4FB321B1BAULL,player,p.x,p.y,p.z+actor.spec->body_height*.5f,true);
        }
    }
    if(qa.metrics_until) {
        const float ms=hook.invoke<float>(0x15C40837039FFAF7ULL)*1000.f;
        if(std::isfinite(ms)&&ms>0&&qa.frames<static_cast<int>(qa.frame_ms.size()))qa.frame_ms[qa.frames++]=ms;
        if(static_cast<std::int32_t>(qa.metrics_until-now)<=0) {
            if(qa.frames>0&&log_file){std::sort(qa.frame_ms.begin(),qa.frame_ms.begin()+qa.frames);double sum=0;for(int i=0;i<qa.frames;i++)sum+=qa.frame_ms[i];
                std::fprintf(log_file,"event=review_frame_times frames=%d mean_ms=%.3f p50_ms=%.3f p95_ms=%.3f p99_ms=%.3f\n",qa.frames,sum/qa.frames,qa.frame_ms[qa.frames/2],qa.frame_ms[qa.frames*95/100],qa.frame_ms[qa.frames*99/100]);std::fflush(log_file);}
            qa.metrics_until=0;
        }
    }
    if(now-qa.last_sample>=500) {
        qa.last_sample=now;
        if(log_file&&actor_ok){const auto p=coords(actor.entity);const auto v=review_vehicle_owned()?coords(qa.vehicle):ergt::Vec3{};
            std::fprintf(log_file,"event=encounter_review_sample actor=%d hp=%.2f state=%d xyz=%.3f,%.3f,%.3f vehicle=%d kind=%d speed=%.3f touching=%d vehicle_xyz=%.3f,%.3f,%.3f player_hp=%d\n",actor.entity,actor.combat.health(),static_cast<int>(actor.combat.state()),p.x,p.y,p.z,qa.vehicle,qa.vehicle_kind,review_vehicle_owned()?hook.invoke<float>(0xD5037BA82E12416FULL,qa.vehicle):0.f,review_vehicle_owned()?hook.invoke<int>(0x17FFC1B2BA35A494ULL,actor.entity,qa.vehicle):0,v.x,v.y,v.z,hook.invoke<int>(0xEEF059FAD016D209ULL,player));std::fflush(log_file);}
    }
}
