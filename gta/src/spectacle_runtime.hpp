// SPDX-License-Identifier: Apache-2.0
// Included by the ScriptHook entrypoint. All abilities remain local, bounded,
// animation-cued and owned by one encounter; no sockets or retail edits.
struct HeldTraffic { int entity=0; std::uint32_t model=0; };
struct Fireball {
    int entity=0,probe=0,boss=0;std::uint32_t model=0,born=0,cast_at=0;
    ergt::Vec3 position{},next{},velocity{};bool active=false;
};
struct Responder {
    int vehicle=0;std::array<int,3> peds{};
    std::uint32_t car_model=0,ped_model=0,requested=0,last_task=0;
    bool attempted=false,arrived=false;
};
struct Showcase {
    int boss=0;std::uint32_t began=0,animation=0,phase_banner=0,traffic_until=0;
    bool city=true,film=false,second_phase=false;
    std::array<HeldTraffic,5> traffic{};
    std::array<Fireball,6> fireballs{};
    std::array<Responder,3> responders{};
    std::uint32_t response_group=0,rock_model=0;
    ergt::PhaseCue cue;
    ergt::Vec3 aim{},wave_origin{};float wave_radius=0;
    bool wave=false;
    std::array<int,640> wave_victims{};int wave_count=0;
    int camera=0,view=0,camera_probe=0;std::uint32_t camera_until=0,camera_cast_at=0;
    ergt::Vec3 camera_desired{},camera_safe{};bool camera_ready=false;
    bool reset_pending=false;std::uint32_t reset_until=0;
    ergt::Vec3 spawn_origin{};float spawn_heading=0;int spawn_preset=0;
    bool spawn_saved=false;
} show;

