#include <iostream>
#include <limits>
#include <stdexcept>
#include "combat.hpp"

void require(bool value, const char* why) { if (!value) throw std::runtime_error(why); }
int main() {
    using namespace ergt;
    Combat boss(&creatures[0]);
    Observation o{{0,0,0},{1,0,0},true,true,true,false};
    require(!boss.tick(16,o).melee_strike, "melee attack must give a warning window");
    o.target = {20,0,0};
    bool hit = false;
    for (int i=0;i<60;i++) hit |= boss.tick(16,o).melee_strike;
    require(!hit, "moving out of range must dodge the committed strike");
    boss.reset(&creatures[1]); o.target={0,0,30}; o.airborne_target=true;
    require(boss.tick(16,o).telegraph, "airborne target receives a telegraph");
    o.target={25,0,30};
    bool blast=false;
    for(int i=0;i<100;i++) { auto d=boss.tick(16,o); if(d.ranged_strike) { blast=true; require(d.aim.x==0,"ranged attack must not track after lock"); } }
    require(blast, "ranged strike eventually fires");
    boss.reset(&creatures[0]); o.target={1,0,0};o.airborne_target=false;
    boss.tick(16,o);o.combat_enabled=false;boss.tick(16,o);o.combat_enabled=true;
    require(!boss.tick(250,o).melee_strike,"combat toggle cannot release a banked attack");
    boss.damage(100000);
    require(boss.state()==CombatState::defeated && !boss.tick(250,o).melee_strike,"dead boss cannot attack");
    boss.reset(&creatures[2]);
    boss.damage(std::numeric_limits<float>::quiet_NaN());
    require(boss.health()==creatures[2].maximum_health,"invalid damage cannot poison health");
    boss.damage(300); require(boss.state()==CombatState::staggered,"heavy impact staggers");
    require(boss.tick(0,o).movement.x==0,"zero-time update cannot advance combat");
    boss.reset(&creatures[1]);o.target={20,0,0};
    auto step=boss.tick(10000,o);
    require(std::hypot(step.movement.x,step.movement.y)<=creatures[1].speed*0.25f+0.001f,"stale frame cannot teleport creature");
    o.line_of_sight=false;require(boss.tick(16,o).movement.x==0,"blocked sight does not move through walls");
    o.target_alive=false;require(boss.tick(16,o).movement.x==0,"dead player stops pursuit");
    require(impact_damage(0)==0 && impact_damage(2)==0,"parked/creeping cars cannot drain HP");
    require(impact_damage(20)>impact_damage(8),"faster impacts deal greater damage");
    require(impact_damage(1000)==1400,"impact damage has a finite ceiling");
    require(impact_damage(std::numeric_limits<float>::infinity())==0,"invalid physics sample rejected");
    require(target_score(10,true,false)<target_score(10,false,false),"current target hysteresis prevents thrashing");
    require(target_score(20,false,true)<target_score(10,false,false),"nearby attacker gets retaliation priority");
    boss.reset(&creatures[0]);o={{0,0,0},{1,0,0},true,true,true,false};
    boss.tick(16,o);boss.tick(250,o);boss.cancel_attack();
    require(!boss.tick(250,o).melee_strike,"changing target cannot transfer a banked strike");
    boss.damage(10000);boss.cancel_attack();
    require(boss.state()==CombatState::defeated,"target selection cannot revive a defeated creature");
    std::cout << "Combat scenarios passed; no GTA runtime executed\n";
}
