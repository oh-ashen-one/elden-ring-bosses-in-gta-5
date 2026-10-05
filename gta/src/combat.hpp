#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace ergt {
struct Vec3 { float x = 0, y = 0, z = 0; };
inline bool finite_vec(Vec3 p) { return std::isfinite(p.x) && std::isfinite(p.y) && std::isfinite(p.z); }
inline float horizontal_distance(Vec3 a, Vec3 b) {
    return std::hypot(a.x - b.x, a.y - b.y);
}

// Contact alone must not drain health. Only a new moving-vehicle impact counts.
inline float impact_damage(float speed) {
    if (!std::isfinite(speed) || speed < 2.5f) return 0;
    return std::clamp(speed * speed * 2.4f, 25.0f, 1400.0f);
}

// The imported rigs face model -Y (feet/head/claws inspected in animated
// source poses). GTA heading zero faces +Y, so apply the model-space offset.
inline float heading_to_target(Vec3 actor, Vec3 target, float model_offset) {
    float heading=std::atan2(actor.x-target.x,target.y-actor.y)*57.2957795f+model_offset;
    return std::fmod(heading+360.0f,360.0f);
}

inline float target_score(float distance, bool current, bool attacker) {
    return distance * (current ? 0.72f : 1.0f) * (attacker ? 0.35f : 1.0f);
}

struct CreatureSpec {
    const char* label;
    const char* model;
    const char* dictionary;
    const char* idle_clip;
    const char* move_clip;
    const char* attack_clip;
    const char* death_clip;
    float maximum_health;
    float speed;
    float melee_range;
    int melee_damage;
    int windup_ms;
    int recovery_ms;
    int attack_clip_ms;
    float minimum_z;
    float model_heading_offset = 180.0f;
    const char* stagger_clip = nullptr;
    int stagger_ms = 500;
    bool ranged_enabled = true;
    float body_radius=.5f,body_height=2.8f,vertical_reach=4.0f,weapon_radius=.12f;
    const char* visual_child=nullptr;
};

// Hit timers now follow inspected source attack-motion landmarks. Contact
// timing, clip roles and GTA playback still require owner gameplay review.
inline constexpr std::array<CreatureSpec, 4> creatures{{
    {"Malenia", "ergt_malenia", "ergt_malenia_anims", "a000_000020", "a000_002100", "a000_003000", "a000_010000",
     3600, 3.2f, 6.0f, 28, 1150, 1500, 2734, -0.005f,180.0f,"a000_008030",1334,false},
    {"Starscourge Radahn", "ergt_radahn", "ergt_radahn_anims", "a000_000020", "a000_002100", "a000_003000", "a000_010000",
     6500,5.2f,9.0f,45,1833,2200,3934,-.04f,180.0f,"a000_008140",1234,false,2.5f,10.3f,12.0f,.45f},
    {"Fire Giant", "ergt_firegiant", "ergt_firegiant_anims", "a000_000020", "a000_002100", "a000_003000", "a000_010000",
     14000,4.0f,46.8f,65,2833,3700,6667,-.598f,180.0f,"a000_008700",7000,false,10.4f,59.8f,67.6f,5.72f,"ergt_firegiant_part1"},
    {"Godfrey, First Elden Lord", "ergt_godfrey", "ergt_godfrey_anims", "a000_000020", "a000_002100", "a000_003000", "a000_010000",
     5000,3.8f,5.5f,38,1100,1600,3834,-.04f,180.0f,"a000_008700",5334,false,.9f,6.5f,8.0f,.55f},
}};

enum class CombatState { idle, chasing, melee_windup, ranged_windup, recovering, staggered, defeated };
enum class AnimationIntent { keep, idle, move, attack, stagger, death };
inline AnimationIntent animation_intent(CombatState state) {
    switch(state) {
    case CombatState::chasing: return AnimationIntent::move;
    case CombatState::melee_windup:
    case CombatState::ranged_windup: return AnimationIntent::attack;
    case CombatState::recovering: return AnimationIntent::keep;
    case CombatState::defeated: return AnimationIntent::death;
    case CombatState::staggered: return AnimationIntent::stagger;
    default: return AnimationIntent::idle;
    }
}
struct Observation {
    Vec3 actor;
    Vec3 target;
    bool target_alive = true;
    bool line_of_sight = true;
    bool combat_enabled = false;
    bool airborne_target = false;
};
struct Decision {
    Vec3 movement;
    bool melee_strike = false;
    bool ranged_strike = false;
    bool telegraph = false;
    Vec3 aim;
};

