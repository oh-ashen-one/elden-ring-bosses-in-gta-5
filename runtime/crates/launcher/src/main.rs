use std::path::PathBuf;

use asset_transport::{ensure_artifacts_dir, games_root_from_env};

#[cfg(windows)]
mod first_run;

#[global_allocator]
static PROCESS_ALLOCATOR: diag::ProcessCountingAllocator = diag::ProcessCountingAllocator;

fn main() {
    // Asset preparation is a command-line operation and never starts a renderer or network listener.
    let setup_args: Vec<String> = std::env::args().skip(1).collect();
    if setup_args.first().map(String::as_str) == Some("prepare-skate") {
        if setup_args.len() != 2 {
            eprintln!("usage: iw4l prepare-skate <converted-assets-folder>");
            std::process::exit(2);
        }
        match assets::skate_board::ensure(std::path::Path::new(&setup_args[1])) {
            Ok(()) => println!("Skate board and rig prepared."),
            Err(error) => { eprintln!("{error}"); std::process::exit(2); }
        }
        return;
    }
    bootstrap::bench::arm();
    prepare_process_root().unwrap_or_else(|e| {
        diag::exit_launch_error(&e);
    });
    #[cfg_attr(not(windows), allow(unused_mut))]
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    #[cfg(windows)]
    {
        // Also for a shortcut that names a map, so it works on first launch.
        first_run::prepare().unwrap_or_else(|e| first_run::fail(&e));
        if args.is_empty() {
            args.push("menu".into());
        }
    }
    let artifacts = ensure_artifacts_dir().unwrap_or_else(|e| diag::exit_launch_error(&e));
    announce_log(diag::init_log(&artifacts));
    let (mode, acceptance) =
        bootstrap::parse_cli(args.into_iter()).unwrap_or_else(|e| diag::exit_launch_error(&e));
    let games = games_root_from_env().unwrap_or_else(|e| diag::exit_launch_error(&e));
    #[cfg(target_os = "macos")]
    if let Some(root) = std::env::var_os("IW4L_SKATE_ASSETS") {
        assets::skate_board::ensure(std::path::Path::new(&root))
            .unwrap_or_else(|e| diag::exit_launch_error(&format!("Skate setup: {e}")));
    }
    bootstrap::launch(games, artifacts, mode, acceptance);
}

fn prepare_process_root() -> Result<(), String> {
    #[cfg(windows)]
    {
        let exe =
            std::env::current_exe().map_err(|error| format!("cannot locate iw4l.exe: {error}"))?;
        let root = exe
            .parent()
            .ok_or_else(|| format!("iw4l.exe has no parent directory: {}", exe.display()))?;
        std::env::set_current_dir(root).map_err(|error| {
            format!(
                "cannot enter launcher directory {}: {error}",
                root.display()
            )
        })?;
    }
    Ok(())
}

fn announce_log(path: PathBuf) {
    diag::announce_log_stdout(&path, diag::latest_log_path().as_deref());
    diag::info!(Launch, "log: {}", path.display());
}
