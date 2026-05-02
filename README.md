# WASTELAND ZERO
### Feature Specification | CSE423: Computer Graphics 

---

## **Game Concept Overview**

Wasteland Zero is a post-apocalyptic survival horror game built with Python and PyOpenGL. Players navigate a radioactive wasteland left behind after humanity's collapse. Every day you venture out to fight and scavenge, and every night you return home to feed and protect an injured pet who depends entirely on you.

---

## **Core Gameplay Loop**

The game runs on a repeating daily cycle that escalates in difficulty with each passing day:

1. Leave homebase and enter the wasteland  
2. Fight enemies and collect resources  
3. Survive hazards — radiation, boss encounters, random events  
4. Return to homebase before nightfall  
5. Feed and protect the injured pet (once per in-game day)  
6. Repeat with increasing difficulty  

---

## **Features**

### Player System
1. **Movement & Model**: Simple player model with basic animations: walk, run, interact, attack  
2. **Customization**: (Visual only, no gameplay effect)
    - Body color
    - Leg color

### View
3. **Camera System**: Dynamic perspective modes including top-down and orbiting views.

### Combat System
4. **Shooting Mechanics**: Shooting-based combat is the primary form of fighting. Ammo is a limited resource; players must scavenge to resupply.

### Enemy System
5. **Movement**: 
    - Enemies patrol autonomously when idle.
    - Aggro system: detect player → chase → attack.
6. **Variants**:
    - **Basic enemies**: Standard speed and damage (Mutants, Wanderers).
    - **Advanced enemies**: Faster, ranged, or tankier threats (Shooters, Tanks).

### World & Level Design
7. **Radioactive Wasteland**:
    - High-radiation zones (Acid) that deal continuous damage-over-time.
    - More aggressive enemy spawns over time.
    - Increased environmental hazards as the game progresses.
    - **Homebase safe zone**: Enemies do not enter or spawn inside.
8. **Day/Night Cycle**: Player must return to homebase before night falls to avoid total failure.

### Pet Systems
9. **Pet System**:
    - Stationary, injured dependent.
    - Represented by the "Biomass Reserve" (Food) requirement.
    - Must be fed once per in-game day using food collected from chests.

### Items & Loot System
10. **Keys**: Dropped by defeated enemies; used to unlock chests.
11. **Chests**: Require a key to open. Contain: health, ammo, and food.

### Special Systems
12. **Spaceship Travel**: 
    - Allows safe long-distance travel across the wasteland.
    - Enemies cannot damage the player while inside the ship.
13. **Environmental Hazard — Radioactive Bombs**:
    - Dropped from orbiting ships at random intervals.
    - Warning: affected ground blinks before impact.
    - Player must identify and vacate the zone before detonation.

### UI & Game Systems
14. **HUD**: Includes health bar, ammo counter, day counter, and danger level indicator.
15. **Notification System**: Real-time feedback for items collected, hacks triggered, or critical warnings.
16. **Minimap**: (Optional/Exploration) Shows player location and points of interest.

---

## **Technical Implementation**

### How to Run

#### Option 1: Virtual Environment (Recommended)
1. **Requirements**: Python 3.x and dependencies listed in `requirements.txt`.
2. **Setup**:
   - Set up a virtual environment: `python -m venv .venv`
   - Activate it: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)
   - Install dependencies: `pip install -r requirements.txt`
3. **Execution**: Run `python main.py` to start the game.

#### Option 2: Manual Folder Setup
1. **Requirements**: Python 3.x.
2. **Setup**: Place the `OpenGL` folder directly in the same directory as `main.py`.
3. **Execution**: Run `main.py` directly using your Python interpreter.

### Controls
* **WASD**: Movement  
* **Space**: Shoot  
* **B**: Drop Bomb (Hazard)  
* **Q**: Exit Spaceship / Leave Homebase  
* **M**: Toggle Minimap Mode  
* **P**: Pause Game  
* **` (Backtick)**: Toggle Debug Mode  
* **Arrow Keys**: Adjust Camera View  
* **= / -**: Zoom Camera In/Out  