class Combat {
public:
    Combat() : Combat(&creatures[0]) {}
    explicit Combat(const CreatureSpec* spec) : spec_(spec), health_(spec->maximum_health) {}
    void reset(const CreatureSpec* spec) { *this = Combat(spec); }
    float health() const { return health_; }
    float ratio() const { return std::clamp(health_ / spec_->maximum_health, 0.0f, 1.0f); }
    bool enraged() const { return ratio() <= 0.5f; }
    CombatState state() const { return state_; }
    unsigned reaction_generation() const { return reaction_generation_; }
    void cancel_attack() {
        if (state_ != CombatState::defeated && state_ != CombatState::staggered) {
            state_ = CombatState::idle; remaining_ms_ = 0;
        }
    }

    void damage(float value) {
        if (!std::isfinite(value) || value <= 0 || state_ == CombatState::defeated) return;
        health_ = std::max(0.0f, health_ - value);
        if (health_ == 0) { state_ = CombatState::defeated; remaining_ms_ = 0; }
        else if (value >= 250) { state_ = CombatState::staggered; remaining_ms_ = spec_->stagger_ms; ++reaction_generation_; }
    }

    Decision tick(int elapsed_ms, const Observation& observation) {
        Decision out{};
        if (state_ == CombatState::defeated) return out;
        const int dt = std::clamp(elapsed_ms, 0, 250);
        if (dt == 0) return out;
        if (remaining_ms_ > 0) remaining_ms_ = std::max(0, remaining_ms_ - dt);
        // Physical hit reactions continue even with aggression paused or no
        // target. Pausing cancels attacks, not the source stagger animation.
        if(state_==CombatState::staggered){
            if(remaining_ms_>0)return out;
            state_=CombatState::idle;
        }
        if (!observation.target_alive || !observation.combat_enabled || !finite_vec(observation.actor) || !finite_vec(observation.target)) {
            state_ = CombatState::idle; remaining_ms_ = 0; return out;
        }
        if (state_ == CombatState::ranged_windup) {
            out.aim = locked_target_; out.telegraph = remaining_ms_ > 0;
            if (remaining_ms_ == 0) {
                out.ranged_strike = observation.line_of_sight;
                state_ = CombatState::recovering; remaining_ms_ = std::max(2200, spec_->attack_clip_ms - 1500);
            }
            return out;
        }
        if (state_ == CombatState::melee_windup) {
            if (remaining_ms_ == 0) {
                out.melee_strike = observation.line_of_sight &&
                    horizontal_distance(observation.actor, observation.target) <= spec_->melee_range + 0.5f &&
                    std::abs(observation.actor.z - observation.target.z) < spec_->vertical_reach;
                state_ = CombatState::recovering;
                // Let the native one-shot reach its end before another attack
                // replaces it. Windup marks the hit, not the clip's endpoint.
                remaining_ms_ = std::max(spec_->attack_clip_ms - spec_->windup_ms,
                    enraged() ? spec_->recovery_ms * 3 / 4 : spec_->recovery_ms);
            }
            return out;
        }
        if (state_ == CombatState::recovering || state_ == CombatState::staggered) {
            if (remaining_ms_ > 0) return out;
            state_ = CombatState::idle;
        }
        const float distance = horizontal_distance(observation.actor, observation.target);
        if (!observation.line_of_sight || distance > 200.0f) { state_ = CombatState::idle; return out; }
        if (spec_->ranged_enabled && (observation.airborne_target || std::abs(observation.actor.z - observation.target.z) > 6.0f || distance > 28.0f)) {
            locked_target_ = observation.target;
            state_ = CombatState::ranged_windup; remaining_ms_ = 1500;
            out.telegraph = true; out.aim = locked_target_;
        } else if (distance <= spec_->melee_range && std::abs(observation.actor.z-observation.target.z)<spec_->vertical_reach) {
            state_ = CombatState::melee_windup; remaining_ms_ = spec_->windup_ms;
        } else {
            state_ = CombatState::chasing;
            const float speed = spec_->speed * (enraged() ? 1.25f : 1.0f);
            if(distance<=spec_->melee_range){state_=CombatState::idle;return out;}
            const float step = std::min(speed * dt / 1000.0f, distance - spec_->melee_range);
            out.movement = {(observation.target.x - observation.actor.x) / distance * step,
                            (observation.target.y - observation.actor.y) / distance * step, 0};
        }
        return out;
    }

private:
    const CreatureSpec* spec_;
    float health_;
    CombatState state_ = CombatState::idle;
    int remaining_ms_ = 0;
    Vec3 locked_target_{};
    unsigned reaction_generation_ = 0;
};
} // namespace ergt
