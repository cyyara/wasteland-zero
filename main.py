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
        base = random.uniform(0.30, 0.45)
        r = base + random.uniform(0.03, 0.08)
        g = base + random.uniform(-0.01, 0.03)
        b = base + random.uniform(-0.04, 0.01)
        # self.color = (random.random(), random.random(), random.random())
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
                

class Player:
    headRadius = 25
    bodyWidth = 65
    bodyHeight = 90
    handLength = 60
    handBaseRadius = 15
    handTopRadius = 5
    legHeight = 50
    legBottomWidth = 40
    legBaseWidth = 25

    gunBaseRadius = 10
    gunTopRadius = 5
    gunLength = 40

    x = 0
    z = 0
    angle = 0
    walkSpeed = 5
    turnSpeed = 3


    @classmethod
    def draw(cls):
        glPushMatrix()
        glTranslatef(cls.x, 0, cls.z)
        glRotatef(cls.angle, 0, 1, 0) 

        # Right leg
        glColor3f(0.08, 0.12, 0.35)
        glPushMatrix()
        glTranslatef(-cls.bodyWidth/4, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), cls.legBottomWidth / 2, cls.legBaseWidth / 2, cls.legHeight, 10, 10)
        glPopMatrix()

        # Left leg
        glColor3f(0.08, 0.12, 0.35)
        glPushMatrix()
        glTranslatef(cls.bodyWidth/4, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), cls.legBottomWidth / 2, cls.legBaseWidth / 2, cls.legHeight, 10, 10)
        glPopMatrix()


        # Body
        glColor3f(0.50, 0.10, 0.18)
        glPushMatrix()
        glTranslatef(0, cls.legHeight + cls.bodyHeight / 2, 0)
        glScalef(cls.bodyWidth, cls.bodyHeight, cls.bodyWidth)
        glutSolidCube(1)
        glPopMatrix()

        # Right hand
        glColor3f(0.8, 0.5, 0.25)
        glPushMatrix()
        glTranslatef(cls.bodyWidth/2 - cls.handBaseRadius, cls.legHeight + (cls.bodyHeight/1.4), 0)
        gluCylinder(gluNewQuadric(), cls.handBaseRadius, cls.handTopRadius, cls.handLength, 10, 10)
        glPopMatrix()

        # Left hand
        glColor3f(0.8, 0.5, 0.25)
        glPushMatrix()
        glTranslatef(-cls.bodyWidth/2 + cls.handBaseRadius, cls.legHeight + (cls.bodyHeight/1.4), 0)
        gluCylinder(gluNewQuadric(), cls.handBaseRadius, cls.handTopRadius, cls.handLength, 10, 10)
        glPopMatrix()

        # Head
        glColor3f(0, 0, 0)
        glPushMatrix()
        glTranslatef(0, cls.legHeight + cls.bodyHeight + cls.headRadius, 0)
        glutSolidSphere(cls.headRadius, 20, 20)
        glPopMatrix()

        # Gun
        glColor3f(0.85, 0.85, 0.85)
        glPushMatrix()
        glTranslatef(10, cls.legHeight + (cls.bodyHeight/1.2), cls.bodyWidth/2)
        gluCylinder(gluNewQuadric(), cls.gunBaseRadius, cls.gunTopRadius, cls.gunLength, 10, 10)
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