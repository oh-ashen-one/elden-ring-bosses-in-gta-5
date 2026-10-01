use serde::{Deserialize, Serialize};
use std::{
    collections::BTreeSet,
    path::{Path, PathBuf},
};

#[derive(Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct Config {
    pub mw2: Option<PathBuf>,
    pub skate_source: Option<PathBuf>,
    pub skate_assets: Option<PathBuf>,
    pub skyrim: Option<PathBuf>,
    pub minecraft: Option<PathBuf>,
}
#[derive(Serialize)]
pub struct Component {
    pub id: &'static str,
    pub title: &'static str,
    pub path: Option<PathBuf>,
    pub ready: bool,
    pub detail: String,
}
#[derive(Serialize)]
pub struct Report {
    pub platform: String,
    pub mw2_ready: bool,
    pub crossover_mission_ready: bool,
    pub components: Vec<Component>,
}
pub fn state_dir() -> Result<PathBuf, String> {
    if let Some(p) = std::env::var_os("MW2AI_HOME") {
        return Ok(PathBuf::from(p));
    }
    let home = std::env::var_os("HOME").ok_or("Cannot locate the user's home directory.")?;
    Ok(PathBuf::from(home).join("Library/Application Support/Modern Warfare 2 AI"))
}
pub fn config_path() -> Result<PathBuf, String> {
    Ok(state_dir()?.join("settings.json"))
}
impl Config {
    pub fn load(path: &Path) -> Result<Self, String> {
        match std::fs::read(path) {
            Ok(bytes) => {
                if bytes.len() > 64 * 1024 {
                    return Err("Settings file is too large.".into());
                }
                serde_json::from_slice(&bytes).map_err(|e| format!("Could not read settings: {e}"))
            }
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(Self::default()),
            Err(e) => Err(e.to_string()),
        }
    }
    pub fn save(&self, path: &Path) -> Result<(), String> {
        let parent = path.parent().ok_or("Settings path has no parent.")?;
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        let temporary = path.with_extension(format!("{}.tmp", std::process::id()));
        std::fs::write(
            &temporary,
            serde_json::to_vec_pretty(self).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())?;
        std::fs::rename(temporary, path).map_err(|e| e.to_string())
    }
    pub fn report(&self) -> Report {
        let mw2 = self.mw2.as_ref().is_some_and(|root| {
            find_file(root, "common_mp.ff", true)
                && find_file(root, "mp_terminal.ff", true)
                && find_file(root, "code_post_gfx_mp.ff", true)
        });
        let skate_source = self
            .skate_source
            .as_ref()
            .is_some_and(|p| p.join("default.xex").is_file() && p.join("data").is_dir());
        let skate = self
            .skate_assets
            .as_ref()
            .is_some_and(|p| p.join("rig.json").is_file() && p.join("board.json").is_file());
        let skyrim = self
            .skyrim
            .as_ref()
            .is_some_and(|p| find_file(p, "Skyrim.esm", false));
        let mc = self
            .minecraft
            .as_ref()
            .is_some_and(|p| p.join("datapacks").is_dir() && p.join("resourcepacks").is_dir());
        let components=vec![
            Component{id:"mw2",title:"Modern Warfare 2 (2009 PC)",path:self.mw2.clone(),ready:mw2,
                detail:if mw2{"Terminal and shared multiplayer zone headers found. Runtime playtest still required."}else{"Required for Terminal. Select the Windows PC multiplayer data folder; common_mp, code_post_gfx_mp and mp_terminal must be present."}.into()},
            Component{id:"skate-source",title:"Skate 3 — original data",path:self.skate_source.clone(),ready:skate_source,
                detail:if skate_source{"Extracted Xbox 360 data found. Conversion is still required."}else{"Select the folder containing default.xex and data from your own Xbox 360 copy."}.into()},
            Component{id:"skate-assets",title:"Skate 3 — converted data",path:self.skate_assets.clone(),ready:skate,
                detail:if skate{"Rig and board files found; animation-bank validity needs a runtime check."}else{"Optional for the MW2 baseline. Select converted skating data after running the converter."}.into()},
            Component{id:"skyrim",title:"Skyrim Special Edition",path:self.skyrim.clone(),ready:skyrim,
                detail:if skyrim{"Game data found. Dragon conversion and the encounter are not implemented yet."}else{"Needed later for the dragon. Select the game or Data folder. Nothing is downloaded."}.into()},
            Component{id:"minecraft",title:"Minecraft Java",path:self.minecraft.clone(),ready:mc,
                detail:if mc{"Prepared resource and data pack folders found. World integration needs verification."}else{"Optional for the MW2 baseline. Select a prepared MinecraftOSS data root after acquiring the game. Automatic downloads are disabled."}.into()},
        ];
        Report {
            platform: format!("{}-{}", std::env::consts::ARCH, std::env::consts::OS),
            mw2_ready: mw2,
            crossover_mission_ready: false,
            components,
        }
    }
}
fn find_file(root: &Path, name: &str, zone: bool) -> bool {
    let mut queue = vec![(root.to_path_buf(), 0)];
    let mut visited = BTreeSet::new();
    let mut scanned = 0;
    while let Some((path, depth)) = queue.pop() {
        scanned += 1;
        if scanned > 20_000 {
            return false;
        }
        if path
            .file_name()
            .is_some_and(|n| n.to_string_lossy().eq_ignore_ascii_case(name))
            && path.is_file()
        {
            if !zone {
                return true;
            }
            use std::io::Read;
            let mut header = [0; 12];
            if std::fs::File::open(&path)
                .and_then(|mut f| f.read_exact(&mut header))
                .is_ok()
                && &header[..4] == b"IWff"
                && u32::from_le_bytes(header[8..12].try_into().unwrap()) == 0x114
            {
                return true;
            }
        }
        if depth >= 5 || !path.is_dir() {
            continue;
        }
        let Ok(canonical) = path.canonicalize() else {
            continue;
        };
        if !visited.insert(canonical) {
            continue;
        }
        if let Ok(entries) = std::fs::read_dir(path) {
            for entry in entries.flatten() {
                queue.push((entry.path(), depth + 1));
            }
        }
    }
    false
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn missing_data_is_reported_without_creating_or_downloading_anything() {
        let c = Config::default();
        let r = c.report();
        assert!(!r.mw2_ready);
        assert!(!r.crossover_mission_ready);
        assert_eq!(r.components.len(), 5);
    }
    #[test]
    fn invalid_zone_cannot_enable_launch_and_config_roundtrips() {
        let root = std::env::temp_dir().join(format!("mw2ai-setup-test-{}", std::process::id()));
        std::fs::create_dir_all(root.join("zone/english")).unwrap();
        let c = Config {
            mw2: Some(root.clone()),
            ..Default::default()
        };
        for name in ["common_mp.ff", "mp_terminal.ff", "code_post_gfx_mp.ff"] {
            std::fs::write(root.join("zone/english").join(name), b"not-a-valid-zone").unwrap();
        }
        assert!(!c.report().mw2_ready);
        let mut header = [0u8; 12];
        header[..4].copy_from_slice(b"IWff");
        header[8..].copy_from_slice(&0x114u32.to_le_bytes());
        for name in ["common_mp.ff", "mp_terminal.ff", "code_post_gfx_mp.ff"] {
            std::fs::write(root.join("zone/english").join(name), header).unwrap();
        }
        assert!(c.report().mw2_ready);
        assert!(!c.report().crossover_mission_ready);
        let path = root.join("settings.json");
        c.save(&path).unwrap();
        assert_eq!(Config::load(&path).unwrap().mw2, c.mw2);
        std::fs::remove_dir_all(root).unwrap();
    }
}