bool matches(int entity,std::uint32_t model) {
    return exists(entity)&&hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,entity)==model;
}
bool contains_player(int vehicle) {
    if(!exists(vehicle))return false;
    const int seats=std::clamp(hook.invoke<int>(0xA7C4F2C6E744A550ULL,vehicle),0,16);
    for(int seat=-1;seat<seats;seat++) {
        if(hook.invoke<int>(0x22AC59A870E6A669ULL,vehicle,seat,false))continue;
        const int ped=hook.invoke<int>(0xBB40DD2270B65366ULL,vehicle,seat,false);
        if(exists(ped)&&hook.invoke<int>(0x12534C348C6CB68BULL,ped))return true;
    }
    return false;
}
void glow(ergt::Vec3 p,bool purple,float size) {
    if(!finite(p))return;
    hook.invoke(0xF2A1B2771A01DBD4ULL,p.x,p.y,p.z,purple?155:255,purple?65:100,purple?255:25,size*5.f,4.f);
}
void orb(ergt::Vec3 p,bool purple,float size) {
    hook.invoke(0x28477EC23D892089ULL,28,p.x,p.y,p.z,0.f,0.f,0.f,0.f,0.f,0.f,size,size,size,
        purple?170:255,purple?65:115,purple?255:35,175,false,false,2,false,
        static_cast<const char*>(nullptr),static_cast<const char*>(nullptr),false);
    glow(p,purple,size);
}
void end_film_camera() {
    if(show.camera) {
        hook.invoke(0x07E5B515DB0636FCULL,false,false,0,true,false,0);
        hook.invoke(0x865908C81A2C22E9ULL,show.camera,true);
    }
    show.camera=0;show.view=0;show.camera_until=0;show.camera_ready=false;
    // Any outstanding shape handle is drained by tick_film, never reused.
}
void release_traffic() {
    // Ambient cars are never owned, frozen, deleted, or stripped of gravity.
    // Ending control simply leaves them to native physics.
    for(auto& car:show.traffic)car={};
    show.traffic_until=0;
}
void retire_fireball(Fireball& ball) {
    ball.active=false;
    if(matches(ball.entity,ball.model)) {
        hook.invoke(0x539E0AE3E6634B9FULL,&ball.entity);
        if(exists(ball.entity)){record("fireball_cleanup_failed",ball.entity);return;}
    }
    ball.entity=0;
}
void clear_responders() {
    for(auto& unit:show.responders) {
        for(auto& ped:unit.peds)if(ped) {
            if(matches(ped,unit.ped_model))hook.invoke(0x9614299DCB53E54BULL,&ped);
            else ped=0;
        }
        if(matches(unit.vehicle,unit.car_model)) {
            if(contains_player(unit.vehicle)) {
                // Never delete a car/heli the owner has entered.
                hook.invoke(0xB736A491E64A32CFULL,&unit.vehicle);
            } else hook.invoke(0xEA386986E786A54FULL,&unit.vehicle);
        } else unit.vehicle=0;
        if(unit.car_model)hook.invoke(0xE532F5D78798DAABULL,unit.car_model);
        if(unit.ped_model)hook.invoke(0xE532F5D78798DAABULL,unit.ped_model);
        if(!unit.vehicle&&std::all_of(unit.peds.begin(),unit.peds.end(),[](int x){return !x;}))unit={};
    }
    const bool empty=std::all_of(show.responders.begin(),show.responders.end(),[](const Responder& r){return !r.vehicle&&std::all_of(r.peds.begin(),r.peds.end(),[](int p){return !p;});});
    if(show.response_group&&empty){hook.invoke(0xB6BA2444AB393DA2ULL,show.response_group);show.response_group=0;}
}
void clear_showcase() {
    end_film_camera();release_traffic();show.wave=false;
    for(auto& ball:show.fireballs)retire_fireball(ball);
    clear_responders();show.boss=0;show.second_phase=false;show.phase_banner=0;
    show.reset_pending=false;
    if(show.rock_model){hook.invoke(0xE532F5D78798DAABULL,show.rock_model);show.rock_model=0;}
}
bool ambient_throwable(int entity,int player) {
    if(!exists(entity)||entity==owned_helicopter||entity==qa.vehicle||contains_player(entity)||
       hook.invoke<int>(0x0A7B270912999B3CULL,entity))return false;
    if(hook.invoke<int>(0x997ABD671D25CA0BULL,player,false)&&hook.invoke<int>(0x9A9112A0FE9A4713ULL,player,false)==entity)return false;
    return hook.invoke<int>(0x7F6DB52EEFC96DF8ULL,hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,entity))!=0;
}
void gather_traffic(Actor& actor,int player,std::uint32_t now) {
    release_traffic();const auto base=coords(actor.entity);int count=0;
    for(int i=0;i<nearby_vehicle_count&&count<(actor.combat.second_phase()?5:3);i++) {
        const int car=nearby_vehicles[i].entity;
        if(!ambient_throwable(car,player))continue;
        auto p=coords(car);
        if(!finite(p)||ergt::length(ergt::subtract(p,base))>35||!hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,car,17))continue;
        show.traffic[count++]={car,hook.invoke<std::uint32_t>(0x9F47B058362C84B5ULL,car)};
    }
    show.traffic_until=now+6000;record("gravity_gathered",actor.entity,static_cast<float>(count));
}
void lift_traffic(Actor& actor,int player,std::uint32_t now) {
    if(!show.traffic_until)return;
    if(ergt::deadline_passed(now,show.traffic_until)){release_traffic();return;}
    const auto base=coords(actor.entity);
    for(std::size_t i=0;i<show.traffic.size();i++) {
        auto& car=show.traffic[i];if(!car.entity)continue;
        if(!matches(car.entity,car.model)||!ambient_throwable(car.entity,player)){car={};continue;}
        const float angle=static_cast<float>(i)*1.256637f;
        const auto anchor=ergt::add(base,{std::cos(angle)*9.f,std::sin(angle)*9.f,10.f+static_cast<float>(i)*.7f});
        const auto p=coords(car.entity);if(!finite(p)){car={};continue;}
        // Velocity steering, no collision/gravity disable or teleporting.
        const auto v=ergt::limited(ergt::scale(ergt::subtract(anchor,p),2.2f),13.f);
        hook.invoke(0x1C99BB7B6E96D16FULL,car.entity,v.x,v.y,v.z+.4f);glow(p,true,3.f);
    }
}
void throw_traffic(Actor& actor,int player) {
    for(auto& car:show.traffic)if(car.entity&&matches(car.entity,car.model)&&ambient_throwable(car.entity,player)) {
        const auto v=ergt::throw_velocity(coords(car.entity),show.aim);
        hook.invoke(0x1C99BB7B6E96D16FULL,car.entity,v.x,v.y,v.z);record("gravity_car_thrown",car.entity,ergt::length(v));
    }
    record("gravity_release_source_cue",actor.entity);release_traffic();
}
void launch_fireballs(Actor& actor,std::uint32_t now) {
    if(!show.rock_model||!hook.invoke<int>(0x98A4EB5D89A0C952ULL,show.rock_model)) {
        record("fireball_model_not_ready",actor.entity);return;
    }
    // Launch from the sampled source shield/weapon tip, not from the target.
    const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
    const auto pose=ergt::sample_motion(*actor.motion,phase);
    auto from=ergt::add(coords(actor.entity),ergt::rotate_heading(pose.blade_tip,actor.motion_heading+pose.yaw*57.2957795f));
    auto direction=ergt::projectile_velocity(from,show.aim,1.f);from=ergt::add(from,ergt::scale(direction,3.f));
    if(!finite(from)||!finite(show.aim)||ergt::length(direction)<.5f)return;
    const int count=actor.combat.second_phase()?3:1;
    for(int i=0;i<count;i++) {
        auto slot=std::find_if(show.fireballs.begin(),show.fireballs.end(),[](const Fireball& f){return !f.entity&&!f.probe;});
        if(slot==show.fireballs.end())break;
        auto aim=show.aim;
        if(i){const float side=i==1?-7.f:7.f;aim.x+=-direction.y*side;aim.y+=direction.x*side;}
        const int entity=hook.invoke<int>(0x9A294B2138ABB884ULL,show.rock_model,from.x,from.y,from.z,false,true,false,0);
        if(!exists(entity)){record("fireball_create_failed");break;}
        hook.invoke(0xAD738C3085FE7E11ULL,entity,true,true);
        hook.invoke(0x1A9205C1B9EE827FULL,entity,false,false);
        hook.invoke(0x428CA6DBD1094446ULL,entity,true);
        *slot={entity,0,actor.entity,show.rock_model,now,0,from,{},ergt::projectile_velocity(from,aim,38.f),true};
        record("fireball_launched_source_cue",entity,phase);
    }
}
void tick_fireballs(std::uint32_t now,int dt,bool enabled) {
    for(auto& ball:show.fireballs) {
        if(ball.entity&&!matches(ball.entity,ball.model)){ball.entity=0;ball.active=false;}
        if(!enabled||now-ball.born>6000||!exists(ball.boss))retire_fireball(ball);
        if(ball.probe) {
            int hit=0,entity=0;ergt::NativeVector point{},normal{};
            const int result=hook.invoke<int>(0x3D87450E15D98694ULL,ball.probe,&hit,&point,&normal,&entity);
            if(result==1) {if(now-ball.cast_at>300)retire_fireball(ball);continue;}
            ball.probe=0;
            if(!ball.active)continue;
            if(result!=2||now-ball.cast_at>300){retire_fireball(ball);continue;}
            if(hit) {
                const ergt::Vec3 contact{point.x,point.y,point.z};
                if(finite(contact)){
                    // Explosion is only a native collision consequence. Missing
                    // or pending casts cannot detonate at a predicted target.
                    hook.invoke(0xE3AD2BDBAEE269ACULL,contact.x,contact.y,contact.z,3,.45f,true,false,.15f,false);
                    record("fireball_native_impact",ball.entity);
                }
                retire_fireball(ball);continue;
            }
            ball.position=ball.next;
            hook.invoke(0x239A3351AC1DA385ULL,ball.entity,ball.position.x,ball.position.y,ball.position.z,true,true,false);
        }
        if(!ball.active)continue;
        orb(ball.position,false,2.3f);
        // No catch-up teleport after a frame stall. Wait for each swept sphere.
        ball.next=ergt::add(ball.position,ergt::scale(ball.velocity,std::clamp(dt,0,50)*.001f));
        ball.cast_at=now;
        ball.probe=hook.invoke<int>(0x28579D1B8F8AAC80ULL,ball.position.x,ball.position.y,ball.position.z,
            ball.next.x,ball.next.y,ball.next.z,1.0f,31,ball.boss,7);
        if(!ball.probe)retire_fireball(ball);
    }
}

