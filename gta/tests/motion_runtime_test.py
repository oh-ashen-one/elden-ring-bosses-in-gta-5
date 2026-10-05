# SPDX-License-Identifier: Apache-2.0
"""Exercise the actual collision/motion/contact helpers against native fixtures.

No engine is launched. These witness asynchronous-result and duplicate-damage
failures, not GTA rendering or subjective play quality.
"""
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).parents[1]
source=(root/'src/encounter_plugin.cpp').read_text()
actor=source[source.index('struct Actor {'):source.index('std::array<Actor, 1> actors;')]
helpers=source[source.index('void move_with_collision('):source.index('bool attack_playback_ready(')]
prefix=r'''
#include <map>
#include <stdexcept>
#include <cstdio>
#include "motion.hpp"
#include "native_bits.hpp"
'''
fixture=r'''
std::map<int,ergt::Vec3> positions;std::map<int,int> cars,hits,engine_hits;
std::array<int,512> nearby_peds{};int nearby_ped_count=0;
FILE* log_file=nullptr;float phase=.35f;int playing=1,cast_status=1,cast_hit=0,next_cast=1000,moves=0;
bool exists(int e){return positions.count(e)>0;}
ergt::Vec3 coords(int e){return positions.at(e);}
void record(const char*,int=0,float=0){}
float number(std::uint64_t v){float f;std::uint32_t x=v;std::memcpy(&f,&x,4);return f;}
struct Hook{
 template<class R=void,class...A>R invoke(std::uint64_t h,A...args){
  std::array<std::uint64_t,sizeof...(A)> a{ergt::native_bits(args)...};
  double result=0;
  if(h==0x3D87450E15D98694ULL){*reinterpret_cast<int*>(a[1])=cast_hit;result=cast_status;}
  else if(h==0xC906A7DAB05C8D2BULL){*reinterpret_cast<float*>(a[3])=0;result=1;}
  else if(h==0x28579D1B8F8AAC80ULL)result=next_cast++;
  else if(h==0x239A3351AC1DA385ULL){positions[a[0]]={number(a[1]),number(a[2]),number(a[3])};moves++;}
  else if(h==0x346D81500D088F42ULL)result=phase;
  else if(h==0x1F0B79228E461EC9ULL)result=playing;
  else if(h==0xE83D4F9BA2A38914ULL)result=0;
  else if(h==0x3317DEDB88C95038ULL)result=0;
  else if(h==0x9A9112A0FE9A4713ULL)result=cars[a[0]];
  else if(h==0x9F47B058362C84B5ULL)result=1;
  else if(h==0x03E8D3D5F549087AULL){
   *reinterpret_cast<ergt::NativeVector*>(a[1])={-1,0,-1,0,-1,0};
   *reinterpret_cast<ergt::NativeVector*>(a[2])={1,0,1,0,1,0};
  }
  else if(h==0xFCDFF7B72D23A1ACULL)result=1;
  else if(h==0x697157CED63F18D4ULL)hits[a[0]]++;
  else if(h==0x45F6D8EEF34ABEF1ULL)engine_hits[a[0]]++;
  else if(h==0xC45D23BAF168AAB8ULL)result=1000;
  else if(h==0x18FF00FC7EFF559EULL){}
  else if(h!=0x2274BC1C4885E333ULL)throw std::runtime_error("unexpected native");
  if constexpr(std::is_same_v<R,ergt::NativeVector>){auto p=positions.at(a[0]);return {number(a[1])-p.x,0,number(a[2])-p.y,0,number(a[3])-p.z,0};}
  else if constexpr(!std::is_void_v<R>)return static_cast<R>(result);
 }
}hook;
void check(bool b,const char* why){if(!b)throw std::runtime_error(why);}
Actor fresh(){Actor a;a.entity=10;a.spec=&ergt::creatures[0];positions[10]={0,0,.055f};moves=0;cast_status=1;cast_hit=0;return a;}
'''
main=r'''
int main(){
 auto a=fresh();move_with_collision(a,{.1f,0,0},100,true);check(moves==0,"unchecked move");
 move_with_collision(a,{},110,true);check(moves==0,"pending cast moved actor");
 cast_status=2;move_with_collision(a,{},120,true);check(moves==1&&positions[10].x>.09f,"clear cast did not move");
 a=fresh();move_with_collision(a,{.1f,0,0},100,true);cast_status=2;cast_hit=1;
 move_with_collision(a,{},120,true);check(moves==0,"wall crossed");
 a=fresh();move_with_collision(a,{.1f,0,0},100,true);positions[10].x=3;cast_status=2;
 move_with_collision(a,{},120,true);check(moves==0&&positions[10].x==3,"impact position overwritten");
 a=fresh();move_with_collision(a,{.1f,0,0},100,true);cast_status=2;a.animation_started++;
 move_with_collision(a,{},120,true);check(moves==0,"old attack cast applied");
 a=fresh();move_with_collision(a,{.1f,0,0},100,true);cast_status=2;
 move_with_collision(a,{},120,false);check(moves==0,"pause moved actor");
 const ergt::MotionSample samples[]={{{},0,{-2,2,1},{2,2,1}},{{},0,{-2,2,1},{2,2,1}}};
 const ergt::ContactWindow windows[]={{.38f,.5f}};
 const ergt::MotionTrack track{"fixture","attack",2.733333f,samples,2,true,false,windows,1};
 a=fresh();a.motion=&track;a.melee_clip=true;a.active_clip="attack";a.animation_accepted=true;
 positions[100]={0,2,1};positions[101]={0,-2,1};nearby_peds[0]=101;nearby_ped_count=1;
 phase=.35f;blade_contacts(a,100,100,true);phase=.42f;blade_contacts(a,100,120,true);
 check(hits[100]==1&&hits[101]==0,"blade geometry victim mismatch");
 phase=.46f;blade_contacts(a,100,140,true);check(hits[100]==1,"repeat blade damage");
 a.blade_victim_count=0;a.blade_phase=.35f;phase=.42f;playing=0;blade_contacts(a,100,160,true);
 check(hits[100]==1,"stopped playback damaged target");playing=1;
 a.blade_phase=.35f;blade_contacts(a,100,180,false);check(hits[100]==1,"pause released hit");
 a.blade_phase=.35f;phase=.99f;blade_contacts(a,100,200,true);check(hits[100]==1,"phase jump released hit");
 a.blade_phase=.35f;phase=.42f;positions[102]={0,2,1};positions[200]={0,2,1};cars[100]=cars[102]=200;
 nearby_peds[0]=102;blade_contacts(a,100,220,true);
 check(engine_hits[200]==1,"passengers duplicated vehicle damage");
 // Two genuine source windows must permit a second hit, but neither window
 // may damage twice. The second weapon must also have a real contact sweep.
 cars.clear();hits.clear();nearby_ped_count=0;
 const ergt::MotionSample dual[]={{{},0,{-2,8,1},{2,8,1},{-2,2,1},{2,2,1}},{{},0,{-2,8,1},{2,8,1},{-2,2,1},{2,2,1}}};
 const ergt::ContactWindow combo_windows[]={{.2f,.3f},{.6f,.7f}};
 const ergt::MotionTrack combo{"fixture","combo",1.f,dual,2,true,true,combo_windows,2};
 a=fresh();a.motion=&combo;a.melee_clip=true;a.active_clip="combo";a.animation_accepted=true;
 phase=.15f;blade_contacts(a,100,300,true);phase=.25f;blade_contacts(a,100,320,true);
 check(hits[100]==1,"secondary sword missed");
 phase=.29f;blade_contacts(a,100,340,true);check(hits[100]==1,"first combo window duplicated damage");
 phase=.45f;blade_contacts(a,100,360,true);phase=.65f;blade_contacts(a,100,380,true);
 check(hits[100]==2,"second source combo window suppressed");
 phase=.69f;blade_contacts(a,100,400,true);check(hits[100]==2,"second combo window duplicated damage");
 puts("Actual runtime helpers: async/stale/blocked movement and native-phase blade damage passed");
}
'''
with tempfile.TemporaryDirectory(prefix='ergt-motion-witness-') as directory:
    p=Path(directory);(p/'test.cpp').write_text(prefix+actor+fixture+helpers+main)
    subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-Werror','-I',str(root/'src'),str(p/'test.cpp'),'-o',str(p/'test')],check=True,timeout=30)
    subprocess.run([str(p/'test')],check=True,timeout=10)
