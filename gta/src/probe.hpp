#pragma once

#include <algorithm>
#include <cstdint>

namespace ergt {
enum class ProbeState { idle, alive, dead, missing };

struct DamageSample {
    int lost_health = 0;
    bool died = false;
    bool disappeared = false;
};

// Observes the GTA actor's real health. It never manufactures damage or heals it.
class Probe {
public:
    void start(int actor, int health) {
        reset();
        if (actor == 0 || health <= 0) return;
        actor_ = actor;
        initial_health_ = previous_health_ = health;
        state_ = ProbeState::alive;
    }

    DamageSample observe(bool exists, int health, bool dead) {
        if (state_ != ProbeState::alive) return {};
        if (!exists) {
            state_ = ProbeState::missing;
            actor_ = 0;
            return {0, false, true};
        }
        health = std::max(0, health);
        const int loss = std::max(0, previous_health_ - health);
        previous_health_ = health;
        total_loss_ += static_cast<std::uint64_t>(loss);
        if (dead) state_ = ProbeState::dead;
        return {loss, dead, false};
    }

    void reset() { *this = Probe{}; }
    int actor() const { return actor_; }
    int health() const { return previous_health_; }
    int initial_health() const { return initial_health_; }
    std::uint64_t total_loss() const { return total_loss_; }
    ProbeState state() const { return state_; }
    float ratio() const {
        if (initial_health_ <= 0 || state_ != ProbeState::alive) return 0.0f;
        return std::clamp(static_cast<float>(previous_health_) /
                          static_cast<float>(initial_health_), 0.0f, 1.0f);
    }

private:
    int actor_ = 0;
    int initial_health_ = 0;
    int previous_health_ = 0;
    std::uint64_t total_loss_ = 0;
    ProbeState state_ = ProbeState::idle;
};
} // namespace ergt
