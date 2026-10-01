#pragma once

#include <cstdint>
#include <cstring>
#include <type_traits>

namespace ergt {
// Script Hook V's x64 native ABI uses one 64-bit slot per scalar argument.
// Floats occupy the low 32 bits; Vector3 returns have an 8-byte stride.
struct NativeVector {
    float x; std::uint32_t pad_x;
    float y; std::uint32_t pad_y;
    float z; std::uint32_t pad_z;
};
static_assert(sizeof(NativeVector) == 24);

template<class T> std::uint64_t native_bits(T value) {
    if constexpr (std::is_pointer_v<T>) {
        return reinterpret_cast<std::uintptr_t>(value);
    } else if constexpr (std::is_same_v<T, float>) {
        std::uint32_t bits = 0;
        std::memcpy(&bits, &value, sizeof(value));
        return bits;
    } else {
        static_assert(std::is_integral_v<T>, "native arguments must be explicit scalar types");
        return static_cast<std::uint64_t>(value);
    }
}
} // namespace ergt