void start_shockwave(Actor& actor) {
    if(!actor.motion||!actor.motion->has_blade)return;
    const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
    if(!std::isfinite(phase)||phase<0||phase>1)return;
    const auto pose=ergt::sample_motion(*actor.motion,phase);
    auto contact=ergt::add(coords(actor.entity),ergt::rotate_heading(pose.blade_tip,actor.motion_heading+pose.yaw*57.2957795f));
    float ground=0;
    if(!finite(contact)||!hook.invoke<int>(0xC906A7DAB05C8D2BULL,contact.x,contact.y,contact.z+3.f,&ground,false,false)||!std::isfinite(ground))return;
    contact.z=ground;show.wave=true;show.wave_radius=0;show.wave_origin=contact;show.wave_count=0;
    record("shockwave_source_cue",actor.entity);
}
void tick_shockwave(Actor& actor,int dt) {
    if(!show.wave)return;
    const float before=show.wave_radius;show.wave_radius+=std::clamp(dt,0,50)*.025f;
    const float maximum=actor.spec==&ergt::creatures[2]?48.f:24.f;
    const auto centre=show.wave_origin;
    if(show.wave_radius>maximum){show.wave=false;return;}
    hook.invoke(0x28477EC23D892089ULL,1,centre.x,centre.y,centre.z+.15f,0.f,0.f,0.f,0.f,0.f,0.f,
        show.wave_radius*2.f,show.wave_radius*2.f,.15f,235,140,50,65,false,false,2,false,
        static_cast<const char*>(nullptr),static_cast<const char*>(nullptr),false);
    auto hit_once=[&](int e,bool car){
        if(!exists(e))return;
        if(std::find(show.wave_victims.begin(),show.wave_victims.begin()+show.wave_count,e)!=show.wave_victims.begin()+show.wave_count)return;
        const auto p=coords(e);const float d=ergt::horizontal_distance(centre,p);
        if(!ergt::wave_crossed(before,show.wave_radius,d,p.z-centre.z)||!hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,e,17))return;
        if(show.wave_count==static_cast<int>(show.wave_victims.size()))return;
        show.wave_victims[show.wave_count++]=e;
        if(car){
            const auto v=ergt::projectile_velocity(centre,{p.x,p.y,centre.z},7.f);
            hook.invoke(0x18FF00FC7EFF559EULL,e,1,v.x,v.y,2.5f,false,false,true,false);
            const float health=hook.invoke<float>(0xC45D23BAF168AAB8ULL,e);
            hook.invoke(0x45F6D8EEF34ABEF1ULL,e,health-100.f);
        } else hook.invoke(0x697157CED63F18D4ULL,e,25,true,0,0u);
        record("shockwave_contact",e);
    };
    for(int i=0;i<nearby_vehicle_count;i++)hit_once(nearby_vehicles[i].entity,true);
    for(int i=0;i<nearby_ped_count;i++)if(!hook.invoke<int>(0x997ABD671D25CA0BULL,nearby_peds[i],false))hit_once(nearby_peds[i],false);
}

