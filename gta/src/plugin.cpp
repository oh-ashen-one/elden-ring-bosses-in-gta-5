#include <atomic>
#include <cstdio>
#include <cwchar>
#include "scripthook.hpp"
#include "probe.hpp"

// A normal Windows import ensures the runtime is loaded before DllMain.
// The generated import library maps this C symbol to the vendor's C++ export.
extern "C" __declspec(dllimport) int ergt_runtime_dependency();

namespace {
ergt::ScriptHook hook;
ergt::Probe probe;
std::atomic<bool> spawn_requested{false}, clear_requested{false};
HMODULE own_module = nullptr;
bool registered = false;
constexpr std::uint32_t model = 0x1EEA6BD; // a_m_m_skidrow_01, GTA's own test actor
constexpr int maximum_health = 5000;
bool streaming = false;
std::uint32_t stream_started = 0;
const char* status = "F6: spawn GTA test actor | F7: remove";
FILE* log_file = nullptr;

void log_event(const char* event, int amount = 0) {
    if (!log_file) return;
    std::fprintf(log_file, "tick=%llu event=%s actor=%d raw_health=%d amount=%d\n",
                 static_cast<unsigned long long>(GetTickCount64()), event,
                 probe.actor(), probe.health(), amount);
    std::fflush(log_file);
}

void open_log() {
    wchar_t path[32768]{};
    const DWORD n = GetModuleFileNameW(own_module, path, 32768);
    if (n == 0 || n >= 32768) return;
    wchar_t* slash = std::wcsrchr(path, L'\\');
    if (!slash) return;
    if (static_cast<size_t>(slash - path) + 28 >= 32768) return;
    std::wcscpy(slash + 1, L"EldenLosSantosProbe.log");
    log_file = _wfopen(path, L"a");
    log_event("probe_loaded_not_gameplay_verified");
}

void text(float x, float y, const char* message) {
    hook.invoke(0x66E0276CC5F6B9DAULL, 0); // SET_TEXT_FONT
    hook.invoke(0x07C837F9A01C34C9ULL, 0.0f, 0.34f);
    hook.invoke(0xBE6B23FFA53FB442ULL, 255, 255, 255, 230);
    hook.invoke(0xC02F4DBFB51D988BULL, false);
    hook.invoke(0x2513DFB0FB8400FEULL);
    hook.invoke(0x25FBB336DF1804CBULL, "STRING");
    hook.invoke(0x6C188BE134E074AAULL, message);
    hook.invoke(0xCD015E5BB0D96A57ULL, x, y, 0);
}

void clear() {
    if (streaming) {
        hook.invoke(0xE532F5D78798DAABULL, model);
        streaming = false;
    }
    int actor = probe.actor();
    if (actor && hook.invoke<int>(0x7239B21A38F536BAULL, actor)) {
        hook.invoke(0x9614299DCB53E54BULL, &actor);
    }
    log_event("reset");
    probe.reset();
    status = "F6: spawn GTA test actor | F7: remove";
}

void request_spawn() {
    clear();
    if (!hook.invoke<int>(0xC0296A2EDF545E92ULL, model) ||
        !hook.invoke<int>(0x35B9E0803292B641ULL, model)) {
        status = "Test model unavailable";
        log_event("invalid_model");
        return;
    }
    stream_started = hook.invoke<std::uint32_t>(0x9CD27B0045628463ULL);
    streaming = true;
    hook.invoke(0x963D27A58DF860ACULL, model);
    status = "Loading GTA test actor...";
}

void finish_spawn() {
    const auto now = hook.invoke<std::uint32_t>(0x9CD27B0045628463ULL);
    if (now - stream_started > 10000) {
        clear();
        status = "Model load timed out; F6 retries";
        log_event("model_timeout");
        return;
    }
    if (!hook.invoke<int>(0x98A4EB5D89A0C952ULL, model)) return;
    const int player = hook.invoke<int>(0xD80958FC74E988A6ULL);
    const auto p = hook.invoke<ergt::NativeVector>(0x1899F328B0E12848ULL, player, 0.0f, 12.0f, 0.0f);
    float ground = 0.0f;
    if (!hook.invoke<int>(0xC906A7DAB05C8D2BULL, p.x, p.y, p.z + 100.0f, &ground, false, false)) {
        clear();
        status = "No ground found; stand outdoors and press F6";
        log_event("no_ground");
        return;
    }
    const float heading = hook.invoke<float>(0xE83D4F9BA2A38914ULL, player) + 180.0f;
    const int actor = hook.invoke<int>(0xD49F9B0955C367DEULL, 4, model,
                                       p.x, p.y, ground + 0.5f, heading, false, true);
    hook.invoke(0xE532F5D78798DAABULL, model);
    streaming = false;
    if (!actor || !hook.invoke<int>(0x7239B21A38F536BAULL, actor)) {
        status = "GTA did not create the test actor";
        log_event("spawn_failed");
        return;
    }
    hook.invoke(0xAD738C3085FE7E11ULL, actor, true, true);
    hook.invoke(0xF5F6378C4F3419D3ULL, actor, maximum_health);
    hook.invoke(0x166E7CF68597D8B5ULL, actor, maximum_health);
    hook.invoke(0x6B76DC1F3AE6E6A3ULL, actor, maximum_health, 0, 0u);
    hook.invoke(0xEBD76F2359F190ACULL, actor, false);
    hook.invoke(0xB128377056A54E2AULL, actor, false);
    hook.invoke(0x9F8AA94D6D97DBF4ULL, actor, true);
    hook.invoke(0x919BE13EED931959ULL, actor, -1);
    probe.start(actor, hook.invoke<int>(0xEEF059FAD016D209ULL, actor));
    status = "Shoot or hit the GTA test actor. F6: reset | F7: remove";
    log_event("spawn");
}

void keyboard(DWORD key, WORD, BYTE, BOOL, BOOL alt, BOOL was_down, BOOL is_up) {
    if (alt || was_down || is_up) return;
    if (key == VK_F6) spawn_requested.store(true);
    if (key == VK_F7) clear_requested.store(true);
}

void run() {
    open_log();
    for (;;) {
        // Extra guard in addition to Script Hook V's own offline-only policy.
        if (hook.invoke<int>(0x9DE624D2FC4B603FULL)) {
            spawn_requested.store(false);
            clear_requested.store(false);
            hook.wait(100);
            continue;
        }
        if (clear_requested.exchange(false)) {
            spawn_requested.store(false);
            clear();
        }
        if (!hook.invoke<int>(0xB0034A223497FFCBULL)) {
            if (spawn_requested.exchange(false)) request_spawn();
            if (streaming) finish_spawn();
            if (probe.state() == ergt::ProbeState::alive) {
                const int actor = probe.actor();
                const bool exists = hook.invoke<int>(0x7239B21A38F536BAULL, actor) != 0;
                const int health = exists ? hook.invoke<int>(0xEEF059FAD016D209ULL, actor) : 0;
                const bool dead = exists && hook.invoke<int>(0x5F9532F3B5CC2551ULL, actor, false);
                const auto sample = probe.observe(exists, health, dead);
                if (sample.lost_health) log_event("native_health_loss", sample.lost_health);
                if (sample.died) { status = "Test actor defeated. F6: reset | F7: remove"; log_event("death"); }
                if (sample.disappeared) { status = "Test actor disappeared; F6: reset"; log_event("actor_missing"); }
            }
            text(0.025f, 0.03f, "Elden x GTA - DAMAGE PROBE (GTA test actor)");
            text(0.025f, 0.06f, status);
            char line[128]{};
            std::snprintf(line, sizeof(line), "Raw GTA health: %d | observed loss: %llu",
                          probe.health(), static_cast<unsigned long long>(probe.total_loss()));
            text(0.025f, 0.09f, line);
            hook.invoke(0x3A618A217E5154F0ULL, 0.175f, 0.135f, 0.30f, 0.012f, 30, 30, 30, 220, false);
            const float width = 0.30f * probe.ratio();
            hook.invoke(0x3A618A217E5154F0ULL, 0.025f + width / 2.0f, 0.135f, width, 0.012f, 190, 35, 40, 240, false);
        } else {
            // A press while paused must not unexpectedly spawn on unpause.
            spawn_requested.store(false);
        }
        hook.wait(0);
    }
}
} // namespace

BOOL APIENTRY DllMain(HMODULE module, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        own_module = module;
        if (ergt_runtime_dependency() < 0) return FALSE;
        if (!hook.bind()) return FALSE;
        hook.register_script(module, run);
        hook.register_keyboard(keyboard);
        registered = true;
    } else if (reason == DLL_PROCESS_DETACH && registered) {
        hook.unregister_keyboard(keyboard);
        hook.unregister_script(module);
        // Natives may only run on the script thread. Press F7 before dev reload.
        if (log_file) { std::fclose(log_file); log_file = nullptr; }
    }
    return TRUE;
}
