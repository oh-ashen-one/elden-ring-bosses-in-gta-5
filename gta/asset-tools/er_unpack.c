/* SPDX-License-Identifier: GPL-3.0-or-later
 * Original standalone texture/material adapter for souls-formats-c.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <io.h>
#include <fcntl.h>
#include "souls_formats/sf_bnd4.h"
#include "souls_formats/sf_tpf.h"
#include "souls_formats/sf_matbin.h"

static FILE *new_file(const wchar_t *path) {
    HANDLE h = CreateFileW(path, GENERIC_WRITE, 0, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h == INVALID_HANDLE_VALUE) return NULL;
    int fd = _open_osfhandle((intptr_t)h, _O_WRONLY | _O_BINARY);
    if (fd < 0) { CloseHandle(h); return NULL; }
    return _fdopen(fd, "wb");
}

static void json_string(FILE *out, const char *s) {
    fputc('"', out);
    if (s) for (const unsigned char *p = (const unsigned char *)s; *p; ++p) {
        if (*p == '"' || *p == '\\') { fputc('\\', out); fputc(*p, out); }
        else if (*p < 32) fprintf(out, "\\u%04x", *p);
        else fputc(*p, out);
    }
    fputc('"', out);
}

int wmain(int argc, wchar_t **argv) {
    if (argc != 4 || (wcscmp(argv[1], L"--textures") && wcscmp(argv[1], L"--materials"))) {
        fprintf(stderr, "Usage: er-unpack --textures|--materials INPUT_BINDER NEW_OUTPUT_DIR_OR_JSON\n");
        return 2;
    }
    const size_t path_len = wcslen(argv[2]);
    const int direct_tpf = !wcscmp(argv[1], L"--textures") && path_len >= 4 && !_wcsicmp(argv[2] + path_len - 4, L".tpf");
    sf_bnd4_t *binder = NULL;
    sf_result_t r = direct_tpf ? SF_OK : sf_bnd4_read_from_path(&binder, argv[2], NULL);
    if (r != SF_OK) { fprintf(stderr, "Read binder: %s\n", sf_result_str(r)); return 3; }
    size_t count = 0;
    if (!wcscmp(argv[1], L"--textures")) {
        for (size_t i = 0; i < (direct_tpf ? 1 : sf_bnd4_file_count(binder)); ++i) {
            const sf_binder_file_t *entry = direct_tpf ? NULL : sf_bnd4_get_file(binder, i);
            if (entry && (entry->size < 4 || memcmp(entry->data, "TPF\0", 4))) continue;
            sf_tpf_t *tpf = NULL;
            r = direct_tpf ? sf_tpf_read_from_path(&tpf, argv[2], NULL)
                           : sf_tpf_read_from_memory(&tpf, entry->data, entry->size, NULL);
            if (r != SF_OK) { fprintf(stderr, "Read TPF: %s\n", sf_result_str(r)); return 4; }
            for (size_t j = 0; j < sf_tpf_texture_count(tpf); ++j) {
                const sf_tpf_texture_t *texture = sf_tpf_get_texture(tpf, j);
                const char *name = sf_tpf_texture_get_name(texture);
                if (!name || strstr(name, "..") || strpbrk(name, "/\\:")) return 5;
                wchar_t filename[1024], path[32768];
                if (!MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, name, -1, filename, 1024)) return 5;
                if (wcslen(argv[3]) + wcslen(filename) + 7 >= 32768) return 5;
                swprintf(path, 32768, L"%ls\\%ls.dds", argv[3], filename);
                size_t size = 0;
                const uint8_t *bytes = sf_tpf_texture_get_bytes(texture, &size);
                if (size < 4 || memcmp(bytes, "DDS ", 4)) return 6;
                FILE *file = new_file(path);
                if (!file) { fprintf(stderr, "Cannot create new texture output\n"); return 7; }
                const size_t written = fwrite(bytes, 1, size, file);
                const int closed = fclose(file);
                if (written != size || closed) return 8;
                ++count;
            }
            sf_tpf_destroy(tpf);
        }
        printf("Unpacked %zu DDS textures\n", count);
    } else {
        FILE *out = new_file(argv[3]);
        if (!out) { fprintf(stderr, "Refusing existing material output\n"); return 7; }
        fputs("{\n", out);
        for (size_t i = 0; i < sf_bnd4_file_count(binder); ++i) {
            const sf_binder_file_t *entry = sf_bnd4_get_file(binder, i);
            if (entry->size < 4 || memcmp(entry->data, "MAB\0", 4)) continue;
            sf_matbin_t *material = NULL;
            r = sf_matbin_read_from_memory(&material, entry->data, entry->size, NULL);
            if (r != SF_OK) { fprintf(stderr, "Material parse: %s\n", sf_result_str(r)); return 4; }
            if (count++) fputs(",\n", out);
            json_string(out, entry->name_utf8);
            fputs(":{\"source\":", out); json_string(out, sf_matbin_source_path(material));
            fputs(",\"shader\":", out); json_string(out, sf_matbin_shader_path(material));
            fputs(",\"samplers\":[", out);
            for (size_t j = 0; j < sf_matbin_sampler_count(material); ++j) {
                const sf_matbin_sampler_t *sampler = sf_matbin_sampler(material, j);
                if (j) fputc(',', out);
                fputs("{\"type\":", out); json_string(out, sf_matbin_sampler_type(sampler));
                fputs(",\"path\":", out); json_string(out, sf_matbin_sampler_path(sampler));
                fputc('}', out);
            }
            fputs("],\"params\":[", out);
            for (size_t j = 0; j < sf_matbin_param_count(material); ++j) {
                const sf_matbin_param_t *p = sf_matbin_param(material, j);
                const sf_matbin_param_type_t type = sf_matbin_param_type(p);
                float values[5] = {0}; int n = 0; int32_t ints[2] = {0}; bool boolean = false;
                switch (type) {
                    case SF_MATBIN_PARAM_TYPE_BOOL: sf_matbin_param_value_bool(p, &boolean); values[0] = boolean ? 1 : 0; n=1; break;
                    case SF_MATBIN_PARAM_TYPE_INT: sf_matbin_param_value_int(p, ints); values[0]=(float)ints[0]; n=1; break;
                    case SF_MATBIN_PARAM_TYPE_INT2: sf_matbin_param_value_int2(p, ints); values[0]=(float)ints[0]; values[1]=(float)ints[1]; n=2; break;
                    case SF_MATBIN_PARAM_TYPE_FLOAT: sf_matbin_param_value_float(p, values); n=1; break;
                    case SF_MATBIN_PARAM_TYPE_FLOAT2: sf_matbin_param_value_float2(p, values); n=2; break;
                    case SF_MATBIN_PARAM_TYPE_FLOAT3: sf_matbin_param_value_float3(p, values); n=3; break;
                    case SF_MATBIN_PARAM_TYPE_FLOAT4: sf_matbin_param_value_float4(p, values); n=4; break;
                    case SF_MATBIN_PARAM_TYPE_FLOAT5: sf_matbin_param_value_float5(p, values); n=5; break;
                    default: return 10;
                }
                if (j) fputc(',', out);
                fputs("{\"name\":", out); json_string(out, sf_matbin_param_name(p));
                fprintf(out, ",\"type\":%d,\"value\":[", (int)type);
                for (int k=0;k<n;++k) { if(k) fputc(',',out); fprintf(out,"%.9g",values[k]); }
                fputs("]}",out);
            }
            fputs("]}", out);
            sf_matbin_destroy(material);
        }
        fputs("\n}\n", out);
        if (fclose(out)) return 8;
        printf("Indexed %zu materials\n", count);
    }
    sf_bnd4_destroy(binder);
    return count ? 0 : 9;
}
