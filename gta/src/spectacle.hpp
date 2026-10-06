// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "motion.hpp"

namespace ergt {
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
