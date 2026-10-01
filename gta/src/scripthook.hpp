#pragma once

#include <windows.h>
#include <cstring>
#include <type_traits>
#include "native_bits.hpp"

namespace ergt {
using KeyboardHandler = void (*)(DWORD, WORD, BYTE, BOOL, BOOL, BOOL, BOOL);

// Original interoperability wrapper. No SDK header, library or vendor binary
// is distributed here. Export names are verified against the official runtime.
struct ScriptHook {
    void (*register_script)(HMODULE, void (*)()) = nullptr;
    void (*unregister_script)(HMODULE) = nullptr;
    void (*register_keyboard)(KeyboardHandler) = nullptr;
    void (*unregister_keyboard)(KeyboardHandler) = nullptr;
    void (*wait)(DWORD) = nullptr;
    void (*init)(std::uint64_t) = nullptr;
    void (*push)(std::uint64_t) = nullptr;
    std::uint64_t* (*call)() = nullptr;
    int (*get_all_peds)(int*, int) = nullptr;
    int (*get_all_vehicles)(int*, int) = nullptr;

    template<class T> static bool resolve(HMODULE dll, const char* name, T& out) {
        const FARPROC address = GetProcAddress(dll, name);
        static_assert(sizeof(out) == sizeof(address));
        std::memcpy(&out, &address, sizeof(out));
        return out != nullptr;
    }

    bool bind() {
        // Do not search arbitrary directories or load a second runtime.
        const HMODULE dll = GetModuleHandleW(L"ScriptHookV.dll");
        if (!dll) return false;
        // Optional SDK pool enumerators; unavailable exports leave the player
        // path working. Never read undocumented game pool memory.
        resolve(dll, "?worldGetAllPeds@@YAHPEAHH@Z", get_all_peds);
        resolve(dll, "?worldGetAllVehicles@@YAHPEAHH@Z", get_all_vehicles);
        return resolve(dll, "?scriptRegister@@YAXPEAUHINSTANCE__@@P6AXXZ@Z", register_script)
            && resolve(dll, "?scriptUnregister@@YAXPEAUHINSTANCE__@@@Z", unregister_script)
            && resolve(dll, "?keyboardHandlerRegister@@YAXP6AXKGEHHHH@Z@Z", register_keyboard)
            && resolve(dll, "?keyboardHandlerUnregister@@YAXP6AXKGEHHHH@Z@Z", unregister_keyboard)
            && resolve(dll, "?scriptWait@@YAXK@Z", wait)
            && resolve(dll, "?nativeInit@@YAX_K@Z", init)
            && resolve(dll, "?nativePush64@@YAX_K@Z", push)
            && resolve(dll, "?nativeCall@@YAPEA_KXZ", call);
    }

    template<class R = void, class... Args> R invoke(std::uint64_t hash, Args... args) {
        init(hash);
        (push(native_bits(args)), ...);
        auto* result = call();
        if constexpr (!std::is_void_v<R>) {
            static_assert(std::is_trivially_copyable_v<R>);
            R value{};
            std::memcpy(&value, result, sizeof(value));
            return value;
        }
    }
};
} // namespace ergt
