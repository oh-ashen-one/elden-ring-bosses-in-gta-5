# SPDX-License-Identifier: Apache-2.0
"""Compile the actual cleanup helper against fixture native calls; no game."""
from pathlib import Path
import subprocess
import tempfile
root=Path(__file__).parents[1]
s=(root/'src/encounter_plugin.cpp').read_text();helper=s[s.index('bool prepare_helicopter_spawn()'):s.index('void begin_spawn(')]
fixture=r'''
#include <cstdio>
#include <cstdint>
#include <tuple>
#include <type_traits>
#include <stdexcept>
int owned_helicopter=42;char notice[192]{};
bool live=true,matching=true,driveable=true,delete_ok=true;int deletes=0;
bool exists(int e){return e==42 && live;}
std::uint32_t hash(const char*){return 123;}
void record(const char*,int=0,float=0){}
struct FakeHook {
 template<class R=void,class...A> R invoke(std::uint64_t h,A...args) {
  if constexpr(std::is_void_v<R>) {
   if(h==0xEA386986E786A54FULL) {
    deletes++;
    if(delete_ok) {live=false;auto tuple=std::make_tuple(args...);
     if constexpr(std::is_pointer_v<std::tuple_element_t<0,decltype(tuple)>>)*std::get<0>(tuple)=0;
    }
   }
   return;
  } else return static_cast<R>(h==0x9F47B058362C84B5ULL?(matching?123:999):driveable);
 }
} hook;
void check(bool b){if(!b)throw std::runtime_error("helicopter ownership regression");}
'''
main=r'''
int main(){
 check(!prepare_helicopter_spawn() && deletes==0 && owned_helicopter==42);
 driveable=false;check(prepare_helicopter_spawn() && deletes==1 && owned_helicopter==0 && !live);
 owned_helicopter=42;live=true;matching=false;check(prepare_helicopter_spawn() && deletes==1 && live);
 owned_helicopter=42;live=false;matching=true;check(prepare_helicopter_spawn() && deletes==1);
 owned_helicopter=42;live=true;delete_ok=false;check(!prepare_helicopter_spawn() && owned_helicopter==42 && live);
 puts("Live helicopter preserved; owned wreck replaced; stale/missing handle preserved; failed cleanup blocks duplicate spawn");
}
'''
with tempfile.TemporaryDirectory(prefix='ergt-helicopter-') as temp:
    p=Path(temp);(p/'test.cpp').write_text(fixture+helper+main)
    subprocess.run(['c++','-std=c++17',str(p/'test.cpp'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
