// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "combat.hpp"
#include <cstring>

namespace ergt {
inline Vec3 add(Vec3 a,Vec3 b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline Vec3 subtract(Vec3 a,Vec3 b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline Vec3 scale(Vec3 a,float s){return {a.x*s,a.y*s,a.z*s};}
inline float dot(Vec3 a,Vec3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline float length(Vec3 a){return std::sqrt(dot(a,a));}
inline Vec3 mix(Vec3 a,Vec3 b,float t){return add(a,scale(subtract(b,a),t));}
inline Vec3 rotate_heading(Vec3 p,float degrees){
    const float a=degrees*0.01745329252f,c=std::cos(a),s=std::sin(a);
    return {c*p.x-s*p.y,s*p.x+c*p.y,p.z};
}
struct MotionSample { Vec3 root; float yaw; Vec3 blade_base,blade_tip; };
struct MotionTrack {
    const char* model; const char* clip; float duration; const MotionSample* samples; int count;
    bool has_blade;
};
inline MotionSample sample_motion(const MotionTrack& track,float phase){
    const float index=std::clamp(phase,0.0f,1.0f)*(track.count-1);
    const int i=std::min(static_cast<int>(index),track.count-2);const float a=index-i;
    const auto& x=track.samples[i];const auto& y=track.samples[i+1];
    return {mix(x.root,y.root,a),x.yaw+(y.yaw-x.yaw)*a,mix(x.blade_base,y.blade_base,a),mix(x.blade_tip,y.blade_tip,a)};
}
struct MotionCursor {
    float phase=0; bool initialized=false;
    // Native phase is authoritative. Missing/stalled playback never advances
    // root motion. A discontinuity is consumed without a catch-up teleport.
    bool advance(const MotionTrack& track,float next,bool loop,float max_seconds,Vec3& delta){
        delta={};
        if(!std::isfinite(next)||next<0||next>1||track.count<2||track.duration<=0)return false;
        if(!initialized){initialized=true;phase=next;return false;}
        const float old=phase;phase=next;
        const bool wrap=loop && old>0.75f && next<0.25f;
        const float span=next-old+(wrap?1.0f:0.0f);
        if(span<=0 || span*track.duration>max_seconds)return false;
        delta=subtract(sample_motion(track,next).root,sample_motion(track,old).root);
        if(wrap)delta=add(delta,subtract(track.samples[track.count-1].root,track.samples[0].root));
        if(!finite_vec(delta)||length(delta)>2.0f){delta={};return false;}
        return true;
    }
};
// Squared distance between two finite line segments (blade and victim axis).
inline float segment_distance_squared(Vec3 p,Vec3 q,Vec3 a,Vec3 b){
    const Vec3 u=subtract(q,p),v=subtract(b,a),w=subtract(p,a);
    const float aa=dot(u,u),bb=dot(u,v),cc=dot(v,v),dd=dot(u,w),ee=dot(v,w);
    float s=0,t=0;const float denom=aa*cc-bb*bb;
    if(aa<1e-8f){t=cc>1e-8f?std::clamp(ee/cc,0.0f,1.0f):0;}
    else if(cc<1e-8f)s=std::clamp(-dd/aa,0.0f,1.0f);
    else{
        s=denom>1e-8f?std::clamp((bb*ee-cc*dd)/denom,0.0f,1.0f):0;
        t=(bb*s+ee)/cc;
        if(t<0){t=0;s=std::clamp(-dd/aa,0.0f,1.0f);}
        else if(t>1){t=1;s=std::clamp((bb-dd)/aa,0.0f,1.0f);}
    }
    const auto d=subtract(add(p,scale(u,s)),add(a,scale(v,t)));return dot(d,d);
}
inline bool segment_box(Vec3 a,Vec3 b,Vec3 low,Vec3 high){
    if(!finite_vec(a)||!finite_vec(b)||!finite_vec(low)||!finite_vec(high)||low.x>high.x||low.y>high.y||low.z>high.z)return false;
    const auto d=subtract(b,a);float lo=0,hi=1;
    const float starts[]={a.x,a.y,a.z},ends[]={d.x,d.y,d.z},mins[]={low.x,low.y,low.z},maxs[]={high.x,high.y,high.z};
    for(int i=0;i<3;i++){
        if(std::abs(ends[i])<1e-7f){if(starts[i]<mins[i]||starts[i]>maxs[i])return false;}
        else {float x=(mins[i]-starts[i])/ends[i],y=(maxs[i]-starts[i])/ends[i];if(x>y)std::swap(x,y);lo=std::max(lo,x);hi=std::min(hi,y);if(lo>hi)return false;}
    }
    return true;
}
// Stale collision results must not snap an actor back after a car impact.
inline bool sweep_still_current(Vec3 planned_from,Vec3 current,unsigned elapsed,bool same_animation){
    return same_animation && elapsed<=150 && finite_vec(current) && length(subtract(planned_from,current))<=0.20f;
}
} // namespace ergt

// Generated from the user's owned game into a PRIVATE build directory. Never
// check this header or the resulting asset-bearing binary into the repository.
#ifdef ERGT_PRIVATE_MOTION_HEADER
#include ERGT_PRIVATE_MOTION_HEADER
#else
namespace ergt { inline constexpr std::array<MotionTrack,0> owned_motion_tracks{}; }
#endif
namespace ergt {
inline const MotionTrack* find_motion(const char* model,const char* clip){
    for(const auto& t:owned_motion_tracks)if(std::strcmp(t.model,model)==0&&std::strcmp(t.clip,clip)==0)return &t;
    return nullptr;
}
}