void equip_responder(int ped,std::uint32_t weapon) {
    if(!exists(ped))return;
    if(!show.response_group) {
        hook.invoke(0xF372BC22FCB88606ULL,"ERGT_CITY_SUPPORT",&show.response_group);
        if(show.response_group) {
            hook.invoke(0xBF25EB89375A37ADULL,2,show.response_group,hash("PLAYER"));
            hook.invoke(0xBF25EB89375A37ADULL,2,hash("PLAYER"),show.response_group);
        }
    }
    if(show.response_group)hook.invoke(0xC80A74AC829DDD92ULL,ped,show.response_group);
    hook.invoke(0x9F8AA94D6D97DBF4ULL,ped,true);
    hook.invoke(0x971D38760FBC02EFULL,ped,true);
    hook.invoke(0x7AEFB85C1D49DEB6ULL,ped,25);
    hook.invoke(0xC7622C0D36B2FDA8ULL,ped,2);
    hook.invoke(0xBF0FD6E56C964FCBULL,ped,weapon,600,false,true);
}
void tick_city(Actor& actor,int player,std::uint32_t now) {
    if(!show.city||!fighting||actor.combat.state()==ergt::CombatState::defeated){clear_responders();return;}
    const auto base=coords(actor.entity);const auto owner=coords(player);
    for(std::size_t i=0;i<show.responders.size();i++) {
        auto& unit=show.responders[i];
        const unsigned delay=i==0?6000u:i==1?18000u:30000u;
        if(now-show.began<delay)continue;
        if(!unit.attempted) {
            unit.attempted=true;unit.requested=now;
            unit.car_model=hash(i==0?"police":i==1?"fbi2":"polmav");
            unit.ped_model=hash(i==0?"s_m_y_cop_01":"s_m_y_swat_01");
            if(!hook.invoke<int>(0x35B9E0803292B641ULL,unit.car_model)||!hook.invoke<int>(0x35B9E0803292B641ULL,unit.ped_model)) {
                record("city_model_unavailable");unit.requested=0;continue;
            }
            hook.invoke(0x963D27A58DF860ACULL,unit.car_model);hook.invoke(0x963D27A58DF860ACULL,unit.ped_model);
        }
        if(unit.requested&&!unit.vehicle) {
            if(now-unit.requested>8000) {
                hook.invoke(0xE532F5D78798DAABULL,unit.car_model);hook.invoke(0xE532F5D78798DAABULL,unit.ped_model);
                unit.requested=0;record("city_streaming_timeout");continue;
            }
            if(!hook.invoke<int>(0x98A4EB5D89A0C952ULL,unit.car_model)||!hook.invoke<int>(0x98A4EB5D89A0C952ULL,unit.ped_model))continue;
            ergt::NativeVector road{};float heading=0;
            const float sign=i==1?-1.f:1.f;
            bool safe=hook.invoke<int>(0xFF071FB798B803B0ULL,owner.x+sign*65.f,owner.y+40.f,owner.z,&road,&heading,1,3.f,0.f)!=0;
            ergt::Vec3 p{road.x,road.y,road.z+1.f};
            safe=safe&&finite(p)&&ergt::horizontal_distance(p,owner)>25&&ergt::horizontal_distance(p,owner)<150&&
                ergt::horizontal_distance(p,base)>actor.spec->body_radius+20.f;
            if(i!=2)for(int v=0;v<nearby_vehicle_count;v++)if(exists(nearby_vehicles[v].entity)&&
                ergt::length(ergt::subtract(coords(nearby_vehicles[v].entity),p))<7.f)safe=false;
            // Spawn on a real road node; air support starts above that node.
            // Failed placement is a logged skip, not an unsafe player teleport.
            if(!safe){unit.requested=0;record("city_no_safe_road");continue;}
            if(i==2)p.z+=std::max(45.f,actor.spec->body_height+20.f);
            unit.vehicle=hook.invoke<int>(0xAF35D0D2583051B0ULL,unit.car_model,p.x,p.y,p.z,heading,false,true,false);
            unit.requested=0;
            if(!exists(unit.vehicle)){unit.vehicle=0;record("city_vehicle_failed");continue;}
            hook.invoke(0xAD738C3085FE7E11ULL,unit.vehicle,true,true);
            hook.invoke(0x2497C4717C8B881EULL,unit.vehicle,true,true,false);
            hook.invoke(0xF4924635A19EB37DULL,unit.vehicle,true);
            const int count=i==2?3:2;
            for(int n=0;n<count;n++) {
                const int seat=i==2?(n==0?-1:n):n-1;
                unit.peds[n]=hook.invoke<int>(0x7DD959874C1FD534ULL,unit.vehicle,6,unit.ped_model,seat,false,true);
                equip_responder(unit.peds[n],hash(i==0?"WEAPON_PISTOL":"WEAPON_CARBINERIFLE"));
            }
            if(exists(unit.peds[0])&&i!=2)hook.invoke(0x158BB33F920D360CULL,unit.peds[0],unit.vehicle,base.x,base.y,base.z,12.f,786603,std::max(20.f,actor.spec->body_radius+16.f));
            unit.last_task=now;record("city_unit_arrived",unit.vehicle,static_cast<float>(i));
            hook.invoke(0xE532F5D78798DAABULL,unit.car_model);hook.invoke(0xE532F5D78798DAABULL,unit.ped_model);
        }
        if(!matches(unit.vehicle,unit.car_model)||now-unit.last_task<2000)continue;
        unit.last_task=now;
        if(contains_player(unit.vehicle))continue;
        if(i==2) {
            const float angle=(now-show.began)*.00012f;
            const float radius=std::max(55.f,actor.spec->body_radius+40.f);
            const auto destination=ergt::add(base,{std::cos(angle)*radius,std::sin(angle)*radius,actor.spec->body_height+20.f});
            // Mission 4 accepts coordinates; mode9 does not. Fly successive
            // waypoints around the object boss using a genuine native pilot.
            if(matches(unit.peds[0],unit.ped_model))hook.invoke(0xDAD029E187A2BEB4ULL,unit.peds[0],unit.vehicle,0,0,
                destination.x,destination.y,destination.z,4,18.f,8.f,-1.f,120,25,15.f,0);
        } else if(!unit.arrived) {
            if(ergt::horizontal_distance(coords(unit.vehicle),base)<actor.spec->body_radius+35.f||now-show.began>delay+14000){
                unit.arrived=true;
                for(int ped:unit.peds)if(matches(ped,unit.ped_model))hook.invoke(0xD3DBCE61A490BE02ULL,ped,unit.vehicle,0);
            }
            continue;
        }
        for(std::size_t n=i==2?1:0;n<unit.peds.size();n++) {
            const int ped=unit.peds[n];
            if(!matches(ped,unit.ped_model)||hook.invoke<int>(0x3317DEDB88C95038ULL,ped,true))continue;
            if(i!=2&&hook.invoke<int>(0x997ABD671D25CA0BULL,ped,false))continue;
            if(i!=2&&ergt::horizontal_distance(coords(ped),base)>45.f)
                hook.invoke(0x6A071245EB0D1882ULL,ped,actor.entity,2500,30.f,2.f,0.f,0);
            else hook.invoke(0x08DA95E8298AE772ULL,ped,actor.entity,2200,hash("FIRING_PATTERN_BURST_FIRE"));
        }
    }
}

