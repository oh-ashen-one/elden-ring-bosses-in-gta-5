# SPDX-License-Identifier: Apache-2.0
"""Execute the production spectacle adapter with native-world fault fixtures.

No renderer/game. These tests check lifecycle and native effects, not aesthetics
or whether GTA's AI successfully flies/drives/shoots in a real encounter.
"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'src/encounter_plugin.cpp').read_text()
actor = source[source.index('struct Actor {'):source.index('std::array<Actor, 1> actors;')]
fixture = r'''
#include <map>
#include <vector>
#include <string>
#include <cstdio>
#include <stdexcept>
#include "spectacle.hpp"
#include "native_bits.hpp"
struct Entity { unsigned model=1;ergt::Vec3 p{},velocity{};bool mission=false,car=false;std::map<int,int> seats; };
std::map<int,Entity> world;
std::map<std::uint64_t,int> calls;
std::vector<std::string> events;
int cast_result=2,cast_hit=0,next_entity=1000,explosions=0,spawned=0,deletes=0,player_id=1;
bool input_pressed=false,delete_failure=false,models_loaded=true;
float animation_phase=0;ergt::Vec3 cast_point{9,8,7};
bool exists(int id){return world.count(id)>0;}
ergt::Vec3 coords(int id){return world.at(id).p;}
bool finite(ergt::Vec3 p){return ergt::finite_vec(p);}
unsigned hash(const char* p){unsigned h=2166136261u;while(*p)h=(h^static_cast<unsigned char>(*p++))*16777619u;return h;}
void record(const char* e,int=0,float=0){events.push_back(e);}
void text(float,float,const char*,float=.32f){}
float num(std::uint64_t v){std::uint32_t bits=v;float f;std::memcpy(&f,&bits,4);return f;}
void check(bool b,const char* why){if(!b)throw std::runtime_error(why);}
struct Hook {
 template<class R=void,class...A>R invoke(std::uint64_t h,A...args){
  const std::array<std::uint64_t,sizeof...(A)> words{ergt::native_bits(args)...};
  std::array<std::uint64_t,32>a{};std::copy(words.begin(),words.end(),a.begin());calls[h]++;
  double result=0;
  if(h==0x9F47B058362C84B5ULL)result=world.at(a[0]).model;
  else if(h==0xA7C4F2C6E744A550ULL)result=3;
  else if(h==0x22AC59A870E6A669ULL)result=!world.at(a[0]).seats.count(static_cast<int>(a[1]));
  else if(h==0xBB40DD2270B65366ULL)result=world.at(a[0]).seats[static_cast<int>(a[1])];
  else if(h==0x12534C348C6CB68BULL)result=a[0]==1;
  else if(h==0x0A7B270912999B3CULL)result=world.at(a[0]).mission;
  else if(h==0x7F6DB52EEFC96DF8ULL)result=a[0]==hash("taxi");
  else if(h==0xFCDFF7B72D23A1ACULL)result=1;
  else if(h==0x1C99BB7B6E96D16FULL)world.at(a[0]).velocity={num(a[1]),num(a[2]),num(a[3])};
  else if(h==0x239A3351AC1DA385ULL)world.at(a[0]).p={num(a[1]),num(a[2]),num(a[3])};
  else if(h==0x539E0AE3E6634B9FULL||h==0xEA386986E786A54FULL||h==0x9614299DCB53E54BULL){
   int& e=*reinterpret_cast<int*>(a[0]);if(!delete_failure){world.erase(e);e=0;deletes++;}
  }
  else if(h==0xB736A491E64A32CFULL){int& e=*reinterpret_cast<int*>(a[0]);world.at(e).mission=false;e=0;}
  else if(h==0x3D87450E15D98694ULL){
   *reinterpret_cast<int*>(a[1])=cast_hit;
   *reinterpret_cast<ergt::NativeVector*>(a[2])={cast_point.x,0,cast_point.y,0,cast_point.z,0};result=cast_result;
  }
  else if(h==0x28579D1B8F8AAC80ULL||h==0x7EE9F5D83DD4F90EULL)result=500;
  else if(h==0xE3AD2BDBAEE269ACULL){explosions++;check(num(a[0])==cast_point.x&&num(a[1])==cast_point.y,"explosion must be at collision, not target");}
  else if(h==0x98A4EB5D89A0C952ULL||h==0x35B9E0803292B641ULL)result=models_loaded;
  else if(h==0x9A294B2138ABB884ULL||h==0xAF35D0D2583051B0ULL){result=next_entity++;world[result]={static_cast<unsigned>(a[0]),{num(a[1]),num(a[2]),num(a[3])},{},true,h==0xAF35D0D2583051B0ULL,{}};spawned++;}
  else if(h==0x7DD959874C1FD534ULL){result=next_entity++;world[result]={static_cast<unsigned>(a[2]),world.at(a[0]).p,{},true,false,{}};world.at(a[0]).seats[static_cast<int>(a[3])]=result;}
  else if(h==0xFF071FB798B803B0ULL){*reinterpret_cast<ergt::NativeVector*>(a[3])={65,0,40,0,0,0};*reinterpret_cast<float*>(a[4])=0;result=1;}
  else if(h==0xF372BC22FCB88606ULL)*reinterpret_cast<unsigned*>(a[1])=123;
  else if(h==0xD80958FC74E988A6ULL)result=player_id;
  else if(h==0x346D81500D088F42ULL)result=animation_phase;
  else if(h==0x1F0B79228E461EC9ULL)result=1;
  else if(h==0xF3A21BCD95725A4AULL)result=input_pressed;
  else if(h==0xB51194800B257161ULL)result=800;
  if constexpr(std::is_same_v<R,ergt::NativeVector>)return {};
  else if constexpr(!std::is_void_v<R>)return static_cast<R>(result);
 }
}hook;
'''
globals_ = r'''
std::array<Actor,1> actors;
std::array<int,512> nearby_peds{};int nearby_ped_count=0;
struct Vehicle {int entity=0;};std::array<Vehicle,128> nearby_vehicles{};int nearby_vehicle_count=0;
struct {int vehicle=0;}qa;
struct {bool active=false,vehicle=false,use_anchor=false;ergt::Vec3 anchor{};float heading=0;}pending;
int owned_helicopter=0,selected=0;bool fighting=true;char notice[192]{};
void clear();
void begin_spawn(bool,std::uint32_t){pending.active=true;}
#include "spectacle_runtime.hpp"
void clear(){clear_showcase();actors={};}
void reset_fixture(){
 show={};actors={};pending={};world.clear();calls.clear();events.clear();explosions=0;deletes=0;spawned=0;
 cast_result=2;cast_hit=0;input_pressed=false;delete_failure=false;models_loaded=true;fighting=true;
 nearby_vehicle_count=0;nearby_ped_count=0;
 world[1]={1,{0,0,0},{},false,false,{}};
 world[40]={40,{0,30,0},{},true,false,{}};
 actors[0].entity=40;actors[0].spec=&ergt::creatures[2];actors[0].combat.reset(actors[0].spec);
 show.boss=40;show.began=1;
}
void ball(){world[50]={50,{0,0,3},{},true,false,{}};show.fireballs[0]={50,0,40,50,100,0,{0,0,3},{},{38,0,0},true};}
int main(){
 reset_fixture();ball();cast_result=1;tick_fireballs(100,16,true);tick_fireballs(116,16,true);
 check(explosions==0&&coords(50).x==0,"pending collision cannot move or detonate");
 cast_result=2;tick_fireballs(132,16,true);check(coords(50).x>0&&explosions==0,"clear sweep advances projectile");
 cast_hit=1;tick_fireballs(148,16,true);check(explosions==1&&!exists(50),"collision detonates once and removes projectile");
 tick_fireballs(164,16,true);check(explosions==1,"retired projectile cannot detonate twice");
 reset_fixture();ball();cast_result=1;tick_fireballs(100,16,true);tick_fireballs(500,16,true);
 check(!exists(50)&&show.fireballs[0].probe&&explosions==0,"stale cast retires object but preserves handle to drain");
 cast_result=2;cast_hit=1;tick_fireballs(516,16,true);check(!show.fireballs[0].probe&&explosions==0,"late hit cannot damage after timeout");
 reset_fixture();ball();tick_fireballs(6101,16,true);check(explosions==0&&!exists(50),"TTL expires without target explosion");
 reset_fixture();ball();world[50].model=99;tick_fireballs(116,16,true);check(exists(50),"recycled handle cannot delete foreign model");
 reset_fixture();ball();delete_failure=true;tick_fireballs(116,16,false);check(show.fireballs[0].entity==50,"failed deletion must preserve ownership");
 delete_failure=false;tick_fireballs(132,16,false);check(!exists(50),"cleanup retry removes owned object");
 reset_fixture();
 for(int id=60;id<63;id++){world[id]={hash("taxi"),{float(id-60),32,0},{},false,true,{}};nearby_vehicles[nearby_vehicle_count++].entity=id;}
 world[61].mission=true;world[62].seats[-1]=1;
 auto& a=actors[0];a.spec=&ergt::creatures[1];a.combat.reset(a.spec);
 gather_traffic(a,1,100);lift_traffic(a,1,116);
 check(show.traffic[0].entity==60&&!show.traffic[1].entity,"gravity excludes mission and occupied player cars");
 check(ergt::length(world[60].velocity)>0&&ergt::length(world[61].velocity)==0&&ergt::length(world[62].velocity)==0,"only selected traffic receives lift velocity");
 show.aim={40,20,5};throw_traffic(a,1);check(!show.traffic[0].entity&&world[60].velocity.x>0,"released car flies ballistically with no continuing steering");
 clear_showcase();check(exists(60)&&exists(61)&&exists(62),"cleanup never deletes ambient traffic");
 reset_fixture();
 auto& caster=actors[0];caster.spec=&ergt::creatures[1];caster.combat.reset(caster.spec);
 const ergt::MotionSample poses[2]={{{},0,{0,0,2},{0,4,2}},{{},0,{0,0,2},{0,4,2}}};
 const ergt::ContactWindow contacts[1]={{.4f,.5f}};
 const ergt::MotionTrack track={"fixture","attack",3.f,poses,2,true,false,contacts,1};
 caster.motion=&track;caster.animation_accepted=true;caster.active_clip=caster.spec->attack_clip;caster.animation_started=100;
 caster.target=1;caster.combat.tick(16,{{0,30,0},{0,0,0},true,true,true,false});show.city=false;
 world[60]={hash("taxi"),{0,32,0},{},false,true,{}};nearby_vehicle_count=1;nearby_vehicles[0].entity=60;
 animation_phase=.30f;tick_showcase_actor(caster,1,100,16);
 check(show.traffic[0].entity==60,"real adapter arms gravity from the active source attack");
 animation_phase=.35f;tick_showcase_actor(caster,1,116,16);
 check(show.traffic[0].entity==60,"timer/frame progression before source cue cannot release");
 animation_phase=.41f;tick_showcase_actor(caster,1,132,16);
 check(!show.traffic[0].entity&&std::count(events.begin(),events.end(),"gravity_release_source_cue")==1,"production adapter releases on observed contact crossing");
 animation_phase=.43f;tick_showcase_actor(caster,1,148,16);
 check(std::count(events.begin(),events.end(),"gravity_release_source_cue")==1,"production adapter prevents duplicate source releases");
 reset_fixture();show.responders[0].vehicle=60;show.responders[0].car_model=hash("police");world[60]={hash("police"),{},{},true,true,{{-1,1}}};
 clear_responders();check(exists(60)&&!world[60].mission&&show.responders[0].vehicle==0,"reset preserves owner-occupied police vehicle");
 reset_fixture();tick_city(actors[0],1,7000);check(spawned==1&&calls[0x158BB33F920D360CULL]==1,"city creates bounded police unit and native approach task");
 tick_city(actors[0],1,33000);check(spawned==3,"SWAT and helicopter are bounded reinforcements");
 tick_city(actors[0],1,36000);check(calls[0xDAD029E187A2BEB4ULL]>0&&calls[0x08DA95E8298AE772ULL]>0,"pilot and shooters receive real native tasks");
 const auto before=actors[0].combat.health();tick_city(actors[0],1,39000);check(actors[0].combat.health()==before&&spawned==3,"city AI does not synthesize boss damage or endless respawns");
 fighting=false;tick_city(actors[0],1,40000);check(show.responders[0].vehicle==0&&world.size()==2,"pause clears only owned responders");
 reset_fixture();show.view=1;show.camera_until=30000;tick_film(1,100);tick_film(1,116);check(show.camera==800,"camera requires a resolved placement cast");
 input_pressed=true;tick_film(1,132);check(!show.camera&&!show.view,"movement restores gameplay camera immediately");
 reset_fixture();remember_boss_spawn(2,{0,80,0},45);request_encounter_reset(100);check(show.reset_pending&&selected==2,"reset keeps original encounter identity");
 tick_encounter_reset(116);check(pending.active&&pending.use_anchor&&pending.anchor.y==80&&pending.heading==45,"reset retains original arena anchor without teleporting player");
 puts("Production spectacle adapter lifecycle fixtures passed; no game launched");
}
'''
with tempfile.TemporaryDirectory(prefix='ergt-spectacle-') as directory:
    p = Path(directory)
    (p / 'test.cpp').write_text(fixture + actor + globals_)
    subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-I', str(root / 'src'),
                    str(p / 'test.cpp'), '-o', str(p / 'test')], check=True)
    subprocess.run([str(p / 'test')], check=True)
