#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exercise the real damage observer against native-event fixtures, without GTA."""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'src/encounter_plugin.cpp').read_text()
observer = source[source.index('void observe_damage('):source.index('int choose_target(')]
prefix = r'''
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <tuple>
#include <type_traits>
#include "combat.hpp"
struct Frame { int hp=10000; bool weapon=false,vehicle=false; int attacker=0; float weapon_damage=32; bool touching=true; } frame;
struct FakeHook {
 template<class R=void,class...Args> R invoke(std::uint64_t hash,Args... args) {
  if constexpr (std::is_void_v<R>) { return; }
  else {
   auto tuple=std::make_tuple(args...); double result=0;
   if(hash==0xEEF059FAD016D209ULL) result=frame.hp;
   else if(hash==0x131D401334815E94ULL) result=frame.weapon;
   else if(hash==0xDFD5033FDBA0A9C8ULL) result=frame.vehicle;
   else if(hash==0x17FFC1B2BA35A494ULL) result=frame.touching;
   else if(hash==0xC86D67D52A707CF8ULL) {
    if constexpr(sizeof...(Args)>1) {
     if constexpr(std::is_arithmetic_v<std::tuple_element_t<1,decltype(tuple)>>)
      result=std::get<1>(tuple)==frame.attacker;
    }
   } else if(hash==0x3133B907D8B32053ULL) result=frame.weapon_damage;
   return static_cast<R>(result);
  }
 }
} hook;
struct Actor {
 int entity=10,native_health=10000; ergt::Combat combat;
 std::uint32_t last_attacked=0,last_impact=0,last_fallback=0,last_log=0;
 float damage_since_log=0;
};
struct VehicleSample { int entity=100; float speed=0,prior_speed=0; std::uint32_t last_contact=0; int contact_actor=0; };
VehicleSample nearby_vehicles[1]; int nearby_vehicle_count=1;
bool exists(int entity) { return entity!=0; }
void record(const char*,int=0,float=0) {}
void expect(float actual,float expected,const char* why) {
 if(std::abs(actual-expected)>0.001f) { std::fprintf(stderr,"%s\n",why); std::exit(1); }
}
'''
scenarios = r'''
int main() {
 Actor parked; frame={9980,false,true,100,32};
 for(unsigned now=1000;now<2000;now+=100) observe_damage(parked,1,now);
 expect(parked.combat.health(),3600,"Repeated parked contacts drained health");
 Actor slow; nearby_vehicles[0].speed=2; observe_damage(slow,1,1000);
 expect(slow.combat.health(),3600,"Creeping contact bypassed speed threshold");
 Actor moving; nearby_vehicles[0].speed=20; observe_damage(moving,1,1000);
 expect(moving.combat.health(),2640,"Moving impact lost speed-scaled damage");
 observe_damage(moving,1,1100);
 expect(moving.combat.health(),2640,"Impact repeat cooldown failed");
 Actor stopped_after_hit; nearby_vehicles[0]={100,0,20}; observe_damage(stopped_after_hit,1,1000);
 expect(stopped_after_hit.combat.health(),2640,"Recent pre-impact speed was discarded");
 Actor mixed; nearby_vehicles[0]={100,0,0}; frame={9968,true,true,1,32}; observe_damage(mixed,1,1000);
 expect(mixed.combat.health(),3568,"Parked-contact filter swallowed a simultaneous bullet");
 Actor remote_gun; nearby_vehicles[0]={100,35,35}; frame={9970,true,true,100,30,false}; observe_damage(remote_gun,1,3000);
 expect(remote_gun.combat.health(),3570,"Distant helicopter gunfire fabricated physical impact damage");
 Actor remote_rocket; frame={8800,true,true,100,1200,false}; observe_damage(remote_rocket,1,4000);
 expect(remote_rocket.combat.health(),2400,"Vehicle impact filter swallowed a real helicopter rocket");
 Actor explosive; frame={8800,true,false,1,1200}; observe_damage(explosive,1,1000);
 expect(explosive.combat.health(),2400,"Native explosive damage was lost");
 Actor fallback; frame={10000,true,false,1,32}; observe_damage(fallback,1,1000);
 expect(fallback.combat.health(),3568,"Player weapon fallback stopped registering");
 observe_damage(fallback,1,1010);
 expect(fallback.combat.health(),3568,"Fallback cooldown allowed a duplicate hit");
 Actor npc; frame={10000,true,false,2,32}; observe_damage(npc,1,1000);
 expect(npc.combat.health(),3600,"NPC hit flag was fabricated into player damage");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ergt-damage-test-') as folder:
    path = Path(folder)
    (path / 'damage.cpp').write_text(prefix + observer + scenarios)
    subprocess.run(['c++', '-std=c++17', '-I', str(ROOT / 'src'), str(path / 'damage.cpp'),
                    '-o', str(path / 'damage-test')], check=True, timeout=30)
    subprocess.run([str(path / 'damage-test')], check=True, timeout=10)
print('Actual damage-observer fixtures passed; no GTA native/runtime executed.')
