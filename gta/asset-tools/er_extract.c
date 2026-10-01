/* SPDX-License-Identifier: GPL-3.0-or-later
 * Original standalone adapter linked to souls-formats-c (GPL-3.0-or-later).
 * Reads owned game archives; creates one NEW, decompressed output file.
 * This executable is separate from the Apache-licensed GTA gameplay plugin.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "souls_formats/sf_bhd5.h"
#include "souls_formats/sf_common.h"
#include "souls_formats/sf_io.h"
#include "souls_formats/sf_dcx.h"
#include "souls_formats/sf_oodle.h"

static char *read_key(const wchar_t *path) {
    FILE *f = _wfopen(path, L"rb");
    if (!f) return NULL;
    char *key = calloc(1, 16385);
    if (!key) { fclose(f); return NULL; }
    size_t n = fread(key, 1, 16384, f);
    const int too_long = fgetc(f) != EOF;
    fclose(f);
    if (!n || too_long) { free(key); return NULL; }
    return key;
}

int wmain(int argc, wchar_t **argv) {
    if (argc != 7) {
        fprintf(stderr, "Usage: er-extract BHD BDT PUBLIC_ASSET_KEY ARCHIVE_PATH NEW_OUTPUT OODLE_DIR\n");
        return 2;
    }
    if (GetFileAttributesW(argv[5]) != INVALID_FILE_ATTRIBUTES) {
        fprintf(stderr, "Refusing to overwrite output\n"); return 2;
    }
    char archive_path[4096];
    if (!WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, argv[4], -1,
                             archive_path, sizeof(archive_path), NULL, NULL)) return 2;
    char *key = read_key(argv[3]);
    if (!key) { fprintf(stderr, "Cannot read public archive key\n"); return 2; }
    sf_bhd5_t *archive = NULL;
    sf_result_t r = sf_bhd5_open_with_key(&archive, argv[1], argv[2],
                                         SF_BHD5_GAME_ELDENRING, key, NULL);
    free(key);
    if (r != SF_OK) { fprintf(stderr, "Open archive: %s\n", sf_result_str(r)); return 3; }
    void *data = NULL;
    size_t size = 0;
    /* Elden Ring BHD5 uses a full 64-bit polynomial hash with multiplier 0x85.
     * The pinned C library's generic helper currently widens a 32-bit hash;
     * call its explicit 64-bit lookup with the verified archive hash instead. */
    uint64_t path_hash = 0;
    for (const unsigned char *c = (const unsigned char *)archive_path; *c; ++c) {
        unsigned char v = *c;
        if (v >= 'A' && v <= 'Z') v = (unsigned char)(v + ('a' - 'A'));
        if (v == '\\') v = '/';
        path_hash = path_hash * 0x85u + v;
    }
    r = sf_bhd5_extract_by_hash_64(archive, path_hash, &data, &size, NULL);
    sf_bhd5_close(archive);
    if (r != SF_OK) { fprintf(stderr, "Extract: %s\n", sf_result_str(r)); return 4; }
    if (size >= 4 && memcmp(data, "DCX\0", 4) == 0) {
        r = sf_oodle_set_search_path(argv[6]);
        void *decoded = NULL;
        size_t decoded_size = 0;
        if (r == SF_OK) r = sf_dcx_decompress(data, size, &decoded, &decoded_size, NULL, NULL);
        sf_free(NULL, data);
        if (r != SF_OK) { fprintf(stderr, "Decompress: %s\n", sf_result_str(r)); return 5; }
        data = decoded;
        size = decoded_size;
    }
    if (size > 1024ULL * 1024 * 1024) {
        fprintf(stderr, "Output exceeds one-file size limit\n"); sf_free(NULL, data); return 6;
    }
    HANDLE output = CreateFileW(argv[5], GENERIC_WRITE, 0, NULL, CREATE_NEW,
                                 FILE_ATTRIBUTE_NORMAL, NULL);
    if (output == INVALID_HANDLE_VALUE) { sf_free(NULL, data); return 7; }
    DWORD written = 0;
    const BOOL ok = WriteFile(output, data, (DWORD)size, &written, NULL);
    const BOOL flushed = FlushFileBuffers(output);
    CloseHandle(output);
    sf_free(NULL, data);
    if (!ok || !flushed || written != size) { DeleteFileW(argv[5]); return 8; }
    printf("Extracted %zu bytes\n", size);
    return 0;
}
