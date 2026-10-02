#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compile the actual strike helper; native calls are local fixtures only."""
from pathlib import Path
import argparse
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, default=Path(__file__).parents[1]/'src/encounter_plugin.cpp')
a = p.parse_args()
s = a.source.read_text()
helper = s[s.index('void strike_nearby('):s.index('void update_actor(')]
prefix = r'''
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <tuple>
#include <type_traits>
#include "combat.hpp"
struct Actor {int entity=10;const ergt::CreatureSpec* spec=&ergt::creatures[0];};
std::array<int,512> nearby_peds{};int nearby_ped_count=0;
std::map<int,int> cars, engine_writes, ped_hits;
std::map<int,float> engine_health;
bool exists(int e){return e>0;}
ergt::Vec3 coords(int){return {2,0,0};}
void record(const char*,int=0,float=0){}
struct FakeHook {
 template<class R=void,class...A> R invoke(std::uint64_t h,A...args) {
  auto t=std::make_tuple(args...);const int e=static_cast<int>(std::get<0>(t));
  if constexpr(std::is_void_v<R>) {
   if(h==0x45F6D8EEF34ABEF1ULL){engine_writes[e]++;engine_health[e]=static_cast<float>(std::get<1>(t));}
   if(h==0x697157CED63F18D4ULL)ped_hits[e]++;
   return;
  } else {
   double result=0;
   if(h==0xFCDFF7B72D23A1ACULL)result=1;
   else if(h==0x9A9112A0FE9A4713ULL)result=cars[e];
   else if(h==0xC45D23BAF168AAB8ULL)result=engine_health.count(e)?engine_health[e]:1000;
   return static_cast<R>(result);
  }
 }
}hook;
void check(bool ok,const char* why){if(!ok){std::fprintf(stderr,"%s\n",why);std::exit(1);}}
void reset(){cars.clear();engine_writes.clear();engine_health.clear();ped_hits.clear();nearby_ped_count=0;}
'''
main = r'''
int main(){
 Actor actor;ergt::Vec3 origin{0,0,0},target{4,0,0};
 reset();nearby_peds[0]=101;nearby_ped_count=1;
 strike_nearby(actor,100,origin,target);
 check(ped_hits[100]==1 && ped_hits[101]==1,"On-foot melee victim coverage regressed");
 reset();cars[100]=1000;cars[101]=1000;nearby_peds[0]=101;nearby_ped_count=1;
 strike_nearby(actor,100,origin,target);
 check(engine_writes[1000]==1,"One vehicle took repeated passenger damage");
 for(const int capacity:{33,256}) {
 reset();
 for(int i=0;i<capacity;i++){
  const int driver=100+2*i,passenger=driver+1;cars[driver]=cars[passenger]=1000+i;
  if(driver!=100)nearby_peds[nearby_ped_count++]=driver;
  nearby_peds[nearby_ped_count++]=passenger;
 }
 strike_nearby(actor,100,origin,target);
 for(int i=0;i<capacity;i++)if(engine_writes[1000+i]!=1){
  std::fprintf(stderr,"Dense melee duplicate: vehicle %d received %d hits in one strike\n",1000+i,engine_writes[1000+i]);return 1;
 }
 }
 puts("Actual strike helper: on-foot victims and all occupied vehicles receive at most one hit per strike");
}
'''
with tempfile.TemporaryDirectory(prefix='ergt-strike-witness-') as tmp:
    d = Path(tmp)
    (d/'witness.cpp').write_text(prefix+helper+main)
    subprocess.run(['c++','-std=c++17','-I',str(a.source.parent),str(d/'witness.cpp'),'-o',str(d/'witness')],check=True,timeout=30)
    result = subprocess.run([str(d/'witness')],timeout=10)
    raise SystemExit(result.returncode)
