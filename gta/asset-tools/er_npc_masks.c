/* SPDX-License-Identifier: GPL-3.0-or-later
 * Read only the owned game's NPC display masks; no game/registry mutation.
 * Keys remain inside the separately obtained format library, never in output.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "souls_formats/sf_regulation.h"
#include "souls_formats/sf_dcx.h"
#include "souls_formats/sf_oodle.h"
#include "souls_formats/sf_bnd4.h"
#include "souls_formats/sf_param.h"
#include "souls_formats/sf_paramdef.h"

int wmain(int argc,wchar_t **argv) {
    if(argc!=4)return 2;
    FILE *f=_wfopen(argv[1],L"rb");if(!f)return 3;
    fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);
    if(n<16 || n>256*1024*1024){fclose(f);return 3;}
    unsigned char *bytes=malloc((size_t)n),*plain=NULL;size_t size=0;
    if(!bytes || fread(bytes,1,(size_t)n,f)!=(size_t)n){fclose(f);return 3;}fclose(f);
    sf_result_t r=sf_regulation_decrypt_er(bytes,(size_t)n,&plain,&size,NULL);free(bytes);
    if(r!=SF_OK){fprintf(stderr,"Regulation read: %s\n",sf_result_str(r));return 4;}
    sf_oodle_set_search_path(argv[3]);
    sf_bnd4_t *b=NULL;
    if(size>4 && !memcmp(plain,"DCX",3)) {
        unsigned char *unpacked=NULL;size_t unpacked_size=0;
        r=sf_dcx_decompress_from_buffer(plain,size,&unpacked,&unpacked_size,NULL,NULL);
        if(r!=SF_OK)return 5;
        free(plain);plain=unpacked;size=unpacked_size;
    }
    r=sf_bnd4_read_from_memory(&b,plain,size,NULL);free(plain);
    if(r!=SF_OK){fprintf(stderr,"Binder read: %s\n",sf_result_str(r));return 6;}
    sf_paramdef_t *def=NULL;r=sf_paramdef_read_xml_from_path(&def,argv[2],NULL);
    if(r!=SF_OK){fprintf(stderr,"Paramdef: %s\n",sf_result_str(r));return 7;}
    for(size_t i=0;i<sf_bnd4_file_count(b);i++) {
        const sf_binder_file_t *entry=sf_bnd4_get_file(b,i);
        if(!strstr(entry->name_utf8,"NpcParam.param"))continue;
        sf_param_t *param=NULL;r=sf_param_read_from_memory(&param,entry->data,entry->size,NULL);
        if(r!=SF_OK)return 8;
        r=sf_param_apply_paramdef(param,def,SF_PARAM_APPLY_UNCONDITIONAL);
        if(r!=SF_OK){fprintf(stderr,"Apply definition: %s\n",sf_result_str(r));return 9;}
        for(size_t j=0;j<sf_param_get_row_count(param);j++) {
            const sf_param_row_t *row=sf_param_get_row(param,j);long long id=sf_param_row_get_id(row);
            int character=(int)(id/10000);
            if(character!=2120&&character!=4720&&character!=4730&&character!=4760)continue;
            printf("%lld masks",id);
            for(int bit=0;bit<32;bit++) {
                char name[32];snprintf(name,sizeof(name),"modelDispMask%d",bit);
                const sf_param_cell_t *cell=sf_param_row_find_cell(row,name);
                if(!cell || sf_param_cell_get_value(cell).kind!=SF_PARAM_CELL_KIND_U8)return 10;
                if(sf_param_cell_get_u8(cell))printf(" %d",bit);
            }
            puts("");
        }
        sf_param_destroy(param);
    }
    sf_paramdef_destroy(def);sf_bnd4_destroy(b);return 0;
}