void tick_showcase_actor(Actor& actor,int player,std::uint32_t now,int dt) {
    if(show.boss!=actor.entity) {
        clear_showcase();show.boss=actor.entity;show.began=now;show.animation=0;show.cue={};
        if(actor.spec==&ergt::creatures[2]) {
            show.rock_model=hash("prop_rock_4_big2");
            if(hook.invoke<int>(0x35B9E0803292B641ULL,show.rock_model))hook.invoke(0x963D27A58DF860ACULL,show.rock_model);
            else {show.rock_model=0;record("fireball_model_unavailable");}
        }
    }
    const auto state=actor.combat.state();
    if(actor.combat.second_phase()&&!show.second_phase) {
        show.second_phase=true;show.phase_banner=now+3500;
        record("phase_two_started",actor.entity,actor.combat.health());
    }
    const bool alive=state!=ergt::CombatState::defeated&&!actor.cleanup_requested;
    const bool attacking=alive&&fighting&&actor.active_clip&&actor.animation_accepted&&actor.motion&&
        std::strcmp(actor.active_clip,actor.spec->attack_clip)==0&&
        (state==ergt::CombatState::melee_windup||state==ergt::CombatState::ranged_windup||state==ergt::CombatState::recovering);
    if(!attacking) {release_traffic();show.animation=0;}
    else {
        if(show.animation!=actor.animation_started) {
            show.animation=actor.animation_started;show.cue={};
            show.aim=exists(actor.target)?coords(actor.target):coords(player);
            if(actor.spec==&ergt::creatures[1])gather_traffic(actor,player,now);
        }
        lift_traffic(actor,player,now);
        const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
        const bool playing=hook.invoke<int>(0x1F0B79228E461EC9ULL,actor.entity,actor.spec->dictionary,actor.active_clip,3)!=0;
        if(actor.motion->contacts&&actor.motion->contact_count>0&&show.cue.sample(phase,actor.motion->contacts[0].start,actor.motion->duration,playing)) {
            if(actor.spec==&ergt::creatures[1])throw_traffic(actor,player);
            if(actor.spec==&ergt::creatures[2]) {
                launch_fireballs(actor,now);
                if(actor.melee_clip)start_shockwave(actor);
            }
            if(actor.spec==&ergt::creatures[3]&&show.second_phase)start_shockwave(actor);
        }
    }
    if(!alive||!fighting)show.wave=false;
    if(alive&&fighting)tick_shockwave(actor,dt);
    tick_fireballs(now,dt,alive&&fighting);
    tick_city(actor,player,now);
    if(alive&&show.second_phase) {
        const auto base=coords(actor.entity);
        glow(ergt::add(base,{0,0,actor.spec->body_height*.45f}),actor.spec==&ergt::creatures[1],actor.spec->body_height*.6f);
        if(!ergt::deadline_passed(now,show.phase_banner))text(.40f,.18f,"PHASE II - UNBOUND",.5f);
    }
}

