// SPDX-License-Identifier: Apache-2.0
// Synthetic author-created tracks only. No retail pose or motion data.
#include "motion.hpp"
#include <stdexcept>
#include <iostream>
void check(bool b){if(!b)throw std::runtime_error("motion/contact regression");}
int main(){
    using namespace ergt;
    const MotionSample s[]={{{0,0,0},0,{},{}},{{0,-2,0},0,{},{}}};
    const MotionTrack t{"fixture","walk",1,s,2,false};MotionCursor c;Vec3 d;
    check(!c.advance(t,0,true,.3f,d));check(c.advance(t,.2f,true,.3f,d));check(std::abs(d.y+.4f)<1e-6);
    check(!c.advance(t,.2f,true,.3f,d));check(!c.advance(t,.9f,true,.3f,d));
    check(c.advance(t,.1f,true,.3f,d));check(std::abs(d.y+.4f)<1e-6); // wrap, no reverse snap
    check(!c.advance(t,.05f,false,.3f,d));check(!c.advance(t,NAN,true,.3f,d));
    const auto world=rotate_heading({0,-1,0},180);check(world.y>.999f);
    check(segment_distance_squared({-2,0,1},{2,0,1},{0,0,0},{0,0,2})<1e-7);
    check(segment_distance_squared({-2,0,1},{2,0,1},{0,3,0},{0,3,2})>8.9f);
    check(segment_distance_squared({0,0,0},{0,0,0},{0,0,2},{0,0,2})==4);
    check(segment_box({-2,0,0},{2,0,0},{-1,-1,-1},{1,1,1}));
    check(!segment_box({-2,2,0},{2,2,0},{-1,-1,-1},{1,1,1}));
    check(sweep_still_current({1,2,3},{1.1f,2,3},50,true));
    check(!sweep_still_current({1,2,3},{2,2,3},50,true)); // external impact wins
    check(!sweep_still_current({1,2,3},{1,2,3},151,true));
    check(!sweep_still_current({1,2,3},{1,2,3},20,false));
    Combat boss(&creatures[0]);Observation o{{0,0,0},{0,0,30},true,true,true,true};
    for(int i=0;i<100;i++){auto result=boss.tick(50,o);check(!result.ranged_strike&&!result.melee_strike&&finite_vec(result.movement));}
    boss.damage(300);o.target={1,0,0};for(int i=0;i<20;i++)boss.tick(50,o);
    check(boss.state()==CombatState::staggered); // full visible reaction survives the old 500 ms cutoff
    std::cout<<"Native-phase motion, loop wrap, blade geometry, collision freshness and stagger checks passed\n";
}
