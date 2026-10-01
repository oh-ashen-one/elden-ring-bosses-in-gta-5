mod setup;
use setup::{Config, config_path};
use std::{path::PathBuf, process::Command};

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(2);
    }
}
fn run() -> Result<(), String> {
    let mut args = std::env::args().skip(1);
    let command = args.next().unwrap_or_else(|| "doctor".into());
    let rest: Vec<String> = args.collect();
    match command.as_str() {
        "--help" | "help" => println!(
            "Modern Warfare 2 AI\n\nmw2ai doctor [--json]\nmw2ai configure [--mw2 PATH] [--skate-source PATH] [--skate-assets PATH] [--skyrim PATH] [--minecraft PATH]\nmw2ai launch --runtime PATH [--map mp_terminal]\nmw2ai demo-check\n\nNo game data is downloaded or purchased by this tool."
        ),
        "doctor" => {
            let c = Config::load(&config_path()?)?;
            let report = c.report();
            println!(
                "{}",
                serde_json::to_string_pretty(&report).map_err(|e| e.to_string())?
            );
        }
        "configure" => {
            let path = config_path()?;
            let mut c = Config::load(&path)?;
            let mut i = 0;
            while i < rest.len() {
                let key = &rest[i];
                i += 1;
                let value = rest
                    .get(i)
                    .ok_or_else(|| format!("Missing value for {key}"))?;
                i += 1;
                let v = if value.is_empty() {
                    None
                } else {
                    Some(PathBuf::from(value))
                };
                if let Some(p) = &v
                    && !p.is_dir()
                {
                    return Err(format!("Choose an existing folder: {}", p.display()));
                }
                match key.as_str() {
                    "--mw2" => c.mw2 = v,
                    "--skate-source" => c.skate_source = v,
                    "--skate-assets" => c.skate_assets = v,
                    "--skyrim" => c.skyrim = v,
                    "--minecraft" => c.minecraft = v,
                    _ => return Err(format!("Unknown setting: {key}")),
                }
            }
            c.save(&path)?;
            println!(
                "{}",
                serde_json::to_string_pretty(&c.report()).map_err(|e| e.to_string())?
            );
        }
        "launch" => {
            let mut engine = None;
            let mut map = "mp_terminal".to_string();
            let mut i = 0;
            while i < rest.len() {
                let key = &rest[i];
                i += 1;
                let value = rest
                    .get(i)
                    .ok_or_else(|| format!("Missing value for {key}"))?;
                i += 1;
                match key.as_str() {
                    "--runtime" => engine = Some(PathBuf::from(value)),
                    "--map" => map = value.clone(),
                    _ => return Err(format!("Unknown option: {key}")),
                }
            }
            if map != "mp_terminal" && map != "mp_rust" {
                return Err("This prototype launcher supports mp_terminal or mp_rust.".into());
            }
            let c = Config::load(&config_path()?)?;
            if !c.report().mw2_ready {
                return Err("MW2 multiplayer data is missing or incomplete. Open setup and select the MW2 (2009 PC) folder.".into());
            }
            let engine = engine.ok_or("Pass --runtime with the built iw4l executable.")?;
            if !engine.is_file() {
                return Err(format!(
                    "Runtime executable is missing: {}",
                    engine.display()
                ));
            }
            let engine = engine.canonicalize().map_err(|e| e.to_string())?;
            let state = setup::state_dir()?;
            std::fs::create_dir_all(&state).map_err(|e| e.to_string())?;
            let mut cmd = Command::new(engine);
            cmd.env_remove("IW4L_SKATE_ASSETS")
                .env_remove("MINECRAFTOSS_ROOT");
            cmd.current_dir(state)
                .args(["map", &map])
                .env("IW4L_GAMES", c.mw2.unwrap())
                .env("MW2AI_ALLOW_MINECRAFT_DOWNLOAD", "0");
            if let Some(p) = c.skate_assets {
                cmd.env("IW4L_SKATE_ASSETS", p);
            }
            if let Some(p) = c.minecraft {
                cmd.env("MINECRAFTOSS_ROOT", p);
            }
            let status = cmd
                .status()
                .map_err(|e| format!("Could not launch runtime: {e}"))?;
            if !status.success() {
                return Err(format!(
                    "Runtime exited with {status}. Check the runtime log in the app's data folder."
                ));
            }
        }
        "demo-check" => {
            let m = mw2ai_demo_core::scenario();
            println!("{}",serde_json::to_string_pretty(&serde_json::json!({
                "kind":"headless_rule_check","gameplay_verified":false,
                "state":m,"note":"Scripted domain events only; not a Terminal, physics, asset, or rendering test."
            })).map_err(|e|e.to_string())?);
            if m.phase != mw2ai_demo_core::Phase::Won {
                return Err("Rule scenario did not finish.".into());
            }
        }
        other => return Err(format!("Unknown command {other}. Use --help.")),
    }
    Ok(())
}
