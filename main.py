# Wasteland Zero
# Single-file OpenGL survival game.
# Controls: WASD move, Space shoot, B bomb, Q exit spaceship/homebase,
#           M minimap toggle, P pause, ` debug mode
# Debug keys (when enabled): 1-8 for various hacks

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import numpy 

# =============================================================================
# INFRASTRUCTURE — Utilities and Foundation
# =============================================================================

# Calls action() after duration seconds. Registered automatically with Game.
# Usage: DelayedAction(5.0, some_function)
class DelayedAction:
    def __init__(self, duration, action):
        Game.delayedActions.append(self)
        self.duration = duration
        self.startTime = time.time()
        self.action = action

    def isComplete(self):
        return time.time() - self.startTime >= self.duration

    def update(self):
        if self.isComplete():
            self.action()
            if self in Game.delayedActions:
                Game.delayedActions.remove(self)

# Keyed by message string so duplicate notifications reset the timer
# rather than stacking. Sorted by expiry for stable display order.
class Notifications:
    # Use a dictionary to store {message: expiry_time} for automatic deduplication
    active = {}

    @classmethod
    def add(cls, message, duration=3.0):
        # Always use the latest expiry for a message
        cls.active[message] = time.time() + duration

    @classmethod
    def draw(cls):
        now = time.time()
        # Filter out expired notifications
        cls.active = {msg: expiry for msg, expiry in cls.active.items() if now < expiry}
        
        # Sort by expiry time so they stay in a consistent order
        sorted_msgs = sorted(cls.active.keys(), key=lambda x: cls.active[x])
        
        for i, msg in enumerate(sorted_msgs):
            # Draw above HUD center
            UIManager.drawText(Window.width//2 - 100, 150 + i * 25, msg, (1, 1, 0.5))

class Window:
    width = 1000
    height = 650

# =============================================================================
# CAMERA — Perspective and View Management
# =============================================================================

class Camera:
    angle = 90
    height = 500
    radius = 700
    fovY = 70
    lastCamX = 0
    lastCamZ = 0

    @classmethod
    def setupCamera(cls):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(cls.fovY, Window.width / Window.height, 10, 5000) 
             
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        rad = -math.radians(Player.angle) - math.radians(cls.angle)
        camX = Player.x + cls.radius * math.cos(rad)
        camY = cls.height
        camZ = Player.z + cls.radius * math.sin(rad)
        
        cls.lastCamX = camX
        cls.lastCamZ = camZ

        focusY = Player.legHeight + Player.bodyHeight + Player.headRadius

        gluLookAt(camX, camY, camZ,
                  Player.x, focusY, Player.z,
                  0, 1, 0)

# =============================================================================
# WORLD — Tiles and Tilesets
# =============================================================================

# Each tile optionally holds one object (a Pickup or Spaceship).
# When the player walks onto a tile, trigger() is called, which calls
# object.apply(player). If apply() returns True, the object is consumed.
class Tile:
    length = width = 150
    minimapColor = (0.35, 0.35, 0.35)
    
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.object = None
        self.color = (1, 1, 1)
        self.isWalkable = True

    def draw(self):
        startX = self.x - self.length/2
        endX = startX + self.length
        startZ = self.z - self.width/2
        endZ = startZ + self.width
        glColor3f(*self.color)
        glBegin(GL_QUADS)
        glVertex3f(startX, 0, startZ)
        glVertex3f(endX, 0, startZ)
        glVertex3f(endX, 0, endZ)
        glVertex3f(startX, 0, endZ)
        glEnd()

        if self.object:
            self.object.draw()

    def spawnObject(self, spawnable):
        self.object = spawnable(self.x, self.z)
    
    def trigger(self):
        if self.object:
            if self.object.apply(Player):
                self.object = None
    
    def discolor(self):
        r = self.color[0] * random.uniform(0.7, 1.0)
        g = self.color[1] * random.uniform(0.7, 1.0)
        b = self.color[2] * random.uniform(0.7, 1.0)
        self.color = (r, g, b)

class WastelandTile(Tile):
    def __init__(self, x, z):
        super().__init__(x, z)
        base = random.uniform(0.30, 0.45)
        r = base + random.uniform(0.03, 0.08)
        g = base + random.uniform(-0.01, 0.03)
        b = base + random.uniform(-0.04, 0.01)
        self.color = (r, g, b)

class AcidTile(Tile):
    minimapColor = (0.2, 0.8, 0.2)
    def __init__(self, x, z):
        super().__init__(x, z)
        self.offset = random.uniform(0, 10)
    
    def draw(self):
        pulse = (math.sin(time.time() * 0.5 + self.offset) + 1) / 2
        self.color = (0, 0.2 + (pulse * 0.8), 0)
        super().draw()

class WaterTile(Tile):
    minimapColor = (0.0, 0.4, 0.7)
    def __init__(self, x, z):
        super().__init__(x, z)
        self.offset = random.uniform(0, 10)
    
    def draw(self):
        self.color = (0, 0, 1)
        super().draw()

# isActive is class-level because there is only ever one portal per wasteland.
# Cooldown is managed via DelayedAction rather than a timer in update().
class PortalTile(Tile):
    isActive = True
    cooldownTime = 30
    minimapColor = (0.8, 0.8, 0.0)

    def __init__(self, x, z):
        super().__init__(x, z)
        self.activeColor = (1.0, 1.0, 0.0) 
        self.disabledColor = (0.5, 0.5, 0.0)
    
    @classmethod
    def enable(cls):
        cls.isActive = True
    @classmethod
    def disable(cls):
        cls.isActive = False
        DelayedAction(cls.cooldownTime, cls.enable)

    def trigger(self):
        if self.isActive:
            Floor.homebase.enter(self)
        
    def draw(self):
        if self.isActive:
            self.color = self.activeColor
        else:
            self.color = self.disabledColor
        super().draw()

class HomeTile(Tile):
    def __init__(self, x, z):
        super().__init__(x, z)
        self.color = (0.9, 0.85, 0.4)
        self.discolor()

    def draw(self):
        super().draw()

class TreeTile(WastelandTile):
    minimapColor = (0.05, 0.15, 0.05)
    def __init__(self, x, z):
        super().__init__(x, z)
        self.isWalkable = False
        self.trunkColor = (0.35, 0.25, 0.15)
        self.leafColor = (0.1, 0.4, 0.1)
        self.height = random.uniform(400, 700)
        self.thickness = random.uniform(60, 85)

    def draw(self):
        super().draw() # Draw wasteland base
        
        # Skip drawing if camera is inside the canopy to avoid clipping artifacts
        dx = self.x - Camera.lastCamX
        dz = self.z - Camera.lastCamZ
        if (dx*dx + dz*dz) < 250**2:
            return
            
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        
        # Trunk
        glColor3f(*self.trunkColor)
        glPushMatrix()
        glTranslatef(0, self.height/2, 0)
        glScalef(self.thickness, self.height, self.thickness)
        glutSolidCube(1)
        glPopMatrix()
        
        # Canopy (Leaves)
        glColor3f(*self.leafColor)
        glPushMatrix()
        glTranslatef(0, self.height, 0)
        # Main sphere
        glutSolidSphere(self.thickness * 2.5, 10, 10)
        # Side spheres for organic look
        glPushMatrix(); glTranslatef(15, -10, 10); glutSolidSphere(self.thickness * 1.5, 8, 8); glPopMatrix()
        glPushMatrix(); glTranslatef(-15, -10, -10); glutSolidSphere(self.thickness * 1.5, 8, 8); glPopMatrix()
        glPopMatrix()
        
        glPopMatrix()

# Base class for all floor types. Builds a grid of tiles centered on the origin.
# self.positions tracks (row, col) pairs not yet assigned to special objects —
# used as a spawn pool to guarantee no two features overlap.
class Tileset:
    def __init__(self, rows, columns, tile):
        self.tiles = []
        self.positions = [(r, c) for r in range(rows) for c in range(columns)]

        floorLength = rows * Tile.length
        floorWidth = columns * Tile.width

        originX = 0
        originZ = 0

        self.startX = originX - floorLength / 2
        self.startZ = originZ - floorWidth / 2

        currentX = self.startX
        currentZ = self.startZ

        for r in range(rows):
            row = []
            for c in range(columns):
                tileX = currentX + Tile.length/2
                tileZ = currentZ + Tile.width/2
                t = tile(tileX, tileZ)
                row.append(t)
                currentX += Tile.length
            self.tiles.append(row)
            currentX = self.startX
            currentZ += Tile.width

    def getClampedPosition(self, x, z):
        rows = len(self.tiles)
        cols = len(self.tiles[0])
        # Small buffer to prevent the player from standing on the very edge
        buffer = 15 
        minX = self.startX + buffer
        maxX = self.startX + (cols * Tile.length) - buffer
        minZ = self.startZ + buffer
        maxZ = self.startZ + (rows * Tile.width) - buffer
        return max(minX, min(maxX, x)), max(minZ, min(maxZ, z))

    def getTile(self, x, z):
        col = int((x - self.startX) / Tile.length)
        row = int((z - self.startZ) / Tile.width)

        if 0 <= row < len(self.tiles) and 0 <= col < len(self.tiles[0]):
            return self.tiles[row][col]
        return None

    def popRandomPosition(self):
        randomIndex = random.randrange(len(self.positions))
        return self.positions.pop(randomIndex)
    
    def changeTile(self, r, c, newTile):
        oldTile = self.tiles[r][c]
        self.tiles[r][c] = newTile(oldTile.x, oldTile.z)
    
    def spawnObject(self, r, c, obj):
        tile = self.tiles[r][c]
        tile.spawnObject(obj)

    def getAdjacentTiles(self, tile):
        col = int((tile.x - self.startX) / Tile.length)
        row = int((tile.z - self.startZ) / Tile.width)
        adj = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < len(self.tiles) and 0 <= nc < len(self.tiles[0]):
                    adj.append(self.tiles[nr][nc])
        return adj

    def draw(self):
        for row in self.tiles:
            for tile in row:
                tile.draw()

class Homebase(Tileset):
    homeDuration = 15
    originPortal = None
    enterTime = None

    def __init__(self, rows, columns):
        super().__init__(rows, columns, HomeTile)

    def enter(self, portal):
        Floor.current = Floor.homebase
        self.originPortal = portal
        self.enterTime = time.time()
        Player.x = 0
        Player.z = 0
        
        # Refills
        Player.health = Player.maxHealth
        Gun.currentAmmo = Gun.maxAmmo
        DayNightManager.lastVisitedDay = DayNightManager.dayCount
        
        Notifications.add("HOMEBASE ACCESSED: GEAR RESTOCKED & HEALTH RESTORED")
        DelayedAction(self.homeDuration, self.exit)
    
    def exit(self):
        if Floor.current != Floor.homebase: return
        Floor.current = Floor.wasteland
        Player.x = self.originPortal.x
        Player.z = self.originPortal.z
        self.originPortal = None
        self.enterTime = None
        PortalTile.disable()

class Wasteland(Tileset):
    def __init__(self, rows, columns):
        super().__init__(rows, columns, tile=WastelandTile)

        self.acidPositions = []
        self.waterPositions = []
        self.treePositions = []
        
        acidTileCount = int(rows * columns * 0.1)
        for t in range(acidTileCount):
            self.acidPositions.append(self.popRandomPosition())

        waterTileCount = random.randint(5, 10)
        for t in range(waterTileCount):
            self.waterPositions.append(self.popRandomPosition())

        treeTileCount = random.randint(10, 20)
        for t in range(treeTileCount):
            self.treePositions.append(self.popRandomPosition())

        # Claim positions in random order so features never overlap 
        self.portalPosition = self.popRandomPosition()
        self.spaceshipPosition = self.popRandomPosition()
        self.chestPosition = self.popRandomPosition()

        for r, c in self.waterPositions: self.changeTile(r, c, WaterTile)
        for r, c in self.acidPositions: self.changeTile(r, c, AcidTile)
        for r, c in self.treePositions: self.changeTile(r, c, TreeTile)

        self.changeTile(*self.portalPosition, PortalTile)
        self.spawnObject(*self.spaceshipPosition, Spaceship)
        self.spawnObject(*self.chestPosition, Chest)

class Floor:
    homebase = None
    wasteland = None
    current = None
    
    @classmethod
    def draw(cls): 
        cls.current.draw()

    @classmethod
    def getTile(cls, x, z):
        return cls.current.getTile(x, z)

# =============================================================================
# PLAYER — Logic and Rendering
# =============================================================================

# Separated from Player so Player only contains state and movement logic.
# All tunable render constants (offsets, colors, sizes) live here.
# Gun muzzle position is replicated in Gun.shoot() — keep both in sync
# if render constants change.
class PlayerRenderer:
    # Tunable render settings
    legColor = [0.08, 0.12, 0.35]
    bodyColor = [0.50, 0.10, 0.18]
    handColor = (0.8, 0.5, 0.25)
    headColor = (0.0, 0.0, 0.0)
    gunColor = (0.35, 0.35, 0.35)
    gunHandleColor = (0.2, 0.2, 0.2)

    legXOffsetFactor = 0.25
    handYDivisor = 1.4
    gunXOffset = -20
    gunYDivisor = 1.2
    gunZOffsetFactor = 0.5
    gunHandleXOffset = 0
    gunHandleYOffset = -12
    gunHandleZOffset = 10

    cylinderSlices = 10
    cylinderStacks = 10
    headSlices = 20
    headStacks = 20

    @classmethod
    def draw(cls, player):
        if player.mode == "human":
            cls.drawHuman(player)
        else:
            cls.drawSpaceship(player)

    @classmethod
    def drawHuman(cls, player):
        glPushMatrix()
        glTranslatef(player.x, 0, player.z)
        glRotatef(player.angle, 0, 1, 0) 

        legXOffset = player.bodyWidth * cls.legXOffsetFactor
        handY = player.legHeight + (player.bodyHeight / cls.handYDivisor)
        gunY = player.legHeight + (player.bodyHeight / cls.gunYDivisor)
        gunZ = player.bodyWidth * cls.gunZOffsetFactor

        glColor3f(*cls.legColor)
        glPushMatrix()
        glTranslatef(-legXOffset, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), player.legBottomWidth / 2, player.legBaseWidth / 2, player.legHeight, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()

        glColor3f(*cls.legColor)
        glPushMatrix()
        glTranslatef(legXOffset, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), player.legBottomWidth / 2, player.legBaseWidth / 2, player.legHeight, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()

        glColor3f(*cls.bodyColor)
        glPushMatrix()
        glTranslatef(0, player.legHeight + player.bodyHeight / 2, 0)
        glScalef(player.bodyWidth, player.bodyHeight, player.bodyThickness)
        glutSolidCube(1)
        glPopMatrix()

        glColor3f(*cls.handColor)
        glPushMatrix()
        glTranslatef(player.bodyWidth/2 - player.handBaseRadius, handY, 0)
        gluCylinder(gluNewQuadric(), player.handBaseRadius, player.handTopRadius, player.handLength, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()

        glColor3f(*cls.handColor)
        glPushMatrix()
        glTranslatef(-player.bodyWidth/2 + player.handBaseRadius, handY, 0)
        gluCylinder(gluNewQuadric(), player.handBaseRadius, player.handTopRadius, player.handLength, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()

        glColor3f(*cls.headColor)
        glPushMatrix()
        glTranslatef(0, player.legHeight + player.bodyHeight + player.headRadius, 0)
        glutSolidSphere(player.headRadius, cls.headSlices, cls.headStacks)
        glPopMatrix()

        glColor3f(*cls.gunColor)
        glPushMatrix()
        glTranslatef(cls.gunXOffset, gunY, gunZ)
        gluCylinder(gluNewQuadric(), player.gunBaseRadius, player.gunTopRadius, player.gunLength, cls.cylinderSlices, cls.cylinderStacks)

        glColor3f(*cls.gunHandleColor)
        glPushMatrix()
        glTranslatef(cls.gunHandleXOffset, cls.gunHandleYOffset, cls.gunHandleZOffset)
        glScalef(player.gunHandleWidth, player.gunHandleHeight, player.gunHandleThickness)
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()
        glPopMatrix()

    @classmethod
    def drawSpaceship(cls, player):
        glPushMatrix()
        # Hover effect
        hoverY = 40 + math.sin(time.time() * 3) * 15
        glTranslatef(player.x, hoverY, player.z)
        glRotatef(player.angle, 0, 1, 0)

        # Main Body
        glColor3f(0.5, 0.5, 0.5) # Silver
        glPushMatrix()
        glScalef(3.0, 0.6, 3.0)
        glutSolidSphere(40, 20, 20)
        glPopMatrix()

        # Cockpit Dome
        glColor3f(0.0, 0.8, 1.0) # Cyan
        glPushMatrix()
        glTranslatef(0, 18, 0)
        glScalef(1.0, 1.3, 1.0)
        glutSolidSphere(25, 20, 20)
        glPopMatrix()

        # Front Indicator
        glPushMatrix()
        glTranslatef(0, 5, 120) 
        glColor3f(1.0, 0.5, 0.0)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()

        glPopMatrix()

class Player:
    # --- Body dimensions (used by PlayerRenderer) ---
    headRadius = 25
    bodyWidth = 65
    bodyThickness = 35
    bodyHeight = 90
    handLength = 60
    handBaseRadius = 10
    handTopRadius = 5
    legHeight = 50
    legBottomWidth = 40
    legBaseWidth = 25

    gunBaseRadius = 5
    gunTopRadius = 5
    gunLength = 50
    gunHandleWidth = 8
    gunHandleHeight = 24
    gunHandleThickness = 10

    # --- Stats ---
    x = 0
    z = 0
    angle = 0
    walkSpeed = 15
    turnSpeed = 3
    health = 100
    maxHealth = 100
    food = 0
    keys = 0
    immunity = 0
    
    # --- Vehicle ---
    mode = "human" # "human" or "spaceship"
    saucerHealth = 300
    maxSaucerHealth = 300
    saucerSpeed = 45

    @classmethod
    def exitSpaceship(cls):
        if cls.mode == "spaceship":
            currentTile = Floor.getTile(cls.x, cls.z)
            if not currentTile: return
            
            # Find adjacent walkable tile for the vessel
            adj = Floor.wasteland.getAdjacentTiles(currentTile)
            targetTile = None
            for t in adj:
                if t.isWalkable and t.object is None:
                    targetTile = t
                    break
                
            if targetTile:
                targetTile.spawnObject(lambda x, z: Spaceship(x, z, health=cls.saucerHealth))
                # Sync with wasteland positions
                col = int((targetTile.x - Floor.wasteland.startX) / Tile.length)
                row = int((targetTile.z - Floor.wasteland.startZ) / Tile.width)
                if (row, col) in Floor.wasteland.positions:
                    Floor.wasteland.positions.remove((row, col))
                cls.mode = "human"

    @classmethod
    def triggerTile(cls):
        tile = Floor.getTile(cls.x, cls.z)
        if tile: tile.trigger()

    @classmethod
    def draw(cls):
        PlayerRenderer.draw(cls)

    @classmethod
    def moveForward(cls):
        speed = cls.walkSpeed if cls.mode == "human" else cls.saucerSpeed
        rad = math.radians(cls.angle)
        nextX = cls.x + speed * math.sin(rad)
        nextZ = cls.z + speed * math.cos(rad)
        
        # Clamp to floor boundary
        nextX, nextZ = Floor.current.getClampedPosition(nextX, nextZ)
        
        targetTile = Floor.getTile(nextX, nextZ)
        if targetTile and not targetTile.isWalkable:
            return
            
        cls.x = nextX
        cls.z = nextZ

    @classmethod
    def moveBackward(cls):
        speed = cls.walkSpeed if cls.mode == "human" else cls.saucerSpeed
        rad = math.radians(cls.angle)
        nextX = cls.x - speed * math.sin(rad)
        nextZ = cls.z - speed * math.cos(rad)
        
        # Clamp to floor boundary
        nextX, nextZ = Floor.current.getClampedPosition(nextX, nextZ)
        
        targetTile = Floor.getTile(nextX, nextZ)
        if targetTile and not targetTile.isWalkable:
            return

        cls.x = nextX
        cls.z = nextZ

    @classmethod
    def turnLeft(cls):
        cls.angle += cls.turnSpeed

    @classmethod
    def turnRight(cls):
        cls.angle -= cls.turnSpeed

    @classmethod
    def heal(cls, amount):
        cls.health = min(cls.maxHealth, cls.health + amount)

    @classmethod
    def addFood(cls, amount):
        cls.food += amount

    @classmethod
    def addImmunity(cls, amount):
        cls.immunity += amount

    @classmethod
    def useKey(cls):
        if cls.keys > 0:
            cls.keys -= 1
            return True
        return False

class Gun:
    maxAmmo = 30
    currentAmmo = 30

    @classmethod
    def shoot(cls):
        if Player.mode == "spaceship": return
        if cls.currentAmmo > 0:
            rad = math.radians(Player.angle)
            gunY = Player.legHeight + (Player.bodyHeight / PlayerRenderer.gunYDivisor)
            gunZLocal = (Player.bodyWidth * PlayerRenderer.gunZOffsetFactor) + Player.gunLength
            muzzleX = Player.x + (PlayerRenderer.gunXOffset * math.cos(rad)) + (gunZLocal * math.sin(rad))
            muzzleZ = Player.z - (PlayerRenderer.gunXOffset * math.sin(rad)) + (gunZLocal * math.cos(rad))

            Bullet(muzzleX, gunY, muzzleZ, Player.angle, damage=20)
            cls.currentAmmo -= 1

    @classmethod
    def addAmmo(cls, amount):
        cls.currentAmmo = min(cls.maxAmmo, cls.currentAmmo + amount)

# =============================================================================
# PICKUPS — Items and Containers
# =============================================================================

class Pickup:
    minimapColor = (0.9, 0.3, 0.6)
    def __init__(self, x, z, color=(1,1,1), y=50):
        self.x = x
        self.z = z
        self.y = y
        self.color = color

    def draw_start(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        angle = (time.time() * 100) % 360
        glRotatef(angle, 0, 1, 0)
        glColor3f(*self.color)

    def draw_end(self):
        glPopMatrix()

    def draw(self):
        pass

    def apply(self, player):
        return False

class HealthPack(Pickup):
    def __init__(self, x, z):
        super().__init__(x, z, color=(1, 1, 1))
        self.crossColor = (1, 0, 0)
    
    def draw(self):
        self.draw_start()
        glColor3f(*self.crossColor)
        glPushMatrix(); glScalef(0.25, 1.0, 0.25); glutSolidCube(60); glPopMatrix()
        glPushMatrix(); glScalef(1.0, 0.25, 0.25); glutSolidCube(60); glPopMatrix()
        self.draw_end()

    def apply(self, player):
        if player.health < player.maxHealth:
            player.heal(25)
            Notifications.add("HEALTH PACK RETRIEVED (+25)")
            return True
        Notifications.add("HEALTH IS ALREADY FULL")
        return False

class ShieldPack(Pickup):
    def __init__(self, x, z):
        super().__init__(x, z, color=(0.2, 0.8, 1.0), y=60)
        
    def draw(self):
        self.draw_start()
        glScalef(0.8, 2.5, 1.8)
        glutSolidSphere(20, 15, 15)
        self.draw_end()
        
    def apply(self, player):
        player.addImmunity(600)
        Notifications.add("SHIELD PACK RETRIEVED")
        return True

class AmmoPack(Pickup):
    def __init__(self, x, z):
        super().__init__(x, z, color=(0.2, 0.2, 0.2))
        self.tipColor = (0.8, 0.6, 0.2)
    
    def draw(self):
        self.draw_start()
        glTranslatef(0, 0, -35) 
        gluCylinder(gluNewQuadric(), 15, 15, 25, 10, 10)
        glPushMatrix(); glScalef(1.0, 1.0, 0.3); glutSolidSphere(15, 10, 10); glPopMatrix()
        
        glTranslatef(0, 0, 25)
        glColor3f(*self.tipColor) 
        gluCylinder(gluNewQuadric(), 15, 15, 25, 10, 10)
        glTranslatef(0, 0, 25)
        gluCylinder(gluNewQuadric(), 15, 0, 20, 10, 10)
        self.draw_end()

    def apply(self, player):
        if Gun.currentAmmo < Gun.maxAmmo:
            Gun.addAmmo(10)
            Notifications.add("AMMO PACK RETRIEVED (+10)")
            return True
        Notifications.add("AMMO CAPACITY FULL")
        return False

class FoodPack(Pickup):
    def __init__(self, x, z):
        super().__init__(x, z, color=(0.2, 0.8, 0.2))
    
    def draw(self):
        self.draw_start()
        glutSolidSphere(25, 12, 12)
        self.draw_end()

    def apply(self, player):
        player.addFood(1)
        Notifications.add("BIOMASS PACK RETRIEVED")
        return True

class Key(Pickup):
    def __init__(self, x, z):
        super().__init__(x, z, color=(0.8, 0.6, 0.2)) # Gold
    
    def draw(self):
        self.draw_start()
        glPushMatrix(); glTranslatef(0, 0, -10); glScalef(0.2, 0.2, 1.0); glutSolidCube(40); glPopMatrix()
        glPushMatrix(); glTranslatef(0, 0, 15); glutSolidSphere(8, 10, 10); glPopMatrix()
        self.draw_end()

    def apply(self, player):
        player.keys += 1
        Notifications.add("ACCESS KEY RETRIEVED")
        return True

class Chest(Pickup):
    minimapColor = (0.4, 0.2, 0.1)
    def __init__(self, x, z):
        super().__init__(x, z, color=(0.4, 0.2, 0.1))
        self.lockColor = (0.8, 0.6, 0.2)
    
    def draw(self):
        self.draw_start()
        glPushMatrix(); glScalef(1.5, 1.0, 1.0); glutSolidCube(40); glPopMatrix()
        glPushMatrix(); glTranslatef(0, 0, 20); glColor3f(*self.lockColor); glutSolidCube(8); glPopMatrix()
        self.draw_end()

    def apply(self, player):
        if player.useKey():
            player.addImmunity(200)
            options = []
            if player.health < player.maxHealth: options.append('hp')
            if Gun.currentAmmo < Gun.maxAmmo: options.append('ammo')
            options.extend(['food', 'shield']) # Always valid backups
            
            reward = random.choice(options)
            if reward == 'hp': 
                player.heal(50)
                Notifications.add("CHEST REWARD: HEALTH REPLENISHED")
            elif reward == 'ammo': 
                Gun.currentAmmo = min(Gun.maxAmmo, Gun.currentAmmo + 20)
                Notifications.add("CHEST REWARD: AMMO RESTOCKED")
            elif reward == 'food': 
                player.addFood(3)
                Notifications.add("CHEST REWARD: BIOMASS BOOST")
            elif reward == 'shield': 
                player.addImmunity(600)
                Notifications.add("CHEST REWARD: SHIELD OVERCHARGE")
            
            Game.spawnNewChest()
            return True
        Notifications.add("CHEST IS LOCKED: REQUIRES ACCESS KEY")
        return False

class Spaceship:
    minimapColor = (0.5, 0.0, 0.7)
    def __init__(self, x, z, health=None):
        self.x = x
        self.z = z
        self.y = 50
        self.health = health if health is not None else Player.maxSaucerHealth
    
    def draw(self):
        glPushMatrix()
        hoverY = self.y + math.sin(time.time() * 2) * 10
        glTranslatef(self.x, hoverY, self.z)
        glScalef(0.4, 0.4, 0.4)
        
        glColor3f(0.6, 0.6, 0.6)
        glPushMatrix()
        glScalef(3.0, 0.6, 3.0)
        glutSolidSphere(40, 15, 15)
        glPopMatrix()
        
        glColor3f(0.0, 0.8, 1.0)
        glPushMatrix()
        glTranslatef(0, 15, 0)
        glScalef(1.0, 1.3, 1.0)
        glutSolidSphere(20, 15, 15)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 5, 120)
        glColor3f(1.0, 0.5, 0.0)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()
        
        glPopMatrix()

    def apply(self, player):
        player.mode = "spaceship"
        player.saucerHealth = self.health
        
        # Put the position back in the pool
        col = int((self.x - Floor.wasteland.startX) / Tile.length)
        row = int((self.z - Floor.wasteland.startZ) / Tile.width)
        pos = (row, col)
        if pos not in Floor.wasteland.positions:
            Floor.wasteland.positions.append(pos)
        return True

# =============================================================================
# ENEMIES — AI and Combat
# =============================================================================

# team="player" bullets damage enemies; team="enemy" bullets damage the player.
# All bullets live in Game.bullets regardless of team.
class Bullet:
    def __init__(self, x, y, z, angle, damage=10, speed=15, radius=4, color=(1, 0.9, 0.2), team="player"):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle
        self.damage = damage
        self.speed = speed
        self.radius = radius
        self.color = color
        self.team = team
        self.life = 100
        Game.bullets.append(self)

    def update(self):
        rad = math.radians(self.angle)
        self.x += self.speed * math.sin(rad)
        self.z += self.speed * math.cos(rad)
        self.life -= 1
        
        tile = Floor.getTile(self.x, self.z)
        if tile and not tile.isWalkable:
            self.life = 0
            return

        if self.team == "player":
            for enemy in EnemyManager.enemies:
                dx = self.x - enemy.x
                dz = self.z - enemy.z
                radius = 70 if isinstance(enemy, Tank) else 40  # Tank is a larger hit target
                if math.sqrt(dx*dx + dz*dz) < radius:
                    enemy.takeDamage(self.damage)
                    self.life = 0
                    break
        else:
            dx = self.x - Player.x
            dz = self.z - Player.z
            if math.sqrt(dx*dx + dz*dz) < 40 and abs(self.y - 50) < 50:
                if Player.immunity <= 0:
                    if Player.mode == "human": Player.health -= self.damage
                    else: Player.saucerHealth -= self.damage
                self.life = 0

    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glutSolidSphere(self.radius, 8, 8)
        glPopMatrix()

# Three-state AI: PATROL (random walk), CHASE (move toward player),
# ATTACK (subclass-defined). Transitions driven by distance each frame.
class Enemy:
    def __init__(self, x, z, health, speed, color):
        self.x = x
        self.z = z
        self.angle = 0
        self.health = health
        self.maxHealth = health
        self.speed = speed
        self.color = color
        
        # AI State
        self.state = "PATROL" # PATROL, CHASE, ATTACK
        self.detectionRange = 800 # Increased detection range
        self.attackRange = 60
        self.patrolTimer = 0
        self.patrolDir = [random.uniform(-1, 1), random.uniform(-1, 1)]

    def drawHealthBar(self):
        ratio = self.health / self.maxHealth
        glPushMatrix()
        # Move up above head
        glTranslatef(0, 130, 0) 
        
        # 1. Get camera position using the same math as Camera.setupCamera
        rad = -math.radians(Player.angle) - math.radians(Camera.angle)
        camX = Player.x + Camera.radius * math.cos(rad)
        camZ = Player.z + Camera.radius * math.sin(rad)
        
        # 2. Angle from enemy to camera
        dx = camX - self.x
        dz = camZ - self.z
        angleToCam = math.degrees(math.atan2(dx, dz))
        
        # 3. Rotate to face camera
        glRotatef(angleToCam, 0, 1, 0)
        
        # Background (Black)
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(-35, -5, 0); glVertex3f(35, -5, 0)
        glVertex3f(35, 5, 0); glVertex3f(-35, 5, 0)
        glEnd()
        
        # Health (Bright Green)
        glColor3f(0.0, 1.0, 0.3)
        glBegin(GL_QUADS)
        glVertex3f(-35, -5, 0.01); glVertex3f(-35 + (70 * ratio), -5, 0.01)
        glVertex3f(-35 + (70 * ratio), 5, 0.01); glVertex3f(-35, 5, 0.01)
        glEnd()
        glPopMatrix()

    def update(self):
        dx = Player.x - self.x
        dz = Player.z - self.z
        dist = math.sqrt(dx*dx + dz*dz)

        # Scale speed and detection range with difficulty, capped at 2.5x base values
        diff = DayNightManager.getDifficulty()
        scaledSpeed = min(self.speed * (1 + diff * 0.1), self.speed * 2.5)
        scaledRange = min(self.detectionRange * (1 + diff * 0.05), 1800)

        # State Transitions
        if dist < self.attackRange:
            self.state = "ATTACK"
        elif dist < scaledRange:
            self.state = "CHASE"
        else:
            self.state = "PATROL"

        nextX, nextZ = self.x, self.z

        if self.state == "PATROL":
            self.patrolTimer -= 1
            if self.patrolTimer <= 0:
                self.patrolDir = [random.uniform(-1, 1), random.uniform(-1, 1)]
                self.patrolTimer = random.randint(60, 120)
            
            nextX += self.patrolDir[0] * (scaledSpeed * 0.5)
            nextZ += self.patrolDir[1] * (scaledSpeed * 0.5)
            self.angle = math.degrees(math.atan2(self.patrolDir[0], self.patrolDir[1]))

        elif self.state == "CHASE":
            targetAngle = math.degrees(math.atan2(dx, dz))
            angleDiff = (targetAngle - self.angle + 180) % 360 - 180
            self.angle += angleDiff * 0.05
            rad = math.radians(self.angle)
            nextX += scaledSpeed * math.sin(rad)
            nextZ += scaledSpeed * math.cos(rad)

        elif self.state == "ATTACK":
            self.performAttack(dist)
            return # No movement in attack state for base enemy

        # Clamp to floor boundary
        nextX, nextZ = Floor.current.getClampedPosition(nextX, nextZ)

        # Collision check
        targetTile = Floor.getTile(nextX, nextZ)
        if targetTile and not targetTile.isWalkable:
            if self.state == "PATROL":
                self.patrolTimer = 0 # Redirect on collision
            return
            
        self.x, self.z = nextX, nextZ

    def performAttack(self, dist):
        # Default melee damage
        if Player.immunity <= 0:
            damagePool = "health" if Player.mode == "human" else "spaceship"
            if damagePool == "health":
                Player.health -= 0.3
            else:
                Player.saucerHealth -= 0.3

    def takeDamage(self, amount):
        self.health -= amount

class Mutant(Enemy):
    def __init__(self, x, z):
        super().__init__(x, z, health=50, speed=2.5, color=(0.3, 0.4, 0.2))
        self.eyeColor = (0.0, 1.0, 0.0)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        
        self.drawHealthBar()
        
        glRotatef(self.angle, 0, 1, 0)
        
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(0, 45, 0)
        glScalef(50, 70, 40)
        glutSolidCube(1)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 85, 15)
        glutSolidSphere(20, 10, 10)
        glColor3f(*self.eyeColor)
        glPushMatrix(); glTranslatef(-8, 5, 15); glutSolidSphere(4, 5, 5); glPopMatrix()
        glPushMatrix(); glTranslatef(8, 5, 15); glutSolidSphere(4, 5, 5); glPopMatrix()
        glPopMatrix()
        glPopMatrix()

class Wanderer(Enemy):
    def __init__(self, x, z):
        super().__init__(x, z, health=30, speed=1.5, color=(0.8, 0.5, 0.1))

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        self.drawHealthBar()
        glRotatef(self.angle, 0, 1, 0)
        
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(0, 20, 0)
        glScalef(60, 40, 40)
        glutSolidCube(1)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(5, 55, 10)
        glutSolidSphere(25, 10, 10)
        glPopMatrix()
        
        glPopMatrix()

class Shooter(Enemy):
    def __init__(self, x, z):
        super().__init__(x, z, health=40, speed=3.0, color=(0.6, 0.2, 0.2))
        self.attackRange = 500
        self.shootTimer = 0

    def performAttack(self, dist):
        dx = Player.x - self.x
        dz = Player.z - self.z
        self.angle = math.degrees(math.atan2(dx, dz))
        
        self.shootTimer -= 1
        if self.shootTimer <= 0:
            Bullet(self.x, 60, self.z, self.angle, damage=5, team="enemy")
            self.shootTimer = 60

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        self.drawHealthBar()
        glRotatef(self.angle, 0, 1, 0)
        
        glColor3f(*self.color)
        glPushMatrix(); glTranslatef(0, 50, 0); glScalef(25, 100, 25); glutSolidCube(1); glPopMatrix()
        glPushMatrix(); glTranslatef(0, 110, 0); glutSolidSphere(15, 10, 10); glPopMatrix()
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix(); glTranslatef(0, 60, 20); gluCylinder(gluNewQuadric(), 5, 5, 40, 8, 8); glPopMatrix()
        
        glPopMatrix()

class Tank(Enemy):
    def __init__(self, x, z):
        super().__init__(x, z, health=200, speed=0.8, color=(0.3, 0.3, 0.3))
        self.attackRange = 700
        self.shootTimer = 0

    def performAttack(self, dist):
        dx = Player.x - self.x
        dz = Player.z - self.z
        targetAngle = math.degrees(math.atan2(dx, dz))
        angleDiff = (targetAngle - self.angle + 180) % 360 - 180
        self.angle += angleDiff * 0.02
        
        self.shootTimer -= 1
        if self.shootTimer <= 0 and abs(angleDiff) < 5:
            rad = math.radians(self.angle)
            muzzleX = self.x + 80 * math.sin(rad)
            muzzleZ = self.z + 80 * math.cos(rad)
            
            Bullet(muzzleX, 70, muzzleZ, self.angle, damage=25, radius=12, color=(1.0, 0.6, 0.0), team="enemy")
            self.shootTimer = 150 # Slow fire rate for balance

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        self.drawHealthBar()
        glRotatef(self.angle, 0, 1, 0)
        
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(0, 30, 0)
        glScalef(100, 60, 100)
        glutSolidCube(1)
        glPopMatrix()
        
        glColor3f(0.2, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(0, 70, 0)
        glScalef(60, 40, 60)
        glutSolidCube(1)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0, 70, 40)
        glColor3f(0.1, 0.1, 0.1)
        gluCylinder(gluNewQuadric(), 10, 10, 40, 10, 10)
        glPopMatrix()
        
        glPopMatrix()

# Tanks always drop loot. Other enemies have a 30% base drop chance
# with type-weighted key probability.
class EnemyManager:
    enemies = []
    
    @classmethod
    def spawnEnemy(cls, x, z, kind="mutant"):
        if kind == "tank": e = Tank(x, z)
        elif kind == "shooter": e = Shooter(x, z)
        elif kind == "wanderer": e = Wanderer(x, z)
        else: e = Mutant(x, z)
        cls.enemies.append(e)
        
    @classmethod
    def update(cls):
        for e in cls.enemies[:]:
            e.update()
            if e.health <= 0:
                cls.enemies.remove(e)
                if isinstance(e, Tank):
                    tile = Floor.getTile(e.x, e.z)
                    if tile and tile.object is None:
                        item = Key if random.random() < 0.5 else ShieldPack
                        tile.spawnObject(item)
                        Notifications.add("TANK DESTROYED: LOOT DROPPED")
                else:
                    roll = random.random()
                    if roll < 0.30: # 30% chance to drop something
                        keyRoll = random.random()
                        keyChance = 0.01 # Mutant/Wanderer
                        if isinstance(e, Shooter): keyChance = 0.08
                        
                        if keyRoll < keyChance:
                            item = Key
                        else:
                            otherRoll = random.random()
                            if otherRoll < 0.50: item = AmmoPack
                            elif otherRoll < 0.85: item = FoodPack
                            else: item = ShieldPack
                        
                        tile = Floor.getTile(e.x, e.z)
                        if tile:
                            tile.spawnObject(item)
                            Notifications.add(f"ENEMY DROPPED {item.__name__.upper()}")

    @classmethod
    def draw(cls):
        for enemy in cls.enemies:
            enemy.draw()

# =============================================================================
# WORLD EVENTS — Hazards and Explosions
# =============================================================================

class Bomb:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 1000 # Start in the sky
        self.groundY = 30
        self.isFalling = True
        self.fallSpeed = 25
        
        self.fuseTime = 2.0
        self.startTime = None # Starts after landing
        self.blinkSpeed = 0.15
        self.affectedTiles = []
        tile = Floor.getTile(x, z)
        if tile:
            self.affectedTiles = Floor.current.getAdjacentTiles(tile)
            self.affectedTiles.append(tile)
        Game.bombs.append(self)

    def update(self):
        if self.isFalling:
            self.y -= self.fallSpeed
            if self.y <= self.groundY:
                self.y = self.groundY
                self.isFalling = False
                self.startTime = time.time()
            return

        elapsed = time.time() - self.startTime
        if elapsed >= self.fuseTime:
            Explosion(self.x, self.z, self.affectedTiles)
            if self in Game.bombs:
                Game.bombs.remove(self)

    def draw(self):
        isBlinkOn = False
        elapsed = 0
        
        if not self.isFalling and self.startTime:
            elapsed = time.time() - self.startTime
            isBlinkOn = (int(elapsed / self.blinkSpeed) % 2) == 0
        
        if not self.isFalling and isBlinkOn:
            for tile in self.affectedTiles:
                blinkColor = (1.0, tile.color[1], tile.color[2])
                glColor3f(*blinkColor)
                
                startX = tile.x - tile.length/2
                endX = startX + tile.length
                startZ = tile.z - tile.width/2
                endZ = startZ + tile.width
                
                glBegin(GL_QUADS)
                glVertex3f(startX, 2, startZ)
                glVertex3f(endX, 2, startZ)
                glVertex3f(endX, 2, endZ)
                glVertex3f(startX, 2, endZ)
                glEnd()

        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        scale = 1.0
        if not self.isFalling:
            scale = 1.0 + (elapsed / self.fuseTime) * 0.7 if isBlinkOn else 1.0
        glScalef(scale, scale, scale)
        
        glColor3f(0.1, 0.1, 0.1) # Black
        glutSolidSphere(20, 15, 15)
        
        if not self.isFalling and isBlinkOn:
            glColor3f(1, 1, 0)
            glPushMatrix()
            glTranslatef(0, 20, 0)
            glutSolidSphere(5, 8, 8)
            glPopMatrix()
            
        glPopMatrix()

class Explosion:
    def __init__(self, x, z, affectedTiles, maxRadius=350):
        self.x = x
        self.z = z
        self.y = 50
        self.affectedTiles = affectedTiles
        self.currentRadius = 0
        self.maxRadius = maxRadius
        self.growthSpeed = 15
        self.isFinished = False
        Game.explosions.append(self)

    def update(self):
        self.currentRadius += self.growthSpeed
        if self.currentRadius >= self.maxRadius:
            self.dealDamage()
            self.isFinished = True
            if self in Game.explosions:
                Game.explosions.remove(self)

    def dealDamage(self):
        playerTile = Floor.getTile(Player.x, Player.z)
        if playerTile in self.affectedTiles:
            damage = 50
            if Player.mode == "human": Player.health -= damage
            else: Player.saucerHealth -= damage
        
        for enemy in EnemyManager.enemies[:]:
            enemyTile = Floor.getTile(enemy.x, enemy.z)
            if enemyTile in self.affectedTiles:
                enemy.takeDamage(100)

    def draw(self):
        pulse = (math.sin(time.time() * 25) + 1) / 2
        r = 1.0
        g = 0.2 + 0.6 * pulse
        b = 0.0
        
        glColor3f(r, g, b)
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glutSolidSphere(self.currentRadius, 32, 32)
        
        glColor3f(1, 1, 1)
        glutSolidSphere(self.currentRadius * 0.6, 20, 20)
        
        glPopMatrix()

# =============================================================================
# GAME SYSTEMS — State and Timing
# =============================================================================

class DayNightManager:
    dayColor = numpy.array([0.72, 0.68, 0.38])
    nightColor = numpy.array([0.01, 0.00, 0.03])
    phaseDuration = 30
    startTime = time.time()
    dayCount = 1
    lastVisitedDay = 1  # Updated on homebase entry; missing a full cycle is instant death
    _lastCycle = 0

    @classmethod
    def getPhase(cls):
        elapsedTime = time.time() - cls.startTime
        fullCycleTime = cls.phaseDuration * 2
        
        cycle = int(elapsedTime / fullCycleTime)
        if cycle > cls._lastCycle:
            cls.dayCount += 1
            cls._lastCycle = cycle

        cycleTime = elapsedTime % fullCycleTime
        isNight = cycleTime >= cls.phaseDuration
        progress = (cycleTime % cls.phaseDuration) / cls.phaseDuration

        return isNight, progress
    
    @classmethod
    def getDifficulty(cls):
        return cls.dayCount + (cls.getDanger() * 2.0)

    # Returns 0.0 at dawn/dusk, 1.0 at full night/noon.
    # Used to scale difficulty and color the danger bar.
    @classmethod
    def getDanger(cls):
        isNight, progress = cls.getPhase()
        return progress if not isNight else (1.0 - progress)

    @classmethod
    def isDangerous(cls):
        return cls.getDanger() > 0.5

    @classmethod
    def updateSky(cls):
        isNight, progress = cls.getPhase()

        # Calculate brightness based on a sine wave that peaks at Noon (progress 0.5)
        # During the day (0.0 to 1.0), brightness goes 0 -> 1 -> 0
        brightness = 0
        if not isNight:
            brightness = math.sin(math.pi * progress)
        
        currentColor = cls.nightColor + (cls.dayColor - cls.nightColor) * brightness
        glClearColor(*currentColor, 1)

class GameState:
    MENU = 0
    CUSTOMIZE = 1
    PLAY = 2
    PAUSE = 3
    GAMEOVER = 4
    
    current = MENU

class Game:
    delayedActions = []
    bombs = []
    explosions = []
    bullets = []

    @classmethod
    def init(cls):
        Floor.homebase = Homebase(6, 6)
        Floor.wasteland = Wasteland(40, 40)
        Floor.current = Floor.wasteland

    @classmethod
    def restart(cls):
        # Reset Player
        Player.x = 0
        Player.z = 0
        Player.angle = 0
        Player.health = 100
        Player.food = 0
        Player.keys = 0
        Player.immunity = 0
        Player.mode = "human"
        Player.saucerHealth = Player.maxSaucerHealth
        
        # Reset Equipment
        Gun.currentAmmo = 20
        cls.bullets = []

        # Reset Camera
        Camera.angle = 90
        Camera.height = 500
        Camera.radius = 700
        
        # Reset DayNight
        DayNightManager.dayCount = 1
        DayNightManager.startTime = time.time()
        DayNightManager._lastCycle = 0
        DayNightManager.lastVisitedDay = 1
        
        # Reset Entities
        EnemyManager.enemies = []
        cls.bombs = []
        cls.explosions = []
        cls.delayedActions = []

        # Reset Systems & UI
        Notifications.active = {}
        UIManager.minimapZoomedIn = True
        Debug.enabled = False
        
        # Regenerate World
        PortalTile.isActive = True
        Floor.homebase = Homebase(6, 6)
        Floor.wasteland = Wasteland(40, 40)
        Floor.current = Floor.wasteland
        
        GameState.current = GameState.PLAY

    @classmethod
    def update(cls):
        for d in cls.delayedActions[:]: d.update()
        
        if GameState.current == GameState.PLAY:
            if Player.immunity > 0:
                Player.immunity -= 1
            
            # Instant kill if player skips a full day/night cycle without visiting homebase
            if Floor.current != Floor.homebase:
                if DayNightManager.dayCount > DayNightManager.lastVisitedDay + 1:
                    Player.health = 0
                    Notifications.add("CRITICAL FAILURE: MISSED MANDATORY DEPLOYMENT")
        
        if Floor.current == Floor.wasteland:
            for b in cls.bombs[:]: b.update()
            for e in cls.explosions[:]: e.update()
            for bullet in cls.bullets[:]:
                bullet.update()
                if bullet.life <= 0:
                    cls.bullets.remove(bullet)
            EnemyManager.update()
            
        if Player.mode == "spaceship" and Player.saucerHealth <= 0:
            Player.mode = "human"

        Player.triggerTile()
        
        if GameState.current == GameState.PLAY and Floor.current != Floor.homebase:
            diff = DayNightManager.getDifficulty()
            
            if random.random() < 0.002 * diff:
                cls.spawnRandomBomb()
                
            enemyCap = 5 + int(diff * 2)
            if len(EnemyManager.enemies) < enemyCap:
                if random.random() < 0.005 * diff:
                    cls.spawnRandomEnemy()

    @classmethod
    def spawnRandomEnemy(cls):
        dist = random.randint(800, 1500)
        angle = random.uniform(0, 2 * math.pi)
        ex = Player.x + dist * math.cos(angle)
        ez = Player.z + dist * math.sin(angle)
        
        diff = DayNightManager.getDifficulty()
        types = ["mutant", "wanderer"]
        if diff > 2: types.append("shooter")
        if diff > 4: types.append("tank")
        
        etype = random.choice(types)
        EnemyManager.spawnEnemy(ex, ez, etype)

    @classmethod
    def spawnNewChest(cls):
        wasteland = Floor.wasteland
        newPosition = wasteland.popRandomPosition()
        wasteland.positions.append(wasteland.chestPosition)
        wasteland.chestPosition = newPosition
        r, c = newPosition
        wasteland.spawnObject(r, c, Chest)

    @classmethod
    def spawnRandomBomb(cls):
        tiles = Floor.current.tiles
        rows = len(tiles)
        cols = len(tiles[0])
        for _ in range(10): # Guard against infinite loop
            r = random.randint(0, rows-1)
            c = random.randint(0, cols-1)
            targetTile = tiles[r][c]
            
            if targetTile.isWalkable:
                Bomb(targetTile.x, targetTile.z)
                break

# =============================================================================
# UI — Heads-Up Display and Menus
# =============================================================================

class UIManager:
    minimapZoomedIn = True
    
    @staticmethod
    def drawText(x, y, text, color=(1, 1, 1)):
        glColor3f(*color)
        glRasterPos2f(x, y)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

    @staticmethod
    def drawBar(x, y, width, height, progress, barColor, bgColor=(0.2, 0.2, 0.2)):
        glColor3f(*bgColor)
        glBegin(GL_QUADS)
        glVertex2f(x, y); glVertex2f(x + width, y)
        glVertex2f(x + width, y + height); glVertex2f(x, y + height)
        glEnd()

        glColor3f(*barColor)
        glBegin(GL_QUADS)
        glVertex2f(x, y); glVertex2f(x + (width * progress), y)
        glVertex2f(x + (width * progress), y + height); glVertex2f(x, y + height)
        glEnd()

    @classmethod
    def draw(cls):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, Window.width, 0, Window.height)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)

        if GameState.current == GameState.MENU:
            cls.drawMenu()
        elif GameState.current == GameState.CUSTOMIZE:
            cls.drawCustomize()
        elif GameState.current == GameState.PLAY:
            cls.drawHUD()
        elif GameState.current == GameState.PAUSE:
            cls.drawPause()
        elif GameState.current == GameState.GAMEOVER:
            cls.drawGameOver()

        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    @classmethod
    def drawMenu(cls):
        glColor3f(0.1, 0.1, 0.1)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(Window.width, 0)
        glVertex2f(Window.width, Window.height); glVertex2f(0, Window.height)
        glEnd()
        
        cls.drawText(Window.width//2 - 100, Window.height//2 + 50, "WASTELAND ZERO", (1, 0.8, 0))
        cls.drawText(Window.width//2 - 120, Window.height//2 - 20, "PRESS ENTER TO START", (1, 1, 1))

    @classmethod
    def drawCustomize(cls):
        glColor3f(0.05, 0.05, 0.1)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(Window.width, 0)
        glVertex2f(Window.width, Window.height); glVertex2f(0, Window.height)
        glEnd()
        
        cls.drawText(50, Window.height - 100, "CUSTOMIZE PLAYER", (1, 0.8, 0))
        cls.drawText(50, Window.height - 150, "PRESS 1: CYCLE BODY COLOR", (1, 1, 1))
        cls.drawText(50, Window.height - 180, "PRESS 2: CYCLE LEG COLOR", (1, 1, 1))
        cls.drawText(50, Window.height - 250, "PRESS ENTER TO CONFIRM", (0, 1, 0.5))
        
        cls.drawText(Window.width - 300, Window.height - 150, "BODY COLOR")
        glColor3f(*PlayerRenderer.bodyColor)
        glBegin(GL_QUADS)
        glVertex2f(Window.width - 300, Window.height - 200); glVertex2f(Window.width - 200, Window.height - 200)
        glVertex2f(Window.width - 200, Window.height - 240); glVertex2f(Window.width - 300, Window.height - 240)
        glEnd()
        
        cls.drawText(Window.width - 300, Window.height - 280, "LEG COLOR")
        glColor3f(*PlayerRenderer.legColor)
        glBegin(GL_QUADS)
        glVertex2f(Window.width - 300, Window.height - 330); glVertex2f(Window.width - 200, Window.height - 330)
        glVertex2f(Window.width - 200, Window.height - 370); glVertex2f(Window.width - 300, Window.height - 370)
        glEnd()

    @classmethod
    def drawMinimap(cls):
        w = Floor.wasteland
        rows = len(w.tiles)
        cols = len(w.tiles[0])
        
        cellSize = 8 if cls.minimapZoomedIn else 4
        viewRadius = 7
        gridSize = (viewRadius * 2 + 1) if cls.minimapZoomedIn else cols
        
        mapWidth = gridSize * cellSize
        mapHeight = gridSize * cellSize
        offsetX = Window.width - mapWidth - 25
        offsetY = 25
        
        glColor3f(0.05, 0.05, 0.05)
        glBegin(GL_QUADS)
        glVertex2f(offsetX - 5, offsetY - 5); glVertex2f(offsetX + mapWidth + 5, offsetY - 5)
        glVertex2f(offsetX + mapWidth + 5, offsetY + mapHeight + 5); glVertex2f(offsetX - 5, offsetY + mapHeight + 5)
        glEnd()

        pCol = int((Player.x - w.startX) / Tile.length)
        pRow = int((Player.z - w.startZ) / Tile.width)

        if cls.minimapZoomedIn:
            rRange = range(pRow - viewRadius, pRow + viewRadius + 1)
            cRange = range(pCol - viewRadius, pCol + viewRadius + 1)
        else:
            rRange = range(rows)
            cRange = range(cols)

        for i, r in enumerate(rRange):
            for j, c in enumerate(cRange):
                if 0 <= r < rows and 0 <= c < cols:
                    tile = w.tiles[r][c]
                    color = tile.minimapColor
                    
                    if tile.object:
                        color = getattr(tile.object, 'minimapColor', color)
                    
                    glColor3f(*color)
                    glBegin(GL_QUADS)
                    x = offsetX + j * cellSize
                    y = offsetY + i * cellSize
                    glVertex2f(x, y); glVertex2f(x + cellSize, y)
                    glVertex2f(x + cellSize, y + cellSize); glVertex2f(x, y + cellSize)
                    glEnd()

        def getMapPos(wx, wz):
            if cls.minimapZoomedIn:
                rx = (wx - Player.x) / Tile.length
                rz = (wz - Player.z) / Tile.width
                mx = offsetX + (viewRadius + rx) * cellSize + cellSize/2
                my = offsetY + (viewRadius + rz) * cellSize + cellSize/2
                return mx, my
            else:
                mx = offsetX + ((wx - w.startX) / (cols * Tile.length)) * mapWidth
                my = offsetY + ((wz - w.startZ) / (rows * Tile.width)) * mapHeight
                return mx, my

        glPointSize(4 if cls.minimapZoomedIn else 3)
        glBegin(GL_POINTS)
        glColor3f(1.0, 0.0, 0.0)
        for e in EnemyManager.enemies:
            mx, my = getMapPos(e.x, e.z)
            if offsetX <= mx <= offsetX + mapWidth and offsetY <= my <= offsetY + mapHeight:
                glVertex2f(mx, my)
        
        glColor3f(1.0, 1.0, 1.0)
        px, py = getMapPos(Player.x, Player.z)
        glVertex2f(px, py)
        glEnd()
        
        cls.drawText(offsetX, offsetY + mapHeight + 10, f"MAP: {'LOCAL' if cls.minimapZoomedIn else 'GLOBAL'} [M]", (0.7, 0.7, 0.7))

    @classmethod
    def drawHUD(cls):
        isSpaceship = Player.mode == "spaceship"
        if isSpaceship:
            hpLabel = "VESSEL HP"
            hpColor = (0.2, 0.8, 1.0)
            hpProgress = Player.saucerHealth / Player.maxSaucerHealth
            hpText = f"{int(Player.saucerHealth)} / {Player.maxSaucerHealth}"
        else:
            hpLabel = "SURVIVOR HP"
            hpColor = (0.9, 0.1, 0.1)
            hpProgress = Player.health / Player.maxHealth
            hpText = f"{int(Player.health)} / {Player.maxHealth}"
        
        cls.drawText(20, Window.height - 35, hpLabel, (1, 0.8, 0))
        cls.drawBar(20, Window.height - 55, 200, 15, hpProgress, hpColor)
        cls.drawText(20, Window.height - 70, hpText, (1, 1, 1))

        foodLimit = 10
        foodProgress = min(1.0, Player.food / foodLimit)
        cls.drawText(20, Window.height - 90, "BIOMASS RESERVE", (0.2, 0.9, 0.2))
        cls.drawBar(20, Window.height - 110, 200, 10, foodProgress, (0.1, 0.8, 0.1))
        
        if Player.immunity > 0:
            shieldProgress = min(1.0, Player.immunity / 600)
            cls.drawText(20, Window.height - 145, "SHIELD CHARGE", (0.4, 0.6, 1.0))
            cls.drawBar(20, Window.height - 160, 200, 8, shieldProgress, (0.2, 0.5, 1.0))

        ammoProgress = Gun.currentAmmo / Gun.maxAmmo
        cls.drawText(Window.width - 200, Window.height - 35, "AMMO CAPACITY", (0.8, 0.7, 0))
        cls.drawBar(Window.width - 200, Window.height - 55, 180, 12, ammoProgress, (0.7, 0.5, 0.1))
        cls.drawText(Window.width - 200, Window.height - 70, f"{Gun.currentAmmo} / {Gun.maxAmmo}")

        cls.drawText(Window.width - 200, Window.height - 90, f"ACCESS KEYS: {Player.keys}", (1, 1, 1))

        cls.drawText(Window.width//2 - 40, Window.height - 40, f"DAY {DayNightManager.dayCount}", (1, 1, 1))

        isNight, _ = DayNightManager.getPhase()
        danger = DayNightManager.getDanger()
        dangerColor = (1, 0.1, 0) if DayNightManager.isDangerous() else (1, 0.6, 0)
        
        phaseText = "NIGHTFALL" if isNight else "SOLAR"
        cls.drawText(20, 55, f"PHASE: {phaseText}", (1, 1, 1))
        cls.drawBar(20, 35, 200, 12, danger, dangerColor)
        cls.drawText(20, 20, "DANGER LEVEL", dangerColor)

        if isSpaceship:
            cls.drawText(Window.width//2 - 100, 100, "PRESS [Q] TO LAND VESSEL", (1, 0.5, 0))
        elif Player.mode == "human" and Gun.currentAmmo == 0:
            cls.drawText(Window.width//2 - 100, 100, "OUT OF AMMO! FIND PACKS", (1, 0, 0))

        if Floor.current == Floor.wasteland:
            cls.drawMinimap()
        elif Floor.current == Floor.homebase:
            elapsed = time.time() - Floor.homebase.enterTime
            remaining = max(0, Floor.homebase.homeDuration - elapsed)
            progress = remaining / Floor.homebase.homeDuration
            
            barWidth = 300
            barHeight = 15
            bx = (Window.width - barWidth) // 2
            by = 40
            
            cls.drawText(bx, by + 20, "TIME UNTIL DEPLOYMENT", (0.8, 0.8, 0.2))
            cls.drawBar(bx, by, barWidth, barHeight, progress, (0.7, 0.7, 0.1))
            cls.drawText(bx + barWidth + 10, by, "PRESS [Q] TO LEAVE EARLY", (0.6, 0.6, 0.6))

        Notifications.draw()

    @classmethod
    def drawPause(cls):
        cls.drawHUD()
        cls.drawText(Window.width//2 - 50, Window.height//2, "PAUSED", (1, 1, 0))
        cls.drawText(Window.width//2 - 80, Window.height//2 - 30, "PRESS P TO RESUME", (1, 1, 1))
        cls.drawText(Window.width//2 - 80, Window.height//2 - 60, "PRESS C TO CUSTOMIZE", (1, 1, 1))

    @classmethod
    def drawGameOver(cls):
        glColor3f(0.2, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(Window.width, 0)
        glVertex2f(Window.width, Window.height); glVertex2f(0, Window.height)
        glEnd()
        cls.drawText(Window.width//2 - 80, Window.height//2 + 20, "GAME OVER", (1, 0, 0))
        cls.drawText(Window.width//2 - 100, Window.height//2 - 30, "PRESS R TO RESTART", (1, 1, 1))

# =============================================================================
# DEBUG — Developer Tools
# =============================================================================

# Developer tools. Toggle with ` key during play.
# All methods notify the player so accidental triggers are visible.
# Has no effect on game state when enabled = False.
class Debug:
    enabled = False

    @classmethod
    def toggle(cls): 
        cls.enabled = not cls.enabled
        Notifications.add(f"DEBUG MODE: {'ON' if cls.enabled else 'OFF'}")

    @classmethod
    def fullHealth(cls): 
        Player.health = Player.maxHealth
        Notifications.add("HACK: FULL HEALTH")
    @classmethod
    def fullAmmo(cls): 
        Gun.currentAmmo = Gun.maxAmmo
        Notifications.add("HACK: FULL AMMO")
    @classmethod
    def addKey(cls): 
        Player.keys += 1
        Notifications.add("HACK: +1 KEY")
    @classmethod
    def spawnAllEnemies(cls):
        types = ["mutant", "wanderer", "shooter", "tank"]
        for i, t in enumerate(types):
            EnemyManager.spawnEnemy(Player.x + 200 + i*150, Player.z, t)
        Notifications.add("HACK: SPAWNED ALL ENEMY TYPES")

    @classmethod
    def spawnAllItems(cls):
        items = [HealthPack, AmmoPack, FoodPack, ShieldPack, Key, Chest]
        for i, item in enumerate(items):
            tile = Floor.getTile(Player.x + 200 + i*150, Player.z)
            if tile: tile.spawnObject(item)
        Notifications.add("HACK: SPAWNED ALL ITEM TYPES")

    @classmethod
    def enterSpaceship(cls):
        Player.mode = "spaceship"
        Player.saucerHealth = Player.maxSaucerHealth
        Notifications.add("HACK: ENTERED SPACESHIP")

    @classmethod
    def triggerChestReward(cls):
        Player.addImmunity(200)
        options = []
        if Player.health < Player.maxHealth: options.append('hp')
        if Gun.currentAmmo < Gun.maxAmmo: options.append('ammo')
        options.extend(['food', 'shield'])
        
        reward = random.choice(options)
        if reward == 'hp': 
            Player.heal(50)
            Notifications.add("HACK REWARD: HEALTH REPLENISHED")
        elif reward == 'ammo': 
            Gun.currentAmmo = min(Gun.maxAmmo, Gun.currentAmmo + 20)
            Notifications.add("HACK REWARD: AMMO RESTOCKED")
        elif reward == 'food': 
            Player.addFood(3)
            Notifications.add("HACK REWARD: BIOMASS BOOST")
        elif reward == 'shield': 
            Player.addImmunity(600)
            Notifications.add("HACK REWARD: SHIELD OVERCHARGE")
        return True

    @classmethod
    def skipToNight(cls): 
        DayNightManager.startTime = time.time() - DayNightManager.phaseDuration
        Notifications.add("HACK: INSTANT NIGHT")

# =============================================================================
# ENTRY POINT — Event Loop and Initialization
# =============================================================================

def keyboardListener(key, x, y):
    if GameState.current == GameState.MENU:
        if key == b'\r': # Enter
            GameState.current = GameState.CUSTOMIZE
        return

    if GameState.current == GameState.CUSTOMIZE:
        if key == b'\r': # Enter
            GameState.current = GameState.PLAY
        elif key == b'1': # Cycle body color
            colors = [(0.5, 0.1, 0.18), (0.1, 0.5, 0.18), (0.1, 0.18, 0.5), (0.8, 0.8, 0.1)]
            currentTuple = tuple(PlayerRenderer.bodyColor)
            idx = (colors.index(currentTuple) + 1) % len(colors) if currentTuple in colors else 0
            PlayerRenderer.bodyColor = list(colors[idx])
        elif key == b'2': # Cycle leg color
            colors = [(0.08, 0.12, 0.35), (0.35, 0.12, 0.08), (0.12, 0.35, 0.08), (0.5, 0.5, 0.5)]
            currentTuple = tuple(PlayerRenderer.legColor)
            idx = (colors.index(currentTuple) + 1) % len(colors) if currentTuple in colors else 0
            PlayerRenderer.legColor = list(colors[idx])
        return

    if GameState.current == GameState.PLAY:
        if Debug.enabled:
            if key == b'1': Debug.fullHealth(); return
            if key == b'2': Debug.fullAmmo(); return
            if key == b'3': Debug.addKey(); return
            if key == b'4': Debug.spawnAllEnemies(); return
            if key == b'5': Debug.spawnAllItems(); return
            if key == b'6': Debug.enterSpaceship(); return
            if key == b'7': Debug.skipToNight(); return
            if key == b'8': Debug.triggerChestReward(); return

        if key == b'w': Player.moveForward()
        if key == b's': Player.moveBackward()
        if key == b'a': Player.turnLeft()
        if key == b'd': Player.turnRight()
        if key == b'q' or key == b'Q':
            if Floor.current == Floor.homebase: Floor.homebase.exit()
            else: Player.exitSpaceship()
        if key == b' ': Gun.shoot()
        if key == b'b': Bomb(Player.x, Player.z)
        if key == b'p': GameState.current = GameState.PAUSE
        if key == b'm' or key == b'M': UIManager.minimapZoomedIn = not UIManager.minimapZoomedIn
        if key == b'=': Camera.radius += 5
        if key == b'-': Camera.radius -= 5
        if key == b'`': Debug.toggle()
        return

    if GameState.current == GameState.PAUSE:
        if key == b'p': GameState.current = GameState.PLAY
        if key == b'c' or key == b'C': GameState.current = GameState.CUSTOMIZE
        return

    if GameState.current == GameState.GAMEOVER:
        if key == b'r' or key == b'R':
            Game.restart()
        return

def specialKeyListener(key, x, y):
    if key == GLUT_KEY_LEFT:
        Camera.angle -= 1
    if key == GLUT_KEY_RIGHT:
        Camera.angle += 1
    if key == GLUT_KEY_UP:
        Camera.height += 5
    if key == GLUT_KEY_DOWN:
        Camera.height -= 5

def mouseListener(button, state, x, y):
    pass

def animate():
    if GameState.current == GameState.PLAY:
        Game.update()
        if Player.health <= 0:
            GameState.current = GameState.GAMEOVER
    glutPostRedisplay()

def display():
    DayNightManager.updateSky()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, Window.width, Window.height)

    Camera.setupCamera()
    
    if GameState.current in [GameState.PLAY, GameState.PAUSE, GameState.GAMEOVER]:
        Floor.draw()
        Player.draw()
        if Floor.current == Floor.wasteland:
            for b in Game.bullets:
                b.draw()
            EnemyManager.draw()
            for b in Game.bombs: b.draw()
            for e in Game.explosions: e.draw()

    UIManager.draw()
    glutSwapBuffers()

# --- INITIALIZATION ---

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH) 
glutInitWindowSize(Window.width, Window.height)
glutInitWindowPosition(0, 0)
glutCreateWindow(b"Wasteland Zero")
glEnable(GL_DEPTH_TEST)
glutDisplayFunc(display)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)
glutIdleFunc(animate)
Game.init()
glutMainLoop()