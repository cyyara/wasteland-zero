from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import numpy 

class DelayedAction:
    def __init__(self, duration, action):
        Game.DelayedActions.append(self)
        self.duration = duration
        self.startTime = time.time()
        self.action = action

    def isComplete(self):
        return time.time() - self.startTime >= self.duration

    def update(self):
        if self.isComplete():
            self.action()
            Game.DelayedActions.remove(self)



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
        

class Window:
    width = 1000
    height = 700

class Tile:
    length = width = 150
    
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
    
    def discolour(self):
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
    def __init__(self, x, z):
        super().__init__(x, z)
        self.offset = random.uniform(0, 10)
    
    def draw(self):
        pulse = (math.sin(time.time() * 0.5 + self.offset) + 1) / 2
        self.color = (0, 0.2 + (pulse * 0.8), 0)
        super().draw()

class WaterTile(Tile):
    def __init__(self, x, z):
        super().__init__(x, z)
        self.offset = random.uniform(0, 10)
    
    def draw(self):
        self.color = (0, 0, 1)
        super().draw()

class PortalTile(Tile):
    isActive = True
    cooldownTime = 30

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
        self.discolour()

    def draw(self):
        super().draw()

class TreeTile(WastelandTile):
    def __init__(self, x, z):
        super().__init__(x, z)
        self.isWalkable = False
        self.trunkColor = (0.35, 0.25, 0.15)
        self.leafColor = (0.1, 0.4, 0.1)
        self.height = random.uniform(400, 700)
        self.thickness = random.uniform(60, 85)

    def draw(self):
        super().draw() # Draw wasteland base
        
        # Don't draw tree if camera is inside/very close to it
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