void tick_film(int player,std::uint32_t now) {
    if(show.film&&!hook.invoke<int>(0xF3A21BCD95725A4AULL,0,37))hook.invoke(0x719FF505F097FD20ULL);
    if(show.camera_probe) {
        int hit=0,entity=0;ergt::NativeVector point{},normal{};
        const int status=hook.invoke<int>(0x3D87450E15D98694ULL,show.camera_probe,&hit,&point,&normal,&entity);
        if(status!=1) {
            show.camera_probe=0;
            if(status==2&&show.view&&now-show.camera_cast_at<=300) {
                show.camera_safe=hit?ergt::Vec3{point.x+normal.x*.5f,point.y+normal.y*.5f,point.z+normal.z*.5f}:show.camera_desired;
                show.camera_ready=finite(show.camera_safe);
            }else show.camera_ready=false;
        }
    }
    if(!show.view)return;
    auto& actor=actors[0];
    bool input=false;
    for(int control:{24,25,30,31,59,60,71,72,75,87,88,89,90,91,92,200})
        input=input||hook.invoke<int>(0xF3A21BCD95725A4AULL,0,control);
    const bool valid=actor.spec&&exists(actor.entity)&&!actor.cleanup_requested;
    if(ergt::camera_interrupted(input,false,false,hook.invoke<int>(0x3317DEDB88C95038ULL,player,true),valid)||ergt::deadline_passed(now,show.camera_until)) {
        end_film_camera();return;
    }
    const auto base=coords(actor.entity);const float height=actor.spec->body_height;
    const float heading=hook.invoke<float>(0xE83D4F9BA2A38914ULL,actor.entity);
    const auto target=ergt::add(base,{0,0,height*(show.view==3?.78f:.45f)});
    const auto offset=show.view==1?ergt::Vec3{0,-height*1.5f,height*.6f}:
        show.view==2?ergt::Vec3{height*1.2f,-height*.2f,height*.55f}:ergt::Vec3{0,-height*.65f,height*.8f};
    if(!show.camera_probe) {
        show.camera_desired=ergt::add(base,ergt::rotate_heading(offset,heading));show.camera_cast_at=now;
        show.camera_probe=hook.invoke<int>(0x7EE9F5D83DD4F90EULL,target.x,target.y,target.z,
            show.camera_desired.x,show.camera_desired.y,show.camera_desired.z,1,actor.entity,7);
        if(!show.camera_probe)show.camera_ready=false;
    }
    if(!show.camera_ready)return;
    if(!show.camera) {
        show.camera=hook.invoke<int>(0xB51194800B257161ULL,"DEFAULT_SCRIPTED_CAMERA",show.camera_safe.x,show.camera_safe.y,show.camera_safe.z,0.f,0.f,0.f,45.f,true,2);
        if(!show.camera){end_film_camera();return;}
        hook.invoke(0x07E5B515DB0636FCULL,true,false,0,true,false,0);
    }
    hook.invoke(0x4D41783FB745E42EULL,show.camera,show.camera_safe.x,show.camera_safe.y,show.camera_safe.z);
    hook.invoke(0xF75497BB865F0803ULL,show.camera,target.x,target.y,target.z);
}
void remember_boss_spawn(int preset,ergt::Vec3 origin,float heading) {
    show.spawn_saved=true;show.spawn_preset=preset;show.spawn_origin=origin;show.spawn_heading=heading;
}
void request_encounter_reset(std::uint32_t now) {
    if(!show.spawn_saved){std::snprintf(notice,sizeof(notice),"Spawn a boss first (2), then 0 resets its encounter.");return;}
    const int preset=show.spawn_preset;
    const int player=hook.invoke<int>(0xD80958FC74E988A6ULL);
    const auto p=exists(player)?coords(player):show.spawn_origin;
    if(ergt::horizontal_distance(p,show.spawn_origin)<ergt::creatures[preset].body_radius+5.f&&
       std::abs(p.z-show.spawn_origin.z)<ergt::creatures[preset].body_height+5.f){
        std::snprintf(notice,sizeof(notice),"Move away from the original boss spawn, then press 0 again.");return;
    }
    clear();selected=preset;show.reset_pending=true;show.reset_until=now+5000;
    record("encounter_reset_requested");
}
void tick_encounter_reset(std::uint32_t now) {
    if(!show.reset_pending)return;
    if(ergt::deadline_passed(now,show.reset_until)) {
        show.reset_pending=false;std::snprintf(notice,sizeof(notice),"Reset cleanup did not finish. Press 3 and check the log.");return;
    }
    if(std::any_of(actors.begin(),actors.end(),[](const Actor& a){return a.entity!=0;}))return;
    show.reset_pending=false;begin_spawn(false,now);
    if(pending.active&&!pending.vehicle) {
        pending.use_anchor=true;pending.anchor=show.spawn_origin;pending.heading=show.spawn_heading;
    }
}
