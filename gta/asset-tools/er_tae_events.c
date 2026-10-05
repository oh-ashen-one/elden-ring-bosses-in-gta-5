/* SPDX-License-Identifier: GPL-3.0-or-later
 * Read selected owned animation events. No game execution or writes.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "souls_formats/sf_bnd4.h"
#include "souls_formats/sf_tae.h"
int wmain(int argc,wchar_t **argv){
    if(argc!=3)return 2;
    long long id=_wtoi64(argv[2]);sf_bnd4_t *b=NULL;
    sf_result_t r=sf_bnd4_read_from_path(&b,argv[1],NULL);if(r!=SF_OK)return 3;
    for(size_t i=0;i<sf_bnd4_file_count(b);i++){
        const sf_binder_file_t *f=sf_bnd4_get_file(b,i);
        if(!strstr(f->name_utf8,".tae"))continue;
        sf_tae_t *tae=NULL;r=sf_tae_read_from_memory(&tae,f->data,f->size,NULL);if(r!=SF_OK){fprintf(stderr,"TAE: %s\n",sf_result_str(r));return 4;}
        for(size_t j=0;j<sf_tae_animation_count(tae);j++){
            const sf_tae_animation_t *a=sf_tae_animation(tae,j);if(sf_tae_animation_id(a)!=id)continue;
            printf("{\"animation\":%lld,\"bank\":%lld,\"events\":[",id,(long long)sf_tae_event_bank(tae));
            for(size_t k=0;k<sf_tae_animation_event_count(a);k++){
                const sf_tae_event_t *e=sf_tae_animation_event(a,k);
                printf("%s{\"type\":%d,\"start\":%.9g,\"end\":%.9g}",k?",":"",sf_tae_event_type(e),sf_tae_event_start_time(e),sf_tae_event_end_time(e));
            }
            puts("]}");
        }
        sf_tae_destroy(tae);
    }
    sf_bnd4_destroy(b);return 0;
}
