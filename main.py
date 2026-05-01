# Create window - Done
# Make ground
# Make camera - Done (3rd POV)
# See ground
# Make player - Done
# See player - Done
# Move player - Done

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import numpy 
 
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
    height = 800

class Tile:
    length = width = 150
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.object = None
        base = random.uniform(0.30, 0.45)
        r = base + random.uniform(0.03, 0.08)
        g = base + random.uniform(-0.01, 0.03)
        b = base + random.uniform(-0.04, 0.01)
        self.color = (r, g, b)

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

class AcidicTile(Tile):
    def __init__(self, x, z):
        super().__init__(x, z)
        self.offset = random.uniform(0, 10)
    
    def draw(self):
        pulse = (math.sin(time.time() * 0.5 + self.offset) + 1) / 2
        self.color = (0, 0.2 + (pulse * 0.8), 0)
        super().draw()

class Floor:
    rows = 50
    cols = 50
    length = rows * Tile.length
    width = cols * Tile.width
    x = 0
    z = 0
    startX = x - length/2
    startZ = z - length/2

    tiles = []

    currentX = startX
    currentZ = startZ
    for r in range(rows):
        row = []
        for c in range(cols):
            tileX = currentX + Tile.length/2
            tileZ = currentZ + Tile.width/2
            chance = random.random()
            if chance < 0.1:
                tile = AcidicTile(tileX, tileZ)
            else:
                tile = Tile(tileX, tileZ)
            row.append(tile)
            currentX += Tile.length
        tiles.append(row)
        currentX = startX
        currentZ += Tile.width

    @classmethod
    def draw(cls):
        for r in range(cls.rows):
            for c in range(cls.cols):
                cls.tiles[r][c].draw()
    @classmethod
    def getTile(cls, x, z):
        col = int((x - cls.startX) / Tile.length)
        row = int((z - cls.startZ) / Tile.width)
        if 0 <= row < cls.rows and 0 <= col < cls.cols:
            return cls.tiles[row][col]
        return None

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
    walkSpeed = 5
    turnSpeed = 3
    health = 100
    maxHealth = 100
    food = 0

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
    def draw(cls):
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
    def moveForward(cls):
        rad = math.radians(cls.angle)
        cls.x = cls.x + cls.walkSpeed * math.sin(rad)
        cls.z = cls.z + cls.walkSpeed * math.cos(rad)

    @classmethod
    def moveBackward(cls):
        rad = math.radians(cls.angle)
        cls.x = cls.x - cls.walkSpeed * math.sin(rad)
        cls.z = cls.z - cls.walkSpeed * math.cos(rad)

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
            if bullet.life <= 0:
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
        player.heal(30)

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
        Gun.addAmmo(10)

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

class Game:
    isImplemented = False

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
    glutPostRedisplay()


def display():
    Sky.updateBackground()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, Window.width, Window.height)

    Camera.setupCamera()
    Floor.draw()
    Player.draw()
    Gun.updateBullets()
    Gun.drawBullets()
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
glutMainLoop()