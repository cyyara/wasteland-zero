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
    mode = "human" # "human" or "saucer"
    saucerHealth = 300
    maxSaucerHealth = 300
    saucerSpeed = 45

    # Tunable render settings
    legColor = (0.08, 0.12, 0.35)
    bodyColor = (0.50, 0.10, 0.18)
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
            cls.drawSaucer()

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
    def drawSaucer(cls):
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

        # Lights
        for i in range(8):
            angle = i * (360/8)
            rad = math.radians(angle)
            lx = 100 * math.cos(rad)
            lz = 100 * math.sin(rad)
            glPushMatrix()
            glTranslatef(lx, -5, lz)
            glColor3f(1.0, 1.0, 0.0) # Yellow lights
            glutSolidSphere(5, 10, 10)
            glPopMatrix()
        # Navigation Light (Direction indicator - Front)
        glPushMatrix()
        glTranslatef(0, 5, 120) # Raised from -5 to 5 for visibility
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
            damagePool = "health" if Player.mode == "human" else "saucer"
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
            Shooter.bullets.append(EnemyBullet(muzzleX, 70, muzzleZ, self.angle, damage=25, scale=12, color=(1.0, 0.6, 0.0)))
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
    bullets = []
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
            self.bullets.append(EnemyBullet(self.x, 60, self.z, self.angle))
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
        for enemy in cls.enemies[:]:
            enemy.update()
            if not enemy.isAlive:
                cls.enemies.remove(enemy)
        
        # Update enemy bullets
        for b in Shooter.bullets[:]:
            b.update()
            if b.life <= 0: Shooter.bullets.remove(b)
                
    @classmethod
    def draw(cls):
        for enemy in cls.enemies:
            enemy.draw()
        for b in Shooter.bullets:
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
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.y = 50
    
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
        
        # Dome (More protruding)
        glColor3f(0.0, 0.8, 1.0)
        glPushMatrix()
        glTranslatef(0, 15, 0)
        glScalef(1.0, 1.3, 1.0)
        glutSolidSphere(20, 15, 15)
        glPopMatrix()

        # Front Indicator (For pickup)
        glPushMatrix()
        glTranslatef(0, 5, 120) # Raised from -5 to 5 for visibility
        glColor3f(1.0, 0.5, 0.0)
        glutSolidSphere(10, 10, 10)
        glPopMatrix()
        
        glPopMatrix()

    def apply(self, player):
        player.mode = "saucer"
        return True

class HUD:
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
        glVertex2f(x, y)
        glVertex2f(x + width, y)
        glVertex2f(x + width, y + height)
        glVertex2f(x, y + height)
        glEnd()

        # Progress
        glColor3f(*barColor)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + (width * progress), y)
        glVertex2f(x + (width * progress), y + height)
        glVertex2f(x, y + height)
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

        # Draw Health Bar (Top Left)
        hpProgress = Player.health / Player.maxHealth
        cls.drawBar(20, Window.height - 40, 200, 20, hpProgress, (0.8, 0.1, 0.1))
        cls.drawText(20, Window.height - 60, f"HP: {int(Player.health)} / {Player.maxHealth}")

        # Draw Food Bar (Below Health)
        foodLimit = 10 # Example limit for the bar scale
        foodProgress = min(1.0, Player.food / foodLimit)
        cls.drawBar(20, Window.height - 90, 200, 15, foodProgress, (0.1, 0.8, 0.1))
        cls.drawText(20, Window.height - 110, f"FOOD: {Player.food}")

        # Draw Ammo (Top Right)
        cls.drawText(Window.width - 150, Window.height - 40, f"AMMO: {Gun.currentAmmo} / {Gun.maxAmmo}")

        # Draw Keys (Below Ammo)
        cls.drawText(Window.width - 150, Window.height - 70, f"KEYS: {Player.keys}")

        # Draw Immunity (If active)
        if Player.immunity > 0:
            seconds = int(Player.immunity / 60) # Assuming ~60fps
            cls.drawText(Window.width // 2 - 50, Window.height - 40, f"SHIELD: {seconds}s", (0.2, 0.8, 1.0))

        glEnable(GL_DEPTH_TEST)
        
        # Switch back to 3D
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

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
            reward = random.choice(['hp', 'ammo', 'food'])
            if reward == 'hp': player.heal(60)
            elif reward == 'ammo': Gun.addAmmo(30)
            else: player.addFood(3)
            
            return True
        return False

class Game:
    DelayedActions = []
    Bombs = []
    Explosions = []

    @classmethod
    def update(cls):
        for d in cls.DelayedActions[:]: d.update()
        for b in cls.Bombs[:]: b.update()
        for e in cls.Explosions[:]: e.update()
        Player.triggerTile()
    
class GameState:
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

class Sky:
    dayColor = numpy.array([0.72, 0.68, 0.38])
    nightColor = numpy.array([0.01, 0.00, 0.03])
    phaseDuration = 30
    startTime = time.time()

    @classmethod
    def getPhase(cls):
        elapsedTime = time.time() - cls.startTime
        fullCycleTime = cls.phaseDuration * 2
        cycleTime = elapsedTime % fullCycleTime

        isNight = cycleTime >= cls.phaseDuration
        progress = (cycleTime % cls.phaseDuration) / cls.phaseDuration

        return isNight, progress
    
    @classmethod
    def updateBackground(cls):
        isNight, progress = cls.getPhase()

        if isNight:
            currentColor = cls.dayColor + (cls.nightColor - cls.dayColor) * progress

        else:
            currentColor = cls.nightColor + (cls.dayColor - cls.nightColor) * progress

        glClearColor(*currentColor, 1)

def keyboardListener(key, x, y):

    if key == b'w':  
        Player.moveForward()
    
    if key == b's':
        Player.moveBackward()

    if key == b'a':
        Player.turnLeft()

    if key == b'd':
        Player.turnRight()

    if key == b'=':
        Camera.radius += 5

    if key == b'-':
        Camera.radius -= 5

    if key == b' ':
        Gun.shoot()
    
    if key == b'b':
        Bomb(Player.x, Player.z)

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
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        Camera.playerPOV = not Camera.playerPOV
            

def animate():
    Game.update()
    glutPostRedisplay()

def display():
    Sky.updateBackground()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, Window.width, Window.height)

    # HomeBase.update()
    # HomeBase.checkEntry()

    Camera.setupCamera()
    if not GameState.inHomebase:
        Floor.draw()
    # HomeBase.draw()
    Player.draw()

    # Update survival logic
    if Player.immunity > 0:
        Player.immunity -= 1

    Gun.updateBullets()
    Gun.drawBullets()

    EnemyManager.update()
    EnemyManager.draw()

    for b in Game.Bombs: b.draw()
    for e in Game.Explosions: e.draw()

    HUD.draw()
    
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
# TEST SP AWNS - DELETE LATER
# Floor.getTile(300, 300).spawnObject(HealthPack)
# Floor.getTile(-300, 300).spawnObject(AmmoPack)
# Floor.getTile(300, -300).spawnObject(FoodPack)
# Floor.getTile(-300, -300).spawnObject(Key)
# TEST ENEMIES
# EnemyManager.spawnEnemy(500, 500, "mutant")
# EnemyManager.spawnEnemy(-500, 500, "tank")
# EnemyManager.spawnEnemy(0, 800, "shooter")
# EnemyManager.spawnEnemy(-800, -800, "shooter")
# EnemyManager.spawnEnemy(200, -600, "wanderer")

glutMainLoop()