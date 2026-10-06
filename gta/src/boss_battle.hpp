// SPDX-License-Identifier: Apache-2.0
// Production source-weapon sweeps against other imported object bosses.
void damage_boss(Actor& victim,Actor& attacker,float damage,const char* event) {
    if(victim.entity==attacker.entity||!living_boss(victim)||!std::isfinite(damage)||damage<=0)return;
    victim.combat.damage(damage);victim.boss_attacker=attacker.entity;
    record(event,victim.entity,damage);
}
void boss_blade_contacts(Actor& actor,std::uint32_t now,bool enabled) {
    using namespace ergt;
    if(!enabled||!actor.motion||!actor.motion->has_blade||!actor.melee_clip||!actor.animation_accepted||
       !actor.active_clip||!actor.motion->contacts||actor.motion->contact_count<=0)return;
    const float phase=hook.invoke<float>(0x346D81500D088F42ULL,actor.entity,actor.spec->dictionary,actor.active_clip);
    const float previous=actor.blade_phase;const auto origin=coords(actor.entity);
    if(!std::isfinite(phase)||previous<0||phase<=previous||phase>1||(phase-previous)*actor.motion->duration>.3f||
       length(subtract(origin,actor.blade_origin))>1.f||!hook.invoke<int>(0x1F0B79228E461EC9ULL,actor.entity,actor.spec->dictionary,actor.active_clip,3))return;
    for(int window=0;window<actor.motion->contact_count;window++) {
        const auto contact=actor.motion->contacts[window];
        const float first=std::max(previous,contact.start),last=std::min(phase,contact.end);
        if(last<first)continue;
        if(actor.boss_window!=window){actor.boss_window=window;actor.boss_victims.clear();}
        for(auto& victim:actors) {
            if(victim.entity==actor.entity||!living_boss(victim))continue;
            if(std::find(actor.boss_victims.begin(),actor.boss_victims.end(),victim.entity)!=actor.boss_victims.end())continue;
            const auto p=coords(victim.entity);
            if(!finite_vec(p)||length(subtract(p,origin))>actor.spec->melee_range+actor.spec->body_height+victim.spec->body_radius+4.f)continue;
            bool hit=false;
            for(int sample=0;sample<=8&&!hit;sample++) {
                const float t=first+(last-first)*sample/8;
                const auto pose=sample_motion(*actor.motion,t);
                const auto base=mix(actor.blade_origin,origin,(t-previous)/(phase-previous));
                for(int weapon=0;weapon<(actor.motion->dual_blade?2:1)&&!hit;weapon++) {
                    const float h=actor.motion_heading+pose.yaw*57.2957795f;
                    const auto a=add(base,rotate_heading(weapon?pose.second_base:pose.blade_base,h));
                    const auto b=add(base,rotate_heading(weapon?pose.second_tip:pose.blade_tip,h));
                    const auto x=hook.invoke<NativeVector>(0x2274BC1C4885E333ULL,victim.entity,a.x,a.y,a.z);
                    const auto y=hook.invoke<NativeVector>(0x2274BC1C4885E333ULL,victim.entity,b.x,b.y,b.z);
                    const float radius=victim.spec->body_radius+actor.spec->weapon_radius;
                    hit=segment_box({x.x,x.y,x.z},{y.x,y.y,y.z},{-radius,-radius,-actor.spec->weapon_radius},
                        {radius,radius,victim.spec->body_height+actor.spec->weapon_radius});
                }
            }
            if(hit&&hook.invoke<int>(0xFCDFF7B72D23A1ACULL,actor.entity,victim.entity,17)) {
                actor.boss_victims.push_back(victim.entity);
                // Boss HP is tuned for GTA guns. Boss-v-boss contact receives
                // its own scale, while player/NPC melee damage is unchanged.
                damage_boss(victim,actor,actor.spec->melee_damage*12.f,"boss_blade_contact");
                if(log_file){std::fprintf(log_file,"event=boss_contact_pair attacker=%d victim=%d phase=%.5f tick=%u\n",actor.entity,victim.entity,phase,now);std::fflush(log_file);}
            }
        }
    }
}
