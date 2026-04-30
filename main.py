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
    angle = 0
    height = 500
    radius = 700
    fovY = 120

    playerPOV = False

    @classmethod
    def setupCamera(cls):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if cls.playerPOV:
            gluPerspective(90, Window.width / Window.height, 10, 5000)
        else:
            gluPerspective(cls.fovY, Window.width / Window.height, 10, 2000) 
            
             
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if cls.playerPOV:
            rad = math.radians(Player.angle)
            eyeX = Player.x
            eyeY = Player.legHeight + Player.bodyHeight + Player.headRadius * 0.8
            eyeZ = Player.z

            targetX = eyeX + math.sin(rad) * 1000
            targetY = eyeY
            targetZ = eyeZ + math.cos(rad) * 1000
                    
            gluLookAt(eyeX, eyeY, eyeZ,
                        targetX, targetY, targetZ,
                        0, 1, 0)        
        else:
            rad = math.radians(cls.angle)
            camX = cls.radius * math.cos(rad)
            camY = cls.height
            camZ = cls.radius * math.sin(rad)

            gluLookAt(camX, camY, camZ,
                    0, 0, 0,
                    0, 1, 0)
            

class Window:
    width = 1000
    height = 800

class Tile:
    length = width = 150
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.color = (random.random(), random.random(), random.random())
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
            row.append(Tile(tileX, tileZ))
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

        if Camera.playerPOV:
            glColor3f(0.85, 0.85, 0.85)
            glPushMatrix()
            glTranslatef(0, cls.legHeight + (cls.bodyHeight / 1.3), 20)
            glRotatef(-10, 1, 0, 0)
            gluCylinder(gluNewQuadric(),
                        cls.gunBaseRadius,
                        cls.gunTopRadius,
                        cls.gunLength,
                        10, 10)
            
            # Hands attached to gun
            glColor3f(0.8, 0.5, 0.25)

            glPushMatrix()
            glTranslatef(15, -5, 0)
            gluCylinder(gluNewQuadric(), 5, 3, 30, 10, 10)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(-15, -5, 0)
            gluCylinder(gluNewQuadric(), 5, 3, 30, 10, 10)
            glPopMatrix()

            glPopMatrix()
            glPopMatrix()
            return

        glColor3f(0.33, 0.42, 0.188)
        glPushMatrix()
        glTranslatef(-cls.bodyWidth/4, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), cls.legBottomWidth / 2, cls.legBaseWidth / 2, cls.legHeight, 10, 10)
        glPopMatrix()

        # Left leg
        glColor3f(0.33, 0.42, 0.188)
        glPushMatrix()
        glTranslatef(cls.bodyWidth/4, 0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), cls.legBottomWidth / 2, cls.legBaseWidth / 2, cls.legHeight, 10, 10)
        glPopMatrix()


        # Body
        glColor3f(1, 0.71, 0.76)
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
    dayColor = numpy.array([0.95, 0.824, 0.06])
    nightColor = numpy.array([0.1, 0.1, 0.1])
    cycleDuration = 30
    startTime = time.time()

    @classmethod
    def isNight(cls):
        return (time.time() - cls.startTime) >= cls.cycleDuration
    
    @classmethod
    def updateBackground(cls):
        progress = min((((time.time()-cls.startTime)/cls.cycleDuration)), 1)
        currentColor = cls.dayColor+(cls.nightColor-cls.dayColor)*progress
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
glutCreateWindow(b"CSE423 | Lab03")
glEnable(GL_DEPTH_TEST)
glutDisplayFunc(display)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)
glutIdleFunc(animate)
glutMainLoop() 