class Player:
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
    
    # Vehicle system
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
    def triggerTile(cls):
        tile = Floor.getTile(cls.x, cls.z)
        if tile: tile.trigger()


    @classmethod
    def draw(cls):
        if cls.mode == "human":
            cls.drawHuman()
        else:
            cls.drawSpaceship()

    @classmethod
    def drawHuman(cls):
        glPushMatrix()
        glTranslatef(cls.x, 0, cls.z)
        glRotatef(cls.angle, 0, 1, 0) 

        legXOffset = cls.bodyWidth * cls.legXOffsetFactor
        handY = cls.legHeight + (cls.bodyHeight / cls.handYDivisor)
        gunY = cls.legHeight + (cls.bodyHeight / cls.gunYDivisor)
        gunZ = cls.bodyWidth * cls.gunZOffsetFactor

        # Right leg
        glColor3f(*cls.legColor)
        glPushMatrix()
        glTranslatef(-legXOffset, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), cls.legBottomWidth / 2, cls.legBaseWidth / 2, cls.legHeight, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()

        # Left leg
        glColor3f(*cls.legColor)
        glPushMatrix()
        glTranslatef(legXOffset, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), cls.legBottomWidth / 2, cls.legBaseWidth / 2, cls.legHeight, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()


        # Body
        glColor3f(*cls.bodyColor)
        glPushMatrix()
        glTranslatef(0, cls.legHeight + cls.bodyHeight / 2, 0)
        glScalef(cls.bodyWidth, cls.bodyHeight, cls.bodyThickness)
        glutSolidCube(1)
        glPopMatrix()

        # Right hand
        glColor3f(*cls.handColor)
        glPushMatrix()
        glTranslatef(cls.bodyWidth/2 - cls.handBaseRadius, handY, 0)
        gluCylinder(gluNewQuadric(), cls.handBaseRadius, cls.handTopRadius, cls.handLength, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()

        # Left hand
        glColor3f(*cls.handColor)
        glPushMatrix()
        glTranslatef(-cls.bodyWidth/2 + cls.handBaseRadius, handY, 0)
        gluCylinder(gluNewQuadric(), cls.handBaseRadius, cls.handTopRadius, cls.handLength, cls.cylinderSlices, cls.cylinderStacks)
        glPopMatrix()

        # Head
        glColor3f(*cls.headColor)
        glPushMatrix()
        glTranslatef(0, cls.legHeight + cls.bodyHeight + cls.headRadius, 0)
        glutSolidSphere(cls.headRadius, cls.headSlices, cls.headStacks)
        glPopMatrix()

        # Gun
        glColor3f(*cls.gunColor)
        glPushMatrix()
        glTranslatef(cls.gunXOffset, gunY, gunZ)
        gluCylinder(gluNewQuadric(), cls.gunBaseRadius, cls.gunTopRadius, cls.gunLength, cls.cylinderSlices, cls.cylinderStacks)

        # Gun handle
        glColor3f(*cls.gunHandleColor)
        glPushMatrix()
        glTranslatef(cls.gunHandleXOffset, cls.gunHandleYOffset, cls.gunHandleZOffset)
        glScalef(cls.gunHandleWidth, cls.gunHandleHeight, cls.gunHandleThickness)
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()

        glPopMatrix()

    @classmethod
    def drawSpaceship(cls):
        glPushMatrix()
        # Hover effect
        hoverY = 40 + math.sin(time.time() * 3) * 15
        glTranslatef(cls.x, hoverY, cls.z)
        glRotatef(cls.angle, 0, 1, 0)

        # Main Body
        glColor3f(0.5, 0.5, 0.5) # Silver
        glPushMatrix()
        glScalef(3.0, 0.6, 3.0)
        glutSolidSphere(40, 20, 20)
        glPopMatrix()

        # Cockpit Dome (More protruding)
        glColor3f(0.0, 0.8, 1.0) # Cyan
        glPushMatrix()
        glTranslatef(0, 18, 0) # Higher up
        glScalef(1.0, 1.3, 1.0) # Taller dome
        glutSolidSphere(25, 20, 20)
        glPopMatrix()

        # Navigation Light (Direction indicator - Front)
        glPushMatrix()
        glTranslatef(0, 5, 120) 
        glColor3f(1.0, 0.5, 0.0) # Bright orange
        glutSolidSphere(10, 10, 10)
        glPopMatrix()

        glPopMatrix()


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
   

class Bullet:
    def __init__(self, x, y, z, angle):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle
        self.speed = 15
        self.radius = 4
        self.life = 100 
        self.color = (1.0, 0.9, 0.2)

    def update(self):
        rad = math.radians(self.angle)
        self.x += self.speed * math.sin(rad)
        self.z += self.speed * math.cos(rad)
        self.life -= 1

        # Check tree collision
        tile = Floor.getTile(self.x, self.z)
        if tile and not tile.isWalkable:
            self.life = 0

    def draw(self):
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glutSolidSphere(self.radius, 10, 10)
        glPopMatrix()

class Gun:
    bullets = []
    maxAmmo = 30
    currentAmmo = 30

    @classmethod
    def shoot(cls):
        if Player.mode == "spaceship": return # Can't shoot while flying
        if cls.currentAmmo > 0:
            rad = math.radians(Player.angle)
            
            # Match the Player.draw() gun height
            gunY = Player.legHeight + (Player.bodyHeight / Player.gunYDivisor)
            # Match the gun's forward protrusion (base Z + cylinder length)
            gunZLocal = (Player.bodyWidth * Player.gunZOffsetFactor) + Player.gunLength
            
            # Local to World transformation matching Player's rotation
            muzzleX = Player.x + (Player.gunXOffset * math.cos(rad)) + (gunZLocal * math.sin(rad))
            muzzleZ = Player.z - (Player.gunXOffset * math.sin(rad)) + (gunZLocal * math.cos(rad))

            cls.bullets.append(Bullet(muzzleX, gunY, muzzleZ, Player.angle))
            cls.currentAmmo -= 1

    @classmethod
    def updateBullets(cls):
        for bullet in cls.bullets[:]:
            bullet.update()
            
            # Check collision with enemies
            hit = False
            for enemy in EnemyManager.enemies:
                dx = bullet.x - enemy.x
                dz = bullet.z - enemy.z
                dist = math.sqrt(dx*dx + dz*dz)
                # Collision radius varies by type
                radius = 70 if isinstance(enemy, Tank) else 40
                if dist < radius:
                    enemy.takeDamage(20)
                    hit = True
                    break
            
            if bullet.life <= 0 or hit:
                cls.bullets.remove(bullet)

    @classmethod
    def drawBullets(cls):
        for bullet in cls.bullets:
            bullet.draw()

    @classmethod
    def addAmmo(cls, amount):
        cls.currentAmmo = min(cls.maxAmmo, cls.currentAmmo + amount)

class HealthPack:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 50
        self.color = (1, 1, 1) # White
        self.crossColor = (1, 0, 0) # Red
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        angle = (time.time() * 100) % 360
        glRotatef(angle, 0, 1, 0) # Rotate
        
        # Red cross
        glColor3f(*self.crossColor)
        # Vertical bar
        glPushMatrix()
        glScalef(0.25, 1.0, 0.25)
        glutSolidCube(60)
        glPopMatrix()
        # Horizontal bar
        glPushMatrix()
        glScalef(1.0, 0.25, 0.25)
        glutSolidCube(60)
        glPopMatrix()
        
        glPopMatrix()

    def apply(self, player):
        if player.health < player.maxHealth:
            player.heal(30)
            return True
        return False

class ShieldPack:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 60
        self.color = (0.2, 0.8, 1.0)
        
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        angle = (time.time() * 100) % 360
        glRotatef(angle, 0, 1, 0)
        
        glColor3f(*self.color)
        # Single Vertical Plate
        glScalef(0.8, 2.5, 1.8)
        glutSolidSphere(20, 15, 15)
        
        glPopMatrix()
        
    def apply(self, player):
        player.addImmunity(900) # 15 seconds of shield
        return True

class AmmoPack:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 50
        self.color = (0.2, 0.2, 0.2) # Dark grey
        self.tipColor = (0.8, 0.6, 0.2) # Gold
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        angle = (time.time() * 100) % 360
        glRotatef(angle, 0, 1, 0) # Rotate
        
        # Center the bullet for rotation
        glTranslatef(0, 0, -35) 
        
        # Back Casing half
        glColor3f(*self.color)
        gluCylinder(gluNewQuadric(), 15, 15, 25, 10, 10)
        
        # Close the bottom of the casing with a sphere cap
        glPushMatrix()
        glScalef(1.0, 1.0, 0.3) # Flatten the sphere into a cap
        glutSolidSphere(15, 10, 10)
        glPopMatrix()
        
        # Front Casing half (Same as tip color)
        glTranslatef(0, 0, 25)
        glColor3f(*self.tipColor) 
        gluCylinder(gluNewQuadric(), 15, 15, 25, 10, 10)

        # Bullet tip
        glTranslatef(0, 0, 25)
        glColor3f(*self.tipColor)
        gluCylinder(gluNewQuadric(), 15, 0, 20, 10, 10)
        
        glPopMatrix()

    def apply(self, player):
        if Gun.currentAmmo < Gun.maxAmmo:
            Gun.addAmmo(10)
            return True
        return False

class Enemy:
    def __init__(self, x, z, health, speed, color):
        self.x = x
        self.z = z
        self.angle = 0
        self.health = health
        self.maxHealth = health
        self.speed = speed
        self.color = color
        self.isAlive = True
        
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

        # State Transitions
        if dist < self.attackRange:
            self.state = "ATTACK"
        elif dist < self.detectionRange:
            self.state = "CHASE"
        else:
            self.state = "PATROL"

        nextX, nextZ = self.x, self.z

        if self.state == "PATROL":
            self.patrolTimer -= 1
            if self.patrolTimer <= 0:
                self.patrolDir = [random.uniform(-1, 1), random.uniform(-1, 1)]
                self.patrolTimer = random.randint(60, 120)
            
            nextX += self.patrolDir[0] * (self.speed * 0.5)
            nextZ += self.patrolDir[1] * (self.speed * 0.5)
            self.angle = math.degrees(math.atan2(self.patrolDir[0], self.patrolDir[1]))

        elif self.state == "CHASE":
            targetAngle = math.degrees(math.atan2(dx, dz))
            angleDiff = (targetAngle - self.angle + 180) % 360 - 180
            self.angle += angleDiff * 0.05
            rad = math.radians(self.angle)
            nextX += self.speed * math.sin(rad)
            nextZ += self.speed * math.cos(rad)

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
        if self.health <= 0:
            self.isAlive = False
            self.dropLoot()

    def dropLoot(self):
        tile = Floor.getTile(self.x, self.z)
        if tile and tile.object is None:
            pickup = random.choice([HealthPack, AmmoPack, FoodPack])
            tile.spawnObject(pickup)

class Mutant(Enemy):
    def __init__(self, x, z):
        super().__init__(x, z, health=50, speed=2.5, color=(0.3, 0.4, 0.2))
        self.eyeColor = (0.0, 1.0, 0.0)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        
        self.drawHealthBar()
        
        glRotatef(self.angle, 0, 1, 0)
        
        # Mutant Body (Hunched)
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(0, 45, 0)
        glScalef(50, 70, 40)
        glutSolidCube(1)
        glPopMatrix()
        
        # Head
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
        # Squat, slow zombie
        super().__init__(x, z, health=30, speed=1.5, color=(0.8, 0.5, 0.1))

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        self.drawHealthBar()
        glRotatef(self.angle, 0, 1, 0)
        
        # Wide flat body
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(0, 20, 0)
        glScalef(60, 40, 40)
        glutSolidCube(1)
        glPopMatrix()
        
        # Big lopsided head
        glPushMatrix()
        glTranslatef(5, 55, 10)
        glutSolidSphere(25, 10, 10)
        glPopMatrix()
        
        glPopMatrix()

class Tank(Enemy):
    def __init__(self, x, z):
        super().__init__(x, z, health=200, speed=0.8, color=(0.3, 0.3, 0.3))
        self.attackRange = 700
        self.shootTimer = 0

    def performAttack(self, dist):
        # Face player
        dx = Player.x - self.x
        dz = Player.z - self.z
        targetAngle = math.degrees(math.atan2(dx, dz))
        # Slow turret rotation towards player
        angleDiff = (targetAngle - self.angle + 180) % 360 - 180
        self.angle += angleDiff * 0.02
        
        self.shootTimer -= 1
        # Only fire if aimed closely at the player (within 5 degrees)
        if self.shootTimer <= 0 and abs(angleDiff) < 5:
            # Calculate muzzle position (at the tip of the barrel)
            rad = math.radians(self.angle)
            muzzleX = self.x + 80 * math.sin(rad)
            muzzleZ = self.z + 80 * math.cos(rad)
            
            # Tank fires heavy shells (Bright glowing orange/gold)
            EnemyBullet.active.append(EnemyBullet(muzzleX, 70, muzzleZ, self.angle, damage=25, scale=12, color=(1.0, 0.6, 0.0)))
            self.shootTimer = 150 # Slow fire rate for balance

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        self.drawHealthBar()
        glRotatef(self.angle, 0, 1, 0)
        
        # Heavy Body
        glColor3f(*self.color)
        glPushMatrix()
        glTranslatef(0, 30, 0)
        glScalef(100, 60, 100)
        glutSolidCube(1)
        glPopMatrix()
        
        # Turret
        glColor3f(0.2, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(0, 70, 0)
        glScalef(60, 40, 60)
        glutSolidCube(1)
        glPopMatrix()
        
        # Barrel
        glPushMatrix()
        glTranslatef(0, 70, 40)
        glColor3f(0.1, 0.1, 0.1)
        gluCylinder(gluNewQuadric(), 10, 10, 40, 10, 10)
        glPopMatrix()
        
        glPopMatrix()

class EnemyBullet:
    active = []
    def __init__(self, x, y, z, angle, damage=5, scale=5, color=(1.0, 0.2, 0.0)):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle
        self.speed = 10
        self.life = 100
        self.damage = damage
        self.scale = scale
        self.color = color

    def update(self):
        rad = math.radians(self.angle)
        self.x += self.speed * math.sin(rad)
        self.z += self.speed * math.cos(rad)
        self.life -= 1
        
        # Check tree collision
        tile = Floor.getTile(self.x, self.z)
        if tile and not tile.isWalkable:
            self.life = 0
            return
            
        # Collision with player
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
        glutSolidSphere(self.scale, 8, 8)
        glPopMatrix()

class Shooter(Enemy):
    def __init__(self, x, z):
        super().__init__(x, z, health=40, speed=3.0, color=(0.6, 0.2, 0.2))
        self.attackRange = 500
        self.shootTimer = 0

    def performAttack(self, dist):
        # Rotate to face player
        dx = Player.x - self.x
        dz = Player.z - self.z
        self.angle = math.degrees(math.atan2(dx, dz))
        
        self.shootTimer -= 1
        if self.shootTimer <= 0:
            EnemyBullet.active.append(EnemyBullet(self.x, 60, self.z, self.angle))
            self.shootTimer = 60

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        self.drawHealthBar()
        glRotatef(self.angle, 0, 1, 0)
        
        # Thin Body
        glColor3f(*self.color)
        glPushMatrix(); glTranslatef(0, 50, 0); glScalef(25, 100, 25); glutSolidCube(1); glPopMatrix()
        # Head
        glPushMatrix(); glTranslatef(0, 110, 0); glutSolidSphere(15, 10, 10); glPopMatrix()
        # Weapon
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix(); glTranslatef(0, 60, 20); gluCylinder(gluNewQuadric(), 5, 5, 40, 8, 8); glPopMatrix()
        
        glPopMatrix()

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
                # Fun Drop Rates!
                roll = random.random()
                if roll < 0.30: # 30% chance to drop something
                    # Key chance based on enemy difficulty
                    keyRoll = random.random()
                    keyChance = 0.01 # Mutant/Wanderer
                    if hasattr(e, 'type'):
                        if e.type == "shooter": keyChance = 0.08
                        elif e.type == "tank": keyChance = 0.20
                    
                    if keyRoll < keyChance:
                        item = Key
                    else:
                        # Other items
                        otherRoll = random.random()
                        if otherRoll < 0.50: item = AmmoPack
                        elif otherRoll < 0.85: item = FoodPack
                        else: item = ShieldPack
                    
                    # Spawn item at enemy's location
                    tile = Floor.getTile(e.x, e.z)
                    if tile:
                        tile.spawnObject(item)
        
        # Update enemy bullets
        for b in EnemyBullet.active[:]:
            b.update()
            if b.life <= 0: EnemyBullet.active.remove(b)
                
    @classmethod
    def draw(cls):
        for enemy in cls.enemies:
            enemy.draw()
        for b in EnemyBullet.active:
            b.draw()

class FoodPack:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 50
        self.color = (0.2, 0.8, 0.2) # Green
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        angle = (time.time() * 100) % 360
        glRotatef(angle, 0, 1, 0) # Rotate
        glColor3f(*self.color)
        glutSolidSphere(25, 12, 12)
        glPopMatrix()

    def apply(self, player):
        player.addFood(1)
        return True

class Spaceship:
    def __init__(self, x, z, health=None):
        self.x = x
        self.z = z
        self.y = 50
        self.health = health if health is not None else Player.maxSaucerHealth
    
    def draw(self):
        glPushMatrix()
        # Hover effect for pickup
        hoverY = self.y + math.sin(time.time() * 2) * 10
        glTranslatef(self.x, hoverY, self.z)
        
        # Scale down for pickup
        glScalef(0.4, 0.4, 0.4)
        
        # Body
        glColor3f(0.6, 0.6, 0.6)
        glPushMatrix()
        glScalef(3.0, 0.6, 3.0)
        glutSolidSphere(40, 15, 15)
        glPopMatrix()
        
        # Dome
        glColor3f(0.0, 0.8, 1.0)
        glPushMatrix()
        glTranslatef(0, 15, 0)
        glScalef(1.0, 1.3, 1.0)
        glutSolidSphere(20, 15, 15)
        glPopMatrix()

        # Front Indicator
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
        # Background
        glColor3f(*bgColor)
        glBegin(GL_QUADS)
        glVertex2f(x, y); glVertex2f(x + width, y)
        glVertex2f(x + width, y + height); glVertex2f(x, y + height)
        glEnd()

        # Progress
        glColor3f(*barColor)
        glBegin(GL_QUADS)
        glVertex2f(x, y); glVertex2f(x + (width * progress), y)
        glVertex2f(x + (width * progress), y + height); glVertex2f(x, y + height)
        glEnd()

    @classmethod
    def draw(cls):
        # Switch to 2D
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
        # Semi-transparent dark background (simulated without blend)
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
        
        # Draw color previews
        cls.drawText(Window.width - 300, Window.height - 150, "BODY COLOR")
        glColor3f(*Player.bodyColor)
        glBegin(GL_QUADS)
        glVertex2f(Window.width - 300, Window.height - 200); glVertex2f(Window.width - 200, Window.height - 200)
        glVertex2f(Window.width - 200, Window.height - 240); glVertex2f(Window.width - 300, Window.height - 240)
        glEnd()
        
        cls.drawText(Window.width - 300, Window.height - 280, "LEG COLOR")
        glColor3f(*Player.legColor)
        glBegin(GL_QUADS)
        glVertex2f(Window.width - 300, Window.height - 330); glVertex2f(Window.width - 200, Window.height - 330)
        glVertex2f(Window.width - 200, Window.height - 370); glVertex2f(Window.width - 300, Window.height - 370)
        glEnd()

    @classmethod
    def drawMinimap(cls):
        w = Floor.wasteland
        rows = len(w.tiles)
        cols = len(w.tiles[0])
        
        # UI Layout
        cellSize = 8 if cls.minimapZoomedIn else 4
        viewRadius = 7 # Number of tiles to show in each direction when zoomed
        gridSize = (viewRadius * 2 + 1) if cls.minimapZoomedIn else cols
        
        mapWidth = gridSize * cellSize
        mapHeight = gridSize * cellSize
        offsetX = Window.width - mapWidth - 25
        offsetY = 25
        
        # Minimap Background Panel
        glColor3f(0.05, 0.05, 0.05)
        glBegin(GL_QUADS)
        glVertex2f(offsetX - 5, offsetY - 5); glVertex2f(offsetX + mapWidth + 5, offsetY - 5)
        glVertex2f(offsetX + mapWidth + 5, offsetY + mapHeight + 5); glVertex2f(offsetX - 5, offsetY + mapHeight + 5)
        glEnd()

        # Get player tile indices
        pCol = int((Player.x - w.startX) / Tile.length)
        pRow = int((Player.z - w.startZ) / Tile.width)

        # Tile range
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
                    color = (0.35, 0.35, 0.35) # Default Grey
                    
                    if isinstance(tile, TreeTile): color = (0.05, 0.15, 0.05)
                    elif isinstance(tile, AcidTile): color = (0.2, 0.8, 0.2)
                    elif isinstance(tile, WaterTile): color = (0.0, 0.4, 0.7)
                    elif isinstance(tile, PortalTile): color = (0.8, 0.8, 0.0)
                    
                    if tile.object:
                        obj = tile.object
                        if isinstance(obj, Chest): color = (0.4, 0.2, 0.1)
                        elif isinstance(obj, Spaceship): color = (0.5, 0.0, 0.7)
                        elif isinstance(obj, (HealthPack, AmmoPack, FoodPack, ShieldPack, Key)): color = (0.9, 0.3, 0.6)
                    
                    glColor3f(*color)
                    glBegin(GL_QUADS)
                    x = offsetX + j * cellSize
                    y = offsetY + i * cellSize
                    glVertex2f(x, y); glVertex2f(x + cellSize, y)
                    glVertex2f(x + cellSize, y + cellSize); glVertex2f(x, y + cellSize)
                    glEnd()

        # Entity calculations
        def getMapPos(wx, wz):
            if cls.minimapZoomedIn:
                # Relative to player
                rx = (wx - Player.x) / Tile.length
                rz = (wz - Player.z) / Tile.width
                mx = offsetX + (viewRadius + rx) * cellSize + cellSize/2
                my = offsetY + (viewRadius + rz) * cellSize + cellSize/2
                return mx, my
            else:
                # Global map
                mx = offsetX + ((wx - w.startX) / (cols * Tile.length)) * mapWidth
                my = offsetY + ((wz - w.startZ) / (rows * Tile.width)) * mapHeight
                return mx, my

        glPointSize(4 if cls.minimapZoomedIn else 3)
        glBegin(GL_POINTS)
        # Enemies
        glColor3f(1.0, 0.0, 0.0)
        for e in EnemyManager.enemies:
            mx, my = getMapPos(e.x, e.z)
            # Only draw if within minimap bounds
            if offsetX <= mx <= offsetX + mapWidth and offsetY <= my <= offsetY + mapHeight:
                glVertex2f(mx, my)
        
        # Player
        glColor3f(1.0, 1.0, 1.0)
        px, py = getMapPos(Player.x, Player.z)
        glVertex2f(px, py)
        glEnd()
        
        cls.drawText(offsetX, offsetY + mapHeight + 10, f"MAP: {'LOCAL' if cls.minimapZoomedIn else 'GLOBAL'} [M]", (0.7, 0.7, 0.7))

    @classmethod
    def drawHUD(cls):
        # Health
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

        # Food
        foodLimit = 10
        foodProgress = min(1.0, Player.food / foodLimit)
        cls.drawText(20, Window.height - 90, "VITAMINS", (0.2, 0.9, 0.2))
        cls.drawBar(20, Window.height - 110, 200, 10, foodProgress, (0.1, 0.8, 0.1))
        
        # Shield / Immunity (Only if active)
        if Player.immunity > 0:
            shieldProgress = min(1.0, Player.immunity / 1800)
            cls.drawText(20, Window.height - 145, "SHIELD CHARGE", (0.4, 0.6, 1.0))
            cls.drawBar(20, Window.height - 160, 200, 8, shieldProgress, (0.2, 0.5, 1.0))

        # Ammo
        ammoProgress = Gun.currentAmmo / Gun.maxAmmo
        cls.drawText(Window.width - 200, Window.height - 35, "AMMO CAPACITY", (0.8, 0.7, 0))
        cls.drawBar(Window.width - 200, Window.height - 55, 180, 12, ammoProgress, (0.7, 0.5, 0.1))
        cls.drawText(Window.width - 200, Window.height - 70, f"{Gun.currentAmmo} / {Gun.maxAmmo}")

        # Keys
        cls.drawText(Window.width - 200, Window.height - 90, f"ACCESS KEYS: {Player.keys}", (1, 1, 1))

        # Day
        cls.drawText(Window.width//2 - 40, Window.height - 40, f"DAY {DayNightManager.dayCount}", (1, 1, 1))

        # Environment
        isNight, _ = DayNightManager.getPhase()
        danger = DayNightManager.getDanger()
        dangerColor = (1, 0.1, 0) if DayNightManager.isDangerous() else (1, 0.6, 0)
        
        phaseText = "NIGHTFALL" if isNight else "SOLAR"
        cls.drawText(20, 55, f"PHASE: {phaseText}", (1, 1, 1))
        cls.drawBar(20, 35, 200, 12, danger, dangerColor)
        cls.drawText(20, 20, "DANGER LEVEL", dangerColor)

        # Context Hints
        if isSpaceship:
            cls.drawText(Window.width//2 - 100, 100, "PRESS [Q] TO LAND VESSEL", (1, 0.5, 0))
        elif Player.mode == "human" and Gun.currentAmmo == 0:
            cls.drawText(Window.width//2 - 100, 100, "OUT OF AMMO! FIND PACKS", (1, 0, 0))

        if Floor.current == Floor.wasteland:
            cls.drawMinimap()

    @classmethod
    def drawPause(cls):
        cls.drawHUD() # Draw gameplay HUD behind
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

class Key:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 50
        self.color = (0.8, 0.6, 0.2) # Gold
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        angle = (time.time() * 100) % 360
        glRotatef(angle, 0, 1, 0)
        
        glColor3f(*self.color)
        
        # Shaft (Horizontal)
        glPushMatrix()
        glTranslatef(0, 0, -10) # Center the 40-unit shaft (partially)
        glScalef(0.2, 0.2, 1.0)
        glutSolidCube(40)
        glPopMatrix()
        
        # Ring (Bow)
        glPushMatrix()
        glTranslatef(0, 0, 15)
        glutSolidSphere(8, 10, 10)
        glPopMatrix()
        
        glPopMatrix()

    def apply(self, player):
        player.keys += 1
        return True

class Chest:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 50
        self.color = (0.4, 0.2, 0.1) # Brown
        self.lockColor = (0.8, 0.6, 0.2) # Gold
    
    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        angle = (time.time() * 100) % 360
        glRotatef(angle, 0, 1, 0)
        
        # Chest Body (Wider)
        glColor3f(*self.color)
        glPushMatrix()
        glScalef(1.5, 1.0, 1.0)
        glutSolidCube(40)
        glPopMatrix()
        
        # Lock
        glPushMatrix()
        glTranslatef(0, 0, 20)
        glColor3f(*self.lockColor)
        glutSolidCube(8)
        glPopMatrix()
        
        glPopMatrix()

    def apply(self, player):
        if player.useKey():
            # Grant Immunity
            player.addImmunity(600)
            
            # Random reward
            reward = random.choice(['hp', 'ammo', 'food', 'shield'])
            if reward == 'hp': player.heal(35)
            elif reward == 'ammo': Gun.currentAmmo += 20
            elif reward == 'food': player.addFood(3)
            elif reward == 'shield': player.addImmunity(1800) # 30s shield
            
            # Spawn a new chest elsewhere in the wasteland
            Game.spawnNewChest()
            
            return True
        return False

class Game:
    DelayedActions = []
    Bombs = []
    Explosions = []

    @classmethod
    def restart(cls):
        # Reset Player
        Player.x = 0
        Player.z = 0
        Player.angle = 0
        Player.health = 100
        Player.food = 3
        Player.keys = 0
        Player.immunity = 0
        Player.mode = "human"
        
        # Reset Equipment
        Gun.currentAmmo = 20
        Gun.activeBullets = []
        EnemyBullet.active = []
        
        # Reset DayNight
        DayNightManager.dayCount = 1
        DayNightManager.startTime = time.time()
        DayNightManager._lastCycle = 0
        
        # Reset Entities
        EnemyManager.enemies = []
        cls.Bombs = []
        cls.Explosions = []
        cls.DelayedActions = []
        
        # Regenerate World
        Floor.current = Wasteland(40, 40)
        
        GameState.current = GameState.PLAY

    @classmethod
    def update(cls):
        for d in cls.DelayedActions[:]: d.update()
        
        if Floor.current == Floor.wasteland:
            for b in cls.Bombs[:]: b.update()
            for e in cls.Explosions[:]: e.update()
            Gun.updateBullets()
            EnemyManager.update()
            
        if Player.mode == "spaceship" and Player.saucerHealth <= 0:
            Player.mode = "human"

        Player.triggerTile()
        
        if GameState.current == GameState.PLAY and Floor.current != Floor.homebase:
            diff = DayNightManager.getDifficulty()
            
            # Random Bomb Drops
            if random.random() < 0.002 * diff:
                cls.spawnRandomBomb()
                
            # Random Enemy Spawning
            enemyCap = 5 + int(diff * 2)
            if len(EnemyManager.enemies) < enemyCap:
                # Chance to spawn per frame (e.g., 1% * diff)
                if random.random() < 0.005 * diff:
                    cls.spawnRandomEnemy()

    @classmethod
    def spawnRandomEnemy(cls):
        # Spawn at a distance from player
        dist = random.randint(800, 1500)
        angle = random.uniform(0, 2 * math.pi)
        ex = Player.x + dist * math.cos(angle)
        ez = Player.z + dist * math.sin(angle)
        
        # Pick type based on difficulty
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
        # Pick a random walkable tile in the current floor
        tiles = Floor.current.tiles
        r = random.randint(0, len(tiles)-1)
        c = random.randint(0, len(tiles[0])-1)
        targetTile = tiles[r][c]
        
        if targetTile.isWalkable:
            Bomb(targetTile.x, targetTile.z)
        else:
            # Try once more if we hit a tree
            cls.spawnRandomBomb()
    
class GameState:
    MENU = 0
    CUSTOMIZE = 1
    PLAY = 2
    PAUSE = 3
    GAMEOVER = 4
    
    current = MENU
    inHomebase = False

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
    cooldownStart = None

    def __init__(self, rows, columns):
        super().__init__(rows, columns, HomeTile)

    def enter(self, portal):
        Floor.current = Floor.homebase
        self.originPortal = portal
        Player.x = 0
        Player.z = 0
        DelayedAction(self.homeDuration, self.exit)
    
    def exit(self):
        Floor.current = Floor.wasteland
        Player.x = self.originPortal.x
        Player.z = self.originPortal.z
        self.originPortal = None
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

        self.portalPosition = self.popRandomPosition()
        self.spaceshipPosition = self.popRandomPosition()
        self.chestPosition = self.popRandomPosition()

        for r, c in self.waterPositions: self.changeTile(r, c, WaterTile)
        for r, c in self.acidPositions: self.changeTile(r, c, AcidTile)
        for r, c in self.treePositions: self.changeTile(r, c, TreeTile)

        self.changeTile(*self.portalPosition, PortalTile)
        self.spawnObject(*self.spaceshipPosition, Spaceship)
        self.spawnObject(*self.chestPosition, Chest)

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
        Game.Explosions.append(self)

    def update(self):
        self.currentRadius += self.growthSpeed
        if self.currentRadius >= self.maxRadius:
            self.dealDamage()
            self.isFinished = True
            Game.Explosions.remove(self)

    def dealDamage(self):
        # Damage Player if they are on a blinking tile
        playerTile = Floor.getTile(Player.x, Player.z)
        if playerTile in self.affectedTiles:
            damage = 50
            if Player.mode == "human": Player.health -= damage
            else: Player.saucerHealth -= damage
        
        # Damage Enemies if they are on a blinking tile
        for enemy in EnemyManager.enemies[:]:
            enemyTile = Floor.getTile(enemy.x, enemy.z)
            if enemyTile in self.affectedTiles:
                enemy.takeDamage(100)

    def draw(self):
        # Flashy colors
        pulse = (math.sin(time.time() * 25) + 1) / 2
        r = 1.0
        g = 0.2 + 0.6 * pulse
        b = 0.0
        
        glColor3f(r, g, b)
        
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glutSolidSphere(self.currentRadius, 32, 32)
        
        # Inner core
        glColor3f(1, 1, 1)
        glutSolidSphere(self.currentRadius * 0.6, 20, 20)
        
        glPopMatrix()

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
        Game.Bombs.append(self)

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
            Game.Bombs.remove(self)

    def draw(self):
        isBlinkOn = False
        elapsed = 0
        
        if not self.isFalling and self.startTime:
            elapsed = time.time() - self.startTime
            isBlinkOn = (int(elapsed / self.blinkSpeed) % 2) == 0
        
        # Draw blinking highlights on tiles (only after landing)
        if not self.isFalling and isBlinkOn:
            for tile in self.affectedTiles:
                # Grab the tile color and maximize the red component
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

        # Draw the bomb itself
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Pulsing scale during fuse
        scale = 1.0
        if not self.isFalling:
            scale = 1.0 + (elapsed / self.fuseTime) * 0.7 if isBlinkOn else 1.0
        glScalef(scale, scale, scale)
        
        glColor3f(0.1, 0.1, 0.1) # Black
        glutSolidSphere(20, 15, 15)
        
        # Fuse spark (only after landing)
        if not self.isFalling and isBlinkOn:
            glColor3f(1, 1, 0)
            glPushMatrix()
            glTranslatef(0, 20, 0)
            glutSolidSphere(5, 8, 8)
            glPopMatrix()
            
        glPopMatrix()



class Floor:
    homebase = Homebase(6, 6)
    wasteland = Wasteland(40, 40)
    current = wasteland
    
    @classmethod
    def draw(cls): 
        cls.current.draw()

    @classmethod
    def getTile(cls, x, z):
        return cls.current.getTile(x, z)

class DayNightManager:
    dayColor = numpy.array([0.72, 0.68, 0.38])
    nightColor = numpy.array([0.01, 0.00, 0.03])
    phaseDuration = 30
    startTime = time.time()
    dayCount = 1
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
        
        # Interpolate between dark night and bright day
        currentColor = cls.nightColor + (cls.dayColor - cls.nightColor) * brightness
        glClearColor(*currentColor, 1)

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
            current_tuple = tuple(Player.bodyColor)
            idx = (colors.index(current_tuple) + 1) % len(colors) if current_tuple in colors else 0
            Player.bodyColor = list(colors[idx])
        elif key == b'2': # Cycle leg color
            colors = [(0.08, 0.12, 0.35), (0.35, 0.12, 0.08), (0.12, 0.35, 0.08), (0.5, 0.5, 0.5)]
            current_tuple = tuple(Player.legColor)
            idx = (colors.index(current_tuple) + 1) % len(colors) if current_tuple in colors else 0
            Player.legColor = list(colors[idx])
        return

    if GameState.current == GameState.PLAY:
        if key == b'w': Player.moveForward()
        if key == b's': Player.moveBackward()
        if key == b'a': Player.turnLeft()
        if key == b'd': Player.turnRight()
        if key == b'q' or key == b'Q': Player.exitSpaceship()
        if key == b' ': Gun.shoot()
        if key == b'b': Bomb(Player.x, Player.z)
        if key == b'p': GameState.current = GameState.PAUSE
        if key == b'm' or key == b'M': UIManager.minimapZoomedIn = not UIManager.minimapZoomedIn
        if key == b'=': Camera.radius += 5
        if key == b'-': Camera.radius -= 5
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
    
    # Draw scene
    if GameState.current in [GameState.PLAY, GameState.PAUSE, GameState.GAMEOVER]:
        Floor.draw()
        Player.draw()
        if Floor.current == Floor.wasteland:
            Gun.drawBullets()
            EnemyManager.draw()
            for b in Game.Bombs: b.draw()
            for e in Game.Explosions: e.draw()

    # Update survival logic (only during play)
    if GameState.current == GameState.PLAY:
        if Player.immunity > 0:
            Player.immunity -= 1

    UIManager.draw()
    glutSwapBuffers()


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
Floor.wasteland = Wasteland(40, 40)
Floor.current = Floor.wasteland

# TEST SP AWNS - DELETE LATER
Floor.getTile(300, 300).spawnObject(HealthPack)
Floor.getTile(-300, 300).spawnObject(AmmoPack)
Floor.getTile(300, -300).spawnObject(FoodPack)
Floor.getTile(-300, -300).spawnObject(Key)
Floor.getTile(0, 300).spawnObject(ShieldPack)

glutMainLoop()