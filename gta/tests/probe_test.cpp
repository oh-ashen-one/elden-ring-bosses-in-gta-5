#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include "probe.hpp"
#include "native_bits.hpp"

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

int main() {
    using namespace ergt;
    Probe p;
    require(p.observe(true, 3000, false).lost_health == 0, "idle cannot invent damage");
    p.start(42, 5000);
    require(p.ratio() == 1.0f, "spawn records initial native health");
    require(p.observe(true, 4800, false).lost_health == 200, "native health loss captured");
    require(p.observe(true, 4800, false).lost_health == 0, "unchanged sample is not duplicate damage");
    require(p.observe(true, 4900, false).lost_health == 0, "healing is not negative damage");
    require(p.observe(true, 4000, false).lost_health == 900, "loss follows updated native health");
    const auto death = p.observe(true, 100, true);
    require(death.died && death.lost_health == 3900, "native death takes precedence over nonzero health");
    require(p.ratio() == 0.0f, "dead actor bar is empty");
    require(!p.observe(true, 0, true).died, "death emitted once");
    p.start(51, 2000);
    require(p.total_loss() == 0, "restart removes prior encounter damage");
    require(p.observe(false, 0, false).disappeared, "despawn distinguished from kill");
    require(p.actor() == 0 && p.total_loss() == 0, "lost handle cannot retain actor or count a kill");
    p.start(0, 5000);
    require(p.state() == ProbeState::idle, "invalid spawn remains idle");
    p.start(99, 100);
    require(p.observe(true, -10, true).lost_health == 100, "negative engine health clamps at zero");
    p.reset();
    require(p.actor() == 0 && p.ratio() == 0.0f, "reset clears state");
    require(native_bits(1.0f) == 0x3f800000ULL, "float native argument is not numeric conversion");
    require(native_bits(-1) == std::numeric_limits<std::uint64_t>::max(), "signed argument preserves bits");
    int marker = 7;
    require(native_bits(&marker) == reinterpret_cast<std::uintptr_t>(&marker), "native pointer argument preserved");
    std::cout << "Probe and native-ABI checks passed (no GTA gameplay executed)\n";
}
