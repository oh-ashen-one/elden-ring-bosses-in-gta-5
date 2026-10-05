# SPDX-License-Identifier: Apache-2.0
"""Exercise actual owned-part cleanup with deletion failures/reused handles."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).parents[1];source=(root/'src/encounter_plugin.cpp').read_text()
actor=source[source.index('struct Actor {'):source.index('std::array<Actor, 1> actors;')]
cleanup=source[source.index('void remove_actor('):source.index('void clear()')]
fixture=r'''
#include <map>
#include <stdexcept>
#include <string>
#include "motion.hpp"
#include "native_bits.hpp"
std::map<int,unsigned> live;bool fail_child=false;int casts=2,deleted=0;
bool exists(int e){return live.count(e)>0;}
unsigned hash(const char* s){return std::string(s)=="ergt_firegiant_part1"?2:1;}
void record(const char*,int=0,float=0){}
struct Hook{template<class R=void,class...A>R invoke(std::uint64_t h,A...args){
 std::array<std::uint64_t,sizeof...(A)> a{ergt::native_bits(args)...};int result=0;
 if(h==0x3D87450E15D98694ULL)result=casts;
 else if(h==0x9F47B058362C84B5ULL)result=live[a[0]];
 else if(h==0x539E0AE3E6634B9FULL){int& e=*reinterpret_cast<int*>(a[0]);if(!(fail_child&&e==11)){live.erase(e);e=0;deleted++;}}
 else throw std::runtime_error("unexpected native");
 if constexpr(!std::is_void_v<R>)return static_cast<R>(result);
}}hook;
void check(bool x){if(!x)throw std::runtime_error("part cleanup regression");}
'''
main=r'''
int main(){
 Actor a;a.entity=10;a.visual_child=11;a.spec=&ergt::creatures[2];live={{10,1},{11,2}};fail_child=true;
 remove_actor(a);check(a.entity==10&&a.visual_child==11&&a.cleanup_failed&&deleted==0);
 fail_child=false;remove_actor(a);check(a.entity==0&&a.visual_child==0&&live.empty()&&deleted==2);
 a.entity=10;a.visual_child=11;a.spec=&ergt::creatures[2];live={{10,1},{11,99}};deleted=0;
 remove_actor(a);check(live.count(11)&&!live.count(10)&&deleted==1);
 a.entity=10;a.visual_child=12;a.spec=&ergt::creatures[2];a.sweep_handles[0]=50;live={{10,1},{12,2}};casts=1;deleted=0;
 remove_actor(a);check(a.entity==10&&a.visual_child==12&&deleted==0);
 casts=2;remove_actor(a);check(live.empty()&&a.entity==0&&deleted==2);
}
'''
with tempfile.TemporaryDirectory(prefix='ergt-part-cleanup-') as d:
 p=Path(d);(p/'t.cpp').write_text(fixture+actor+cleanup+main)
 subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-Werror','-I',str(root/'src'),str(p/'t.cpp'),'-o',str(p/'t')],check=True)
 subprocess.run([str(p/'t')],check=True)
