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
    for (int i=0;i<90;i++) hit |= boss.tick(16,o).melee_strike;
    require(!hit, "moving out of range must dodge the committed strike");
    auto ranged_spec=creatures[1];ranged_spec.ranged_enabled=true;
    boss.reset(&ranged_spec); o.target={0,0,30}; o.airborne_target=true;
    require(boss.tick(16,o).telegraph, "airborne target receives a telegraph");
    o.target={25,0,30};
    bool blast=false;
    for(int elapsed=0;elapsed<ranged_spec.windup_ms+32;elapsed+=16) { auto d=boss.tick(16,o); if(d.ranged_strike) { blast=true; require(d.aim.x==0,"ranged attack must not track after lock"); } }
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
    auto paused_reaction=o;paused_reaction.combat_enabled=false;paused_reaction.target_alive=false;
    boss.tick(250,paused_reaction);
    require(boss.state()==CombatState::staggered,"paused aggression or missing target must not erase a physical hit reaction");
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
    for(const auto& spec:creatures) {
        Combat timing(&spec);Observation close{{0,0,0},{spec.melee_range,0,0},true,true,true,false};
        timing.tick(1,close);int elapsed=0;bool struck=false;
        while(elapsed<spec.attack_clip_ms-10) {
            auto d=timing.tick(10,close);elapsed+=10;struck|=d.melee_strike;
            if(struck) {
                require(timing.state()==CombatState::recovering,"recovery covers remaining source attack clip");
                require(animation_intent(timing.state())==AnimationIntent::keep,"hit must not replace attack with idle");
            }
        }
        require(struck,"attack must still land during its windup window");
        close.combat_enabled=false;timing.tick(10,close);
        require(animation_intent(timing.state())==AnimationIntent::idle,"combat OFF cancels playback explicitly");
        timing.damage(100000);
        require(animation_intent(timing.state())==AnimationIntent::death,"death replaces attack playback");
    }
    for(const Vec3 target:std::array<Vec3,4>{{{0,10,0},{10,0,0},{0,-10,0},{-10,0,0}}}) {
        const float angle=heading_to_target({0,0,0},target,180)*3.1415926535f/180;
        // Rotate the measured model-forward vector (0,-1,0) into world space.
        const Vec3 forward{std::sin(angle),-std::cos(angle),0};
        require((forward.x*target.x+forward.y*target.y)/10>0.999f,"imported model must face toward its target");
    }
    for(int encounter=0;encounter<50;encounter++) {
        const auto& spec=creatures[encounter%creatures.size()];boss.reset(&spec);
        require(boss.health()==spec.maximum_health && boss.state()==CombatState::idle,"respawn starts with fresh health and no queued attack");
        o={{0,0,0},{spec.melee_range,0,0},true,true,true,false};boss.tick(1,o);
        bool hit=false;int elapsed=0;
        while(!hit && elapsed<5000) {hit=boss.tick(10,o).melee_strike;elapsed+=10;}
        require(hit && elapsed>=spec.windup_ms && elapsed<spec.windup_ms+10,"hit occurs at configured motion landmark");
        boss.damage(100000);require(!boss.tick(250,o).ranged_strike,"defeated encounter stays inert");
    }
    boss.reset(&creatures[0]);o={{0,0,0},{1,0,0},true,true,true,false};boss.tick(16,o);
    o.target.x=std::numeric_limits<float>::quiet_NaN();auto invalid=boss.tick(250,o);
    require(!invalid.melee_strike && !invalid.ranged_strike && finite_vec(invalid.movement),"invalid target transform cannot create damage or NaN movement");
    boss.reset(&creatures[0]);o={{0,0,0},{1,0,0},true,true,true,false};
    auto space=boss.tick(100,o);require(space.reposition && space.movement.x<0,"Hugging target must create space using real movement");
    o.target.x=5.2f;require(boss.tick(100,o).reposition,"Retreat must retain hysteresis until attack range");
    o.target.x=6.f;require(!boss.tick(100,o).reposition && boss.state()==CombatState::melee_windup,"Retreat must recommit the source attack at range");
    boss.reset(&creatures[2]);boss.damage(300);auto reaction=boss.reaction_generation();
    boss.damage(300);require(boss.reaction_generation()==reaction,"Repeated explosives must not restart stagger every shot");
    for(int i=0;i<40;i++)boss.tick(250,o);
    boss.damage(300);require(boss.reaction_generation()>reaction,"Stagger resistance must expire");
    std::cout << "Combat scenarios passed; no GTA runtime executed\n";
}
