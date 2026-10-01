//! Deterministic rules for the planned Terminal mission.
//! Runtime adapters must supply verified events; these rules do not claim map or asset integration.
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

pub const RUN_MS: u64 = 600_000;
pub const STRIKE_MS: u64 = 8_000;
pub const REQUIRED_CHARGE: u32 = 1_000;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Phase {
    Concourse,
    BuildRoute,
    TrickLine,
    Defend,
    DragonPass,
    Extract,
    Won,
    Lost,
}

#[derive(Clone, Debug, Serialize)]
pub struct Mission {
    pub phase: Phase,
    pub elapsed_ms: u64,
    pub charge: u32,
    pub kills: u32,
    pub deaths: u32,
    pub placed_blocks: u32,
    last_landing: u64,
    defeated: BTreeSet<u64>,
    defense_kills: u32,
    strike_at: Option<u64>,
}

#[derive(Clone, Copy, Debug)]
pub enum Event {
    EnemyDefeated(u64),
    BlockCount(u32),
    RouteReached,
    Landed {
        sequence: u64,
        points: u32,
        clean: bool,
    },
    Died,
    CallDragon {
        asset_ready: bool,
    },
    Extracted,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Effect {
    None,
    PhaseChanged,
    RespawnCheckpoint,
    DragonStarted,
    MissingDragonAsset,
}

impl Default for Mission {
    fn default() -> Self {
        Self {
            phase: Phase::Concourse,
            elapsed_ms: 0,
            charge: 0,
            kills: 0,
            deaths: 0,
            placed_blocks: 0,
            last_landing: 0,
            defeated: BTreeSet::new(),
            defense_kills: 0,
            strike_at: None,
        }
    }
}
impl Mission {
    pub fn finished(&self) -> bool {
        matches!(self.phase, Phase::Won | Phase::Lost)
    }
    pub fn remaining_ms(&self) -> u64 {
        RUN_MS.saturating_sub(self.elapsed_ms)
    }
    pub fn advance(&mut self, millis: u64, paused: bool) {
        if paused || self.finished() {
            return;
        }
        self.elapsed_ms = self.elapsed_ms.saturating_add(millis).min(RUN_MS);
        if self.elapsed_ms >= RUN_MS {
            self.phase = Phase::Lost;
            return;
        }
        if self.phase == Phase::DragonPass
            && self
                .strike_at
                .is_some_and(|t| self.elapsed_ms.saturating_sub(t) >= STRIKE_MS)
        {
            self.phase = Phase::Extract;
        }
    }
    pub fn apply(&mut self, event: Event) -> Effect {
        if self.finished() {
            return Effect::None;
        }
        let previous = self.phase;
        match event {
            Event::EnemyDefeated(id) => {
                if !self.defeated.insert(id) {
                    return Effect::None;
                }
                self.kills += 1;
                if self.phase == Phase::Concourse && self.kills >= 3 {
                    self.phase = Phase::BuildRoute;
                } else if self.phase == Phase::Defend {
                    self.defense_kills += 1;
                }
            }
            Event::BlockCount(count) => self.placed_blocks = count,
            Event::RouteReached if self.phase == Phase::BuildRoute && self.placed_blocks >= 6 => {
                self.phase = Phase::TrickLine;
            }
            Event::Landed {
                sequence,
                points,
                clean,
            } => {
                if sequence <= self.last_landing {
                    return Effect::None;
                }
                self.last_landing = sequence;
                if self.phase == Phase::TrickLine && clean {
                    self.charge = self.charge.saturating_add(points).min(REQUIRED_CHARGE);
                    if self.charge == REQUIRED_CHARGE {
                        self.phase = Phase::Defend;
                    }
                }
            }
            Event::Died => {
                self.deaths += 1;
                self.advance(15_000, false);
                return if self.finished() {
                    Effect::PhaseChanged
                } else {
                    Effect::RespawnCheckpoint
                };
            }
            Event::CallDragon { asset_ready }
                if self.phase == Phase::Defend
                    && self.defense_kills >= 5
                    && self.charge == REQUIRED_CHARGE =>
            {
                if !asset_ready {
                    return Effect::MissingDragonAsset;
                }
                self.charge = 0;
                self.strike_at = Some(self.elapsed_ms);
                self.phase = Phase::DragonPass;
                return Effect::DragonStarted;
            }
            Event::Extracted if self.phase == Phase::Extract => self.phase = Phase::Won,
            _ => {}
        }
        if self.phase != previous {
            Effect::PhaseChanged
        } else {
            Effect::None
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Cell(pub i32, pub i32, pub i32);

#[derive(Clone, Copy, Debug, Default)]
pub struct PlacementProbe {
    pub overlaps_player: bool,
    pub overlaps_original_map: bool,
    pub protected: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct BlockLayer {
    schema: u32,
    map: String,
    cells: BTreeSet<Cell>,
    limit: usize,
    revision: u64,
}
impl BlockLayer {
    pub fn new(map: impl Into<String>) -> Self {
        Self {
            schema: 1,
            map: map.into(),
            cells: BTreeSet::new(),
            limit: 128,
            revision: 0,
        }
    }
    pub fn cells(&self) -> &BTreeSet<Cell> {
        &self.cells
    }
    pub fn revision(&self) -> u64 {
        self.revision
    }
    pub fn place(&mut self, cell: Cell, probe: PlacementProbe) -> Result<(), &'static str> {
        if !valid_cell(cell) {
            return Err("outside build bounds");
        }
        if probe.overlaps_player {
            return Err("player occupies block");
        }
        if probe.overlaps_original_map {
            return Err("original map occupies block");
        }
        if probe.protected {
            return Err("protected route");
        }
        if self.cells.contains(&cell) {
            return Err("block already exists");
        }
        if self.cells.len() >= self.limit {
            return Err("block budget exhausted");
        }
        self.cells.insert(cell);
        self.revision += 1;
        Ok(())
    }
    pub fn remove(&mut self, cell: Cell) -> bool {
        if self.cells.remove(&cell) {
            self.revision += 1;
            true
        } else {
            false
        }
    }
    pub fn save(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }
    pub fn restore(json: &str, expected_map: &str) -> Result<Self, String> {
        if json.len() > 64 * 1024 {
            return Err("save exceeds size limit".into());
        }
        let layer: Self = serde_json::from_str(json).map_err(|e| e.to_string())?;
        if layer.schema != 1
            || layer.map != expected_map
            || layer.limit != 128
            || layer.cells.len() > layer.limit
            || layer.cells.iter().any(|c| !valid_cell(*c))
        {
            return Err("incompatible or invalid block save".into());
        }
        Ok(layer)
    }
    /// Nearest placed cube on a ray. Coordinates and returned distance are in block units.
    pub fn raycast(
        &self,
        origin: [f32; 3],
        direction: [f32; 3],
        max_distance: f32,
    ) -> Option<(Cell, f32)> {
        if !origin.iter().chain(direction.iter()).all(|x| x.is_finite())
            || !max_distance.is_finite()
            || max_distance <= 0.0
        {
            return None;
        }
        let length = direction.iter().map(|v| v * v).sum::<f32>().sqrt();
        if length < 1e-6 {
            return None;
        }
        let d = direction.map(|v| v / length);
        self.cells
            .iter()
            .filter_map(|cell| {
                let min = [cell.0 as f32, cell.1 as f32, cell.2 as f32];
                let mut near = 0.0_f32;
                let mut far = max_distance;
                for k in 0..3 {
                    if d[k].abs() < 1e-6 {
                        if origin[k] < min[k] || origin[k] > min[k] + 1.0 {
                            return None;
                        }
                    } else {
                        let a = (min[k] - origin[k]) / d[k];
                        let z = (min[k] + 1.0 - origin[k]) / d[k];
                        near = near.max(a.min(z));
                        far = far.min(a.max(z));
                        if near > far {
                            return None;
                        }
                    }
                }
                Some((*cell, near))
            })
            .min_by(|a, b| a.1.total_cmp(&b.1))
    }
}
fn valid_cell(c: Cell) -> bool {
    [c.0, c.1, c.2].iter().all(|v| (-4096..=4096).contains(v))
}

/// A deterministic rule check, not a gameplay or renderer test.
pub fn scenario() -> Mission {
    let mut m = Mission::default();
    for id in 1..=3 {
        m.apply(Event::EnemyDefeated(id));
    }
    m.advance(120_000, false);
    m.apply(Event::BlockCount(6));
    m.apply(Event::RouteReached);
    m.advance(120_000, false);
    for sequence in 1..=4 {
        m.apply(Event::Landed {
            sequence,
            points: 250,
            clean: true,
        });
    }
    m.advance(120_000, false);
    for id in 4..=8 {
        m.apply(Event::EnemyDefeated(id));
    }
    m.advance(180_000, false);
    m.apply(Event::CallDragon { asset_ready: true });
    m.advance(STRIKE_MS, false);
    m.apply(Event::Extracted);
    m
}

#[cfg(test)]
mod tests {
    use super::*;
    fn charged() -> Mission {
        let mut m = Mission::default();
        for id in 1..=3 {
            m.apply(Event::EnemyDefeated(id));
        }
        m.apply(Event::BlockCount(6));
        m.apply(Event::RouteReached);
        m.apply(Event::Landed {
            sequence: 1,
            points: 1000,
            clean: true,
        });
        for id in 4..=8 {
            m.apply(Event::EnemyDefeated(id));
        }
        m
    }
    #[test]
    fn complete_run_has_real_end_and_timeout_is_terminal() {
        let m = scenario();
        assert_eq!(m.phase, Phase::Won);
        assert_eq!(m.elapsed_ms, 548_000);
        let mut m = Mission::default();
        m.advance(RUN_MS, false);
        m.apply(Event::Extracted);
        assert_eq!(m.phase, Phase::Lost);
    }
    #[test]
    fn cannot_skip_objectives_or_replay_rewards() {
        let mut m = Mission::default();
        m.apply(Event::Extracted);
        m.apply(Event::RouteReached);
        for _ in 0..5 {
            m.apply(Event::EnemyDefeated(1));
        }
        assert_eq!(m.phase, Phase::Concourse);
        assert_eq!(m.kills, 1);
        m.apply(Event::EnemyDefeated(2));
        m.apply(Event::EnemyDefeated(3));
        m.apply(Event::BlockCount(5));
        m.apply(Event::RouteReached);
        assert_eq!(m.phase, Phase::BuildRoute);
        m.apply(Event::BlockCount(6));
        m.apply(Event::RouteReached);
        m.apply(Event::Landed {
            sequence: 1,
            points: 900,
            clean: false,
        });
        m.apply(Event::Landed {
            sequence: 1,
            points: 900,
            clean: true,
        });
        assert_eq!(m.charge, 0);
        m.apply(Event::Landed {
            sequence: 2,
            points: 250,
            clean: true,
        });
        m.apply(Event::Landed {
            sequence: 2,
            points: 250,
            clean: true,
        });
        assert_eq!(m.charge, 250);
    }
    #[test]
    fn missing_dragon_does_not_spend_reward() {
        let mut m = charged();
        assert_eq!(
            m.apply(Event::CallDragon { asset_ready: false }),
            Effect::MissingDragonAsset
        );
        assert_eq!(m.charge, REQUIRED_CHARGE);
        assert_eq!(m.phase, Phase::Defend);
        assert_eq!(
            m.apply(Event::CallDragon { asset_ready: true }),
            Effect::DragonStarted
        );
        assert_eq!(m.charge, 0);
        assert_eq!(
            m.apply(Event::CallDragon { asset_ready: true }),
            Effect::None
        );
        m.apply(Event::Extracted);
        assert_eq!(m.phase, Phase::DragonPass);
        m.advance(STRIKE_MS, false);
        m.apply(Event::Extracted);
        assert_eq!(m.phase, Phase::Won);
    }
    #[test]
    fn pause_death_and_restart_keep_clock_consistent() {
        let mut m = Mission::default();
        m.advance(10_000, true);
        assert_eq!(m.elapsed_ms, 0);
        m.advance(RUN_MS - 10_000, false);
        m.apply(Event::Died);
        assert_eq!(m.phase, Phase::Lost);
        m = Mission::default();
        assert_eq!(m.remaining_ms(), RUN_MS);
        assert_eq!(m.kills, 0);
    }
    #[test]
    fn blocks_respect_scene_probes_budget_and_save_identity() {
        let mut b = BlockLayer::new("mp_terminal");
        assert!(
            b.place(
                Cell(0, 0, 0),
                PlacementProbe {
                    overlaps_player: true,
                    ..Default::default()
                }
            )
            .is_err()
        );
        assert!(
            b.place(
                Cell(0, 0, 0),
                PlacementProbe {
                    overlaps_original_map: true,
                    ..Default::default()
                }
            )
            .is_err()
        );
        for x in 0..128 {
            b.place(Cell(x, 0, 0), Default::default()).unwrap();
        }
        assert!(b.place(Cell(128, 0, 0), Default::default()).is_err());
        let json = b.save().unwrap();
        assert!(BlockLayer::restore(&json, "mp_rust").is_err());
        assert_eq!(
            BlockLayer::restore(&json, "mp_terminal")
                .unwrap()
                .cells()
                .len(),
            128
        );
        assert!(b.remove(Cell(0, 0, 0)));
        assert!(!b.remove(Cell(0, 0, 0)));
        b.place(Cell(128, 0, 0), Default::default()).unwrap();
    }
    #[test]
    fn rays_hit_nearest_cube_and_reject_invalid_input() {
        let mut b = BlockLayer::new("mp_terminal");
        for x in [4, 8] {
            b.place(Cell(x, 0, 0), Default::default()).unwrap();
        }
        assert_eq!(
            b.raycast([0., 0.5, 0.5], [1., 0., 0.], 10.),
            Some((Cell(4, 0, 0), 4.))
        );
        assert_eq!(b.raycast([0., 0.5, 0.5], [1., 0., 0.], 3.), None);
        assert_eq!(b.raycast([0., 2., 0.5], [1., 0., 0.], 10.), None);
        assert_eq!(b.raycast([f32::NAN, 0., 0.], [1., 0., 0.], 10.), None);
    }
}
