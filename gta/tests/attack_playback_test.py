# SPDX-License-Identifier: Apache-2.0
"""Compile the actual attack acceptance gate with local native fixtures only."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).parents[1];s=(root/'src/encounter_plugin.cpp').read_text()
helper=s[s.index('bool attack_playback_ready('):s.index('void strike_nearby(')]
fixture=r'''
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <type_traits>
#include <stdexcept>
#include "combat.hpp"
struct Actor{int entity=42;const ergt::CreatureSpec* spec=&ergt::creatures[0];bool animation_accepted=false;const char* active_clip=nullptr;unsigned animation_started=100;};
FILE* log_file=nullptr;int suppressions=0,calls=0;
void record(const char*,int){suppressions++;}
struct Hook{template<class R,class...A>R invoke(std::uint64_t,A...){calls++;return static_cast<R>(0.5);}} hook;
void check(bool b){if(!b)throw std::runtime_error("attack acceptance regression");}
'''
main=r'''
int main(){
 Actor a;ergt::Vec3 pos{1,2,3};
 check(!attack_playback_ready(a,"melee",pos,pos,1000) && calls==0);
 a.animation_accepted=true;a.active_clip=a.spec->idle_clip;
 check(!attack_playback_ready(a,"melee",pos,pos,1000) && calls==0);
 a.active_clip=a.spec->attack_clip;check(attack_playback_ready(a,"melee",pos,pos,1000) && calls==2);
 a.animation_accepted=false;check(!attack_playback_ready(a,"ranged_area",pos,pos,1000) && calls==2);
 check(suppressions==3);puts("Rejected/missing/wrong clips suppress damage; accepted attack samples engine playback telemetry");
}
'''
with tempfile.TemporaryDirectory(prefix='ergt-playback-') as d:
 p=Path(d);(p/'test.cpp').write_text(fixture+helper+main)
 subprocess.run(['c++','-std=c++17','-I',str(root/'src'),str(p/'test.cpp'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
