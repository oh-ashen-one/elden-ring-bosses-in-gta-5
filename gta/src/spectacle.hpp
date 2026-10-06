// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "motion.hpp"

namespace ergt {
struct SpawnPoint { Vec3 point;bool valid; };
template<class Clear> SpawnPoint separate_spawn(Vec3 origin,float radius,Clear clear,bool anchored=false) {
    if(!finite_vec(origin)||!std::isfinite(radius)||radius<0)return {origin,false};
    if(clear(origin))return {origin,true};
    if(anchored)return {origin,false};
    // Search a bounded neighborhood instead of piling new bosses together.
    for(int ring=1;ring<=4;ring++)for(int angle=0;angle<12;angle++) {
        const float a=angle*.523598776f,d=ring*std::max(8.f,radius*2.f+4.f);
        const auto candidate=add(origin,{std::cos(a)*d,std::sin(a)*d,0});
        if(clear(candidate))return {candidate,true};
    }
    return {origin,false};
}
inline Vec3 boss_target_point(Vec3 attacker,Vec3 victim,float radius) {
    const float distance=horizontal_distance(attacker,victim);
    if(distance<.01f)return victim;
    const float reach=std::min(std::max(0.f,radius-.15f),distance);
    return {victim.x+(attacker.x-victim.x)/distance*reach,victim.y+(attacker.y-victim.y)/distance*reach,victim.z};
}
inline Vec3 limited(Vec3 v,float maximum) {
    if(!finite_vec(v))return {};
    const float n=length(v);return n>maximum?scale(v,maximum/n):v;
}
inline Vec3 projectile_velocity(Vec3 from,Vec3 target,float speed) {
    if(!finite_vec(from)||!finite_vec(target)||!std::isfinite(speed)||speed<=0)return {};
    auto delta=subtract(target,from);const float d=length(delta);
    return d>.01f?scale(delta,speed/d):Vec3{};
}
inline Vec3 throw_velocity(Vec3 from,Vec3 target) {
    if(!finite_vec(from)||!finite_vec(target))return {};
    const float seconds=std::clamp(length(subtract(target,from))/32.f,.65f,2.5f);
    auto v=scale(subtract(target,from),1.f/seconds);v.z+=4.905f*seconds;
    return limited(v,65.f);
}
// A source event fires once, from observed playback only. Rewinds, missing
// animation, rejected playback and big phase skips never manufacture a hit.
struct PhaseCue {
    float previous=-1;bool fired=false;
    bool sample(float phase,float cue,float duration,bool playing) {
        const float old=previous;previous=phase;
        if(fired||!playing||!std::isfinite(phase)||!std::isfinite(cue)||!std::isfinite(duration)||duration<=0||
           old<0||phase<old||phase>1||(phase-old)*duration>.30f)return false;
        if(old<=cue && phase>=cue){fired=true;return true;}return false;
    }
};
inline bool deadline_passed(std::uint32_t now,std::uint32_t end) {
    return static_cast<std::int32_t>(now-end)>=0;
}
inline bool camera_interrupted(bool moved,bool attacked,bool paused,bool dead,bool actor_valid) {
    return moved||attacked||paused||dead||!actor_valid;
}
inline bool wave_crossed(float previous,float radius,float distance,float height) {
    return std::isfinite(distance)&&std::isfinite(height)&&distance>=previous-1.2f&&distance<=radius+1.2f&&std::abs(height)<3.f;
}
} // namespace ergt
