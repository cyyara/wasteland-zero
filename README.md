# Wasteland Zero

A post-apocalyptic survival game built with Python and PyOpenGL for CSE423: Computer Graphics.

---

## Setup

### Option 1: Virtual Environment (Recommended)

```bash
python -m venv .venv
```

Activate:
- Windows: `.venv\Scripts\activate`
- Mac/Linux: `source .venv/bin/activate`

Install dependencies:
```bash
pip install -r requirements.txt
```

Run:
```bash
python main.py
```

### Option 2: Manual

Place the `OpenGL` folder in the same directory as `main.py`, then run `main.py` with your Python interpreter.

---

## Controls

| Key | Action |
|-----|--------|
| `W` `A` `S` `D` | Move and turn |
| `Space` | Shoot |
| `Q` | Exit spaceship / Leave homebase early |
| `M` | Toggle minimap (local / global) |
| `P` | Pause |
| `C` | Customize player (from pause menu) |
| `Arrow Keys` | Rotate and adjust camera |
| `=` / `-` | Zoom camera in / out |
| `` ` `` | Toggle debug mode |
| `R` | Restart (from game over screen) |

### Debug Mode Keys (when enabled)

| Key | Action |
|-----|--------|
| `1` | Full health |
| `2` | Full ammo |
| `3` | Add key |
| `4` | Spawn all enemy types |
| `5` | Spawn all item types |
| `6` | Enter spaceship |
| `7` | Skip to night |
| `8` | Trigger chest reward |
| `B` | Drop bomb |

---

## Gameplay

### Core Loop

Each run follows a repeating daily cycle that grows harder with each passing day:

1. Leave the homebase through the portal
2. Fight enemies and collect resources
3. Survive hazards — acid zones, falling bombs, enemy fire
4. Return to homebase before the day cycle ends
5. Repeat with increasing difficulty

Missing a full day/night cycle without returning to homebase results in **instant death**.

### World

The wasteland is a procedurally generated 40×40 tile grid. Each run places terrain features randomly with no two overlapping:

| Tile | Effect |
|------|--------|
| Wasteland | Standard ground |
| Acid | Drains biomass reserve, then health |
| Water | Slowly restores health |
| Trees | Impassable |
| Portal | Entrance to homebase |

### Enemies

| Enemy | Behavior |
|-------|----------|
| Mutant | Balanced melee |
| Wanderer | Slow, low health |
| Shooter | Ranged, fires on cooldown |
| Tank | Slow, high health, telegraphed ranged attack |

All enemies patrol when idle and chase when the player enters detection range. Speed and detection range scale with difficulty over time. Tanks always drop loot on death. Other enemies have a 30% drop chance.

### Items

| Item | Effect |
|------|--------|
| Health Pack | Restores 25 HP (only if not full) |
| Ammo Pack | Restores 10 ammo (only if not full) |
| Food Pack | +1 biomass reserve |
| Shield Pack | Temporary immunity to damage |
| Key | Used to unlock chests |
| Chest | Requires a key; gives a useful random reward |
| Spaceship | Vehicle with separate health pool and acid immunity |

### Homebase

Entering the homebase via the portal:
- Fully restores health and ammo
- Marks the current cycle as visited (preventing the death penalty)
- Automatically returns the player to the wasteland after 15 seconds
- Triggers a 30-second portal cooldown on exit

### Biomass Reserve

Food collected from packs and chests fills the biomass reserve. When walking through acid without a shield, the reserve drains first — once it hits zero, health starts taking damage.

---

## Technical Notes

- Single-file implementation (`main.py`)
- Rendering: PyOpenGL with GLUT — `glutSolidSphere`, `glutSolidCube`, `gluCylinder` for 3D; `GL_QUADS` and `GL_POINTS` for 2D UI
- No external assets — all geometry is procedural
- All game state is held in class-level variables; no instances of manager classes are created
```
