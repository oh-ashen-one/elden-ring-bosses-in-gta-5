// SPDX-License-Identifier: Apache-2.0
#include <iostream>
#include <limits>
#include <stdexcept>
#include "spectacle.hpp"
void check(bool value,const char* why){if(!value)throw std::runtime_error(why);}
int main(){
    using namespace ergt;
    PhaseCue cue;
    check(!cue.sample(.30f,.4f,3,true),"first observation cannot manufacture crossed contact");
    check(!cue.sample(.35f,.4f,3,false),"stopped animation cannot release an attack");
    check(cue.sample(.41f,.4f,3,true),"actual source crossing releases once");
    check(!cue.sample(.42f,.4f,3,true),"repeat frame cannot throw cars twice");
    cue={};cue.sample(.1f,.4f,3,true);
    check(!cue.sample(.8f,.4f,3,true),"long frame jump must fail closed");
    cue={};cue.sample(.5f,.4f,3,true);
    check(!cue.sample(.1f,.4f,3,true),"rewind cannot release");
    check(length(projectile_velocity({0,0,0},{30,40,0},38))-38<.001f,"finite travelling projectile speed");
    check(length(projectile_velocity({0,0,0},{0,0,0},38))==0,"zero aim cannot divide by zero");
    auto v=throw_velocity({0,0,10},{32,0,0});
    const float t=length(Vec3{32,0,-10})/32.f;
    auto landing=add({0,0,10},scale(v,t));landing.z-=4.905f*t*t;
    check(length(subtract(landing,{32,0,0}))<.01f,"traffic trajectory compensates native gravity");
    check(length(throw_velocity({}, {10000,10000,10000}))<=65.01f,"throw speed is bounded");
    check(length(throw_velocity({}, {NAN,0,0}))==0,"invalid aim rejected");
    check(deadline_passed(5,0xfffffff0u),"deadline survives game clock rollover");
    check(!deadline_passed(0xfffffff0u,5),"future rollover deadline remains pending");
    check(wave_crossed(3,4,3.8f,1)&&!wave_crossed(3,4,10,1)&&!wave_crossed(3,4,3.8f,10),"ground shockwave cannot hit outside ring or an airborne helicopter");
    check(camera_interrupted(true,false,false,false,true)&&camera_interrupted(false,true,false,false,true)&&
        camera_interrupted(false,false,false,false,false),"camera always yields to input or missing boss");
    auto relocated=separate_spawn({0,0,0},2.f,[](Vec3 p){return horizontal_distance(p,{})>10;});
    check(relocated.valid&&horizontal_distance(relocated.point,{})>10,"new bosses search clear space instead of intersecting");
    check(!separate_spawn({0,0,0},2.f,[](Vec3){return false;}).valid,"blocked spawn neighborhood must fail closed");
    check(!separate_spawn({0,0,0},2.f,[](Vec3){return false;},true).valid,"reset cannot silently shift a blocked anchor");
    auto giant_surface=boss_target_point({12,0,0},{},10.4f);
    check(horizontal_distance({12,0,0},giant_surface)<2.f,"small bosses approach giant surface rather than unreachable torso center");
    for(const auto& spec:creatures){
        Combat combat(&spec);Observation o{{},{spec.melee_range,0,0},true,true,true,false};
        // Small hits reach phase threshold without invoking stagger.
        while(combat.ratio()>.5f)combat.damage(100);
        combat.tick(16,o);check(combat.state()==CombatState::phase_transition&&combat.second_phase(),"phase2 visibly interrupts attack once");
        const auto hp=combat.health();combat.damage(100);
        check(combat.health()==hp-100,"phase transition remains vulnerable");
        for(int n=0;n<100;n++)combat.tick(100,o);
        check(combat.state()!=CombatState::phase_transition&&combat.attack_rate()>1,"phase transition cannot loop forever");
        combat.damage(100000);check(combat.state()==CombatState::defeated,"death overrides phase2");
        combat.reset(&spec);check(!combat.second_phase()&&combat.attack_rate()==1&&combat.ratio()==1,"reset clears phase and rate");
    }
    std::cout<<"Phase, flight, camera and reset rules passed; no GTA launched\n";
}
