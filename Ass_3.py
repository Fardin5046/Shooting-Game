from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math
import random

# =====================
# Global Configuration
# =====================
WINDOW_W, WINDOW_H = 1000, 800
ASPECT = WINDOW_W / WINDOW_H
fovY = 120

# World/grid
GRID_LENGTH = 600
CELL = 80
WALL_H = 120

# Player & gameplay
player_pos = [0.0, 0.0]
player_angle = 0.0            # 0° faces +X
player_speed = 6.0
turn_speed =3.0

# Gun/bullets
bullet_speed = 4.0
bullet_size = 13.0
bullets = []

# Enemies
ENEMY_COUNT = 5
enemy_speed = 0.1
enemies = []
ENEMY_MIN_SPAWN_R = GRID_LENGTH * 0.3
ENEMY_MAX_SPAWN_R = GRID_LENGTH * 0.85

# Game state
life = 5
score = 0
bullets_missed = 0
game_over = False
MAX_MISSED = 10

# Cheat/Camera
cheat_auto = False   # spin + auto-fire
cheat_vision = False # extra head lift / follow — visible only in FPS & when cheat_auto is ON
first_person = False

cam_radius = 500.0
cam_angle = math.radians(90.0)

shoot_cooldown_frames = 0

random.seed(423)

# one re-usable quadric (avoid allocating each draw)
_q = None
def Q():
    global _q
    if _q is None:
        _q = gluNewQuadric()
    return _q

# =====================
# Utility
# =====================
def deg2rad(d):
    return d * math.pi / 180.0

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def angle_wrap_deg(a):
    while a < 0:
        a += 360
    while a >= 360:
        a -= 360
    return a

# =====================
# Text Overlay
# =====================
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# =====================
# Drawing helpers
# =====================
def draw_checker_grid():
    glPushMatrix()
    glBegin(GL_QUADS)
    for i in range(-GRID_LENGTH, GRID_LENGTH, CELL):
        for j in range(-GRID_LENGTH, GRID_LENGTH, CELL):
            c = ((i // CELL) + (j // CELL)) & 1
            if c == 0:
                glColor3f(0.6, 0.4, 0.8)  # purple
            else:
                glColor3f(0.92, 0.92, 0.92)
            glVertex3f(i, j + CELL, 0)
            glVertex3f(i + CELL, j + CELL, 0)
            glVertex3f(i + CELL, j, 0)
            glVertex3f(i, j, 0)
    glEnd()
    glPopMatrix()

def draw_boundaries():
    glColor3f(0.35, 0.2, 0.5)
    glBegin(GL_QUADS)
    # +Y wall
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, WALL_H)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, WALL_H)
    # -Y wall
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, WALL_H)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, WALL_H)
    # +X wall
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, WALL_H)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, WALL_H)
    # -X wall
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, WALL_H)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, WALL_H)
    glEnd()

# def draw_player(first_person_view=False):
#     """
#     Player composed of: sphere head, cylinder arms, cuboid torso/legs.
#     In first person we hide the body so the camera never sits inside it.
#     """
#     glPushMatrix()
#     glTranslatef(player_pos[0], player_pos[1], 0)
#
#     # Rotate full body to face player_angle (0°=+X)
#     glRotatef(player_angle, 0, 0, 1)
#
#     if game_over:
#         glRotatef(90, 1, 0, 0)
#
#     # ---------- third-person full body ----------
#     if not first_person_view:
#         # Torso (green cuboid)
#         glPushMatrix()
#         glTranslatef(0, 50, 30)
#         glColor3f(0.0, 0.55, 0.0)
#         glScalef(50, 25, 800)            # width, depth, height
#         glutSolidCube(1)
#         glPopMatrix()
#
#         # Head (black sphere)
#         glPushMatrix()
#         glTranslatef(0, 0, 85)
#         glColor3f(0.0, 0.0, 0.0)
#         gluSphere(Q(), 15, 20, 20)
#         glPopMatrix()
#
#         # Shoulder spheres + arms (cylinders)
#         for side in (-1, 1):  # -1 = left, 1 = right (Y axis)
#             glPushMatrix()
#             glTranslatef(0, side * 18, 35)
#             # shoulder joint
#             glColor3f(0.95, 0.85, 0.72)
#             gluSphere(Q(), 6.5, 18, 16)
#             # upper arm
#             glRotatef(90, 0, 1, 0)   # point along +X
#             gluCylinder(Q(), 5.5, 5.5, 22, 16, 6)
#             # forearm + hand
#             glTranslatef(22, 0, 0)
#             gluCylinder(Q(), 5.2, 5.2, 18, 16, 6)
#             glTranslatef(18, 0, 0)
#             gluSphere(Q(), 6.2, 18, 16)
#             glPopMatrix()
#
#         # Legs (blue cuboids)
#         for side in (-8, 8):
#             glPushMatrix()
#             glTranslatef(side, -4, -26)
#             # glColor3f(0.0, 0.0, 0.85)
#             # glScalef(12, 12, 30)
#             # glutSolidCube(1)
#             glColor3f(1, 1, 0)
#             glScalef(2, 2, 2)
#             glRotatef(180, 0, 1, 0)  # parameters are: angle, x, y, z
#             gluCylinder(gluNewQuadric(), 40, 5, 150, 10, 10)
#             glPopMatrix()
#
#         # Backpack (dark green)
#         # glPushMatrix()
#         # glTranslatef(-10, 0, 25)
#         # glColor3f(0.0, 0.4, 0.1)
#         # glScalef(14, 12, 32)
#         # glutSolidCube(1)
#         # glPopMatrix()
#
#         # Gun (cylinder)
#         glPushMatrix()
#         glTranslatef(20, 0, 36)
#         glRotatef(90, 0, 1, 0)  # along +X
#         glColor3f(0.45, 0.45, 0.45)
#         gluCylinder(Q(), 3.2, 3.2, 42, 16, 6)
#         glTranslatef(42, 0, 0)
#         gluSphere(Q(), 3.2, 16, 12)
#         glPopMatrix()
#
#     # ---------- first-person view: draw only a simple gun ----------
#     else:
#         glPushMatrix()
#         glTranslatef(10, -14, 32)
#         glRotatef(90, 0, 1, 0)   # barrel along +X
#         glColor3f(0.45, 0.45, 0.45)
#         gluCylinder(Q(), 3.3, 3.3, 40, 16, 6)  # barrel
#         glTranslatef(-12, 0, 0)
#         glColor3f(0.2, 0.2, 0.2)
#         gluCylinder(Q(), 7, 7, 12, 16, 6)     # body
#         glPopMatrix()
#
#     glPopMatrix(w)


# def draw_player(first_person_view=False):
#     """
#     Corrected player model:
#       - head: black sphere
#       - torso: green cuboid
#       - arms: two skin-colored cylinder arms (hand = sphere)
#       - legs: TWO BLUE cylinders (visible) + blue foot caps
#       - gun: thicker grey cylinder
#     First-person: only forearms + hands + gun + tiny front head cap
#     """
#     S = 1.35                     # global scale (tweak 1.1 - 1.6)
#     quad = gluNewQuadric()       # one quadric reused in this function
#
#     glPushMatrix()
#     glTranslatef(player_pos[0], player_pos[1], 0.0)
#     glRotatef(player_angle, 0, 0, 1)
#     if game_over:
#         glRotatef(90, 1, 0, 0)
#
#     # Uniformly scale whole model so we can easily make it slightly larger/smaller
#     glScalef(S, S, S)
#
#     if not first_person_view:
#         # ===== Torso (green cuboid) =====
#         glPushMatrix()
#         glTranslatef(0.0, 0.0, 36.0)   # torso center height
#         glColor3f(0.0, 0.55, 0.0)
#         glScalef(20.0, 36.0, 56.0)     # depth (X), width (Y), height (Z)
#         glutSolidCube(1.0)
#         glPopMatrix()
#
#         # ===== Head (black sphere) =====
#         glPushMatrix()
#         glTranslatef(0.0, 0.0, 72.0)   # above torso
#         glColor3f(0.0, 0.0, 0.0)
#         gluSphere(quad, 12.0, 24, 20)
#         glPopMatrix()
#
#         # ===== Arms (LEFT and RIGHT). Each arm fully contained in its push/pop. =====
#         for side in (-1, 1):
#             glPushMatrix()
#             # shoulder anchor: (x, y, z)
#             glTranslatef(0.0, side * 20.0, 46.0)
#             # align cylinders along +X (forward)
#             glRotatef(90.0, 0.0, 1.0, 0.0)
#
#             # skin color for arm
#             glColor3f(0.95, 0.85, 0.72)
#
#             # Upper arm
#             gluCylinder(quad, 3.6, 3.6, 20.0, 16, 6)
#
#             # Move to forearm start
#             glTranslatef(20.0, 0.0, 0.0)
#             gluCylinder(quad, 3.4, 3.4, 18.0, 16, 6)
#
#             # Move to hand and draw it
#             glTranslatef(18.0, 0.0, 0.0)
#             gluSphere(quad, 5.0, 18, 16)
#
#             glPopMatrix()
#
#         # ===== Legs (BLUE cylinders) =====
#         # place hips slightly out on Y, under the torso (so legs are visible)
#         hip_z = 10.0
#         leg_radius = 6.0
#         leg_length = 44.0
#         for side in (-1, 1):
#             glPushMatrix()
#             # hips: (x = 0), y = left/right, z = hip height
#             glTranslatef(0.0, side * 9.0, hip_z)
#             glColor3f(0.0, 0.0, 0.85)   # blue color for leg + foot
#
#             # rotate so cylinder goes downwards from hip
#             glRotatef(180.0, 1.0, 0.0, 0.0)
#             # draw leg (from hip downward)
#             gluCylinder(quad, leg_radius, leg_radius, leg_length, 20, 6)
#
#             # foot cap at the bottom of the leg
#             glTranslatef(0.0, 0.0, -leg_length)
#             gluSphere(quad, leg_radius + 0.1, 14, 12)
#
#             glPopMatrix()
#
#         # ===== Gun (held near chest) =====
#         glPushMatrix()
#         glTranslatef(22.0, 0.0, 46.0)     # in front / chest height
#         glRotatef(90.0, 0.0, 1.0, 0.0)    # point along +X
#         glColor3f(0.45, 0.45, 0.45)       # gun color (gray)
#         gluCylinder(quad, 4.6, 4.6, 44.0, 20, 6)   # slightly thicker than arm
#         glTranslatef(44.0, 0.0, 0.0)
#         gluSphere(quad, 4.6, 16, 12)
#         glPopMatrix()
#
#     # ---------- FIRST-PERSON: only forearms + hands + gun + tiny head front ----------
#     else:
#         # Forearms & hands
#         for side in (-1, 1):
#             glPushMatrix()
#             # place each forearm a little left/right of center in FP view
#             glTranslatef(12.0, side * 6.5, 22.0)
#             glRotatef(90.0, 0.0, 1.0, 0.0)
#             glColor3f(0.95, 0.85, 0.72)
#             gluCylinder(quad, 3.4, 3.4, 18.0, 16, 6)  # forearm
#             glTranslatef(18.0, 0.0, 0.0)
#             gluSphere(quad, 5.0, 18, 16)              # hand
#             glPopMatrix()
#
#         # Gun in the middle
#         glPushMatrix()
#         glTranslatef(18.0, 0.0, 24.0)
#         glRotatef(90.0, 0.0, 1.0, 0.0)
#         glColor3f(0.45, 0.45, 0.45)
#         gluCylinder(quad, 4.6, 4.6, 40.0, 20, 6)
#         glTranslatef(40.0, 0.0, 0.0)
#         gluSphere(quad, 4.6, 16, 12)
#         glPopMatrix()
#
#         # tiny front-cap of the head (so a little bit of head is visible)
#         glPushMatrix()
#         glTranslatef(6.0, 0.0, 30.0)
#         glScalef(1.0, 1.0, 0.6)
#         glColor3f(0.0, 0.0, 0.0)
#         gluSphere(quad, 6.0, 18, 14)
#         glPopMatrix()
#
#     glPopMatrix()
#

#     # gluDeleteQuadric(quad)



def draw_enemy(e):
    x, y, base_r, ph = e['x'], e['y'], e['base_r'], e['phase']
    r = base_r + 6.0 * math.sin(ph)
    glPushMatrix()
    glTranslatef(x, y, 0)
    glColor3f(0.9, 0, 0)
    gluSphere(Q(), r, 20, 16)
    glTranslatef(0, 0, r * 0.95)
    glColor3f(0, 0, 0)
    gluSphere(Q(), r * 0.55, 16, 12)
    glPopMatrix()

def draw_bullet(b):
    glPushMatrix()
    glTranslatef(b['x'], b['y'], 35)
    glColor3f(1.0, 0, 0)
    glScalef(bullet_size, bullet_size, bullet_size)
    glutSolidCube(1)
    glPopMatrix()

# =====================
# Spawning
# =====================
def random_spawn_point():
    while True:
        ang = random.uniform(0, 2 * math.pi)
        rad = random.uniform(ENEMY_MIN_SPAWN_R, ENEMY_MAX_SPAWN_R)
        x, y = player_pos[0] + rad * math.cos(ang), player_pos[1] + rad * math.sin(ang)
        if abs(x) < GRID_LENGTH - 50 and abs(y) < GRID_LENGTH - 50:
            return x, y

def respawn_enemy(idx=None):
    e = {'x': (random_spawn_point())[0], 'y': (random_spawn_point())[1], 'base_r': random.uniform(18, 30),
         'phase': random.uniform(0, math.pi * 2)}
    if idx is None:
        enemies.append(e)
    else:
        enemies[idx] = e

# =====================
# Input Handlers
# =====================
def keyboardListener(key, x, y):
    global player_angle, first_person, cheat_auto, cheat_vision, player_pos, game_over
    k = key.lower() if isinstance(key, bytes) else key

    if k == b'w' and not game_over:
        rad = deg2rad(player_angle)
        nx = player_pos[0] + player_speed * math.cos(rad)
        ny = player_pos[1] + player_speed * math.sin(rad)
        player_pos[0] = clamp(nx, -GRID_LENGTH+20, GRID_LENGTH-20)
        player_pos[1] = clamp(ny, -GRID_LENGTH+20, GRID_LENGTH-20)

    if k == b's' and not game_over:
        rad = deg2rad(player_angle)
        nx = player_pos[0] - player_speed * math.cos(rad)
        ny = player_pos[1] - player_speed * math.sin(rad)
        player_pos[0] = clamp(nx, -GRID_LENGTH+20, GRID_LENGTH-20)
        player_pos[1] = clamp(ny, -GRID_LENGTH+20, GRID_LENGTH-20)

    if k == b'a' and not game_over:
        player_angle = angle_wrap_deg(player_angle + turn_speed)

    if k == b'd' and not game_over:
        player_angle = angle_wrap_deg(player_angle - turn_speed)

    if k == b'c' and not game_over:
        cheat_auto = not cheat_auto

    if k == b'v' and not game_over:
        # Only meaningful when cheat mode is ON; in other cases, keep it False
        if cheat_auto:
            cheat_vision = not cheat_vision
        else:
            cheat_vision = False

    if k == b'r':
        reset_game()

def specialKeyListener(key, x, y):
    global cam_angle, cam_radius
    if key == GLUT_KEY_LEFT:
        cam_angle += math.radians(2.0)
    if key == GLUT_KEY_RIGHT:
        cam_angle -= math.radians(2.0)
    if key == GLUT_KEY_UP:
        cam_radius = clamp(cam_radius - 25.0, 200.0, 2000.0)
    if key == GLUT_KEY_DOWN:
        cam_radius = clamp(cam_radius + 25.0, 200.0, 2000.0)

def mouseListener(button, state, x, y):
    global first_person
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        fire_bullet()
        print("Player Bullet Fired!")
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person

# =====================
# Camera
# =====================
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        # FPS camera at head; when cheat is ON and cheat_vision True, lift & follow a bit stronger
        rad = deg2rad(player_angle)
        base_eye_z = 68.0
        if cheat_auto and cheat_vision:
            eye_z = base_eye_z + 20.0
            eye_x = player_pos[0] + 8.0 * math.cos(rad)
            eye_y = player_pos[1] + 8.0 * math.sin(rad)
        else:
            eye_z = base_eye_z
            eye_x = player_pos[0] + 6.0 * math.cos(rad)
            eye_y = player_pos[1] + 6.0 * math.sin(rad)

        center_x = eye_x + 200 * math.cos(rad)
        center_y = eye_y + 200 * math.sin(rad)
        center_z = eye_z
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 0, 1)
    else:
        eye_x = cam_radius * math.cos(cam_angle)
        eye_y = cam_radius * math.sin(cam_angle)
        eye_z = 550.0
        gluLookAt(eye_x, eye_y, eye_z, player_pos[0], player_pos[1], 0, 0, 0, 1)

# =====================
# Game Logic
# =====================
def reset_game():
    global life, score, bullets_missed, game_over, bullets, enemies
    global player_pos, player_angle, cheat_auto, cheat_vision, first_person
    life = 5
    score = 0
    bullets_missed = 0
    game_over = False
    bullets = []
    enemies = []
    player_pos = [0.0, 0.0]
    player_angle = 0.0
    cheat_auto = False
    cheat_vision = False
    first_person = False
    for _ in range(ENEMY_COUNT):
        respawn_enemy()

def fire_bullet():
    global shoot_cooldown_frames
    if shoot_cooldown_frames > 0:
        return
    rad = deg2rad(player_angle)
    # spawn from in front of player so it doesn't collide immediately
    bx = player_pos[0] + 90 * math.cos(rad)
    by = player_pos[1] + 90 * math.sin(rad)
    bullets.append({'x': bx, 'y': by, 'ang': player_angle})
    shoot_cooldown_frames = 4

def enemy_in_line_of_sight(threshold_cos=0.994):  # ~6°
    if not enemies:
        return False
    fr = deg2rad(player_angle)
    fx, fy = math.cos(fr), math.sin(fr)
    best = None
    for e in enemies:
        vx, vy = e['x'] - player_pos[0], e['y'] - player_pos[1]
        d = math.hypot(vx, vy)
        if d < 1e-5:
            continue
        cosang = (fx * vx + fy * vy) / d
        if cosang > threshold_cos:
            if best is None or d < best:
                best = d
    return best is not None

def update_cheat():
    global player_angle
    if cheat_auto and not game_over:
        # spin continuously (full 360 over time)
        player_angle = angle_wrap_deg(player_angle - 2.5)
        # auto-fire when an enemy is roughly in front
        if enemy_in_line_of_sight():
            fire_bullet()

def update_bullets():
    global bullets, bullets_missed, score, game_over
    alive = []
    for b in bullets:
        rad = deg2rad(b['ang'])
        b['x'] += bullet_speed * math.cos(rad)
        b['y'] += bullet_speed * math.sin(rad)
        if abs(b['x']) > GRID_LENGTH or abs(b['y']) > GRID_LENGTH:
            bullets_missed += 1
            print(f"Bullet missed: {bullets_missed}")
            if not cheat_auto:  # don't count missed bullets in cheat mode
                if bullets_missed >= MAX_MISSED:
                    game_over = True
            continue
        hit = False
        for i, e in enumerate(enemies):
            r = e['base_r'] + 6.0 * math.sin(e['phase'])
            if math.hypot(b['x'] - e['x'], b['y'] - e['y']) < (r + bullet_size * 0.6):
                score += 1
                respawn_enemy(i)
                hit = True
                break
        if not hit:
            alive.append(b)
    bullets = alive

def update_enemies():
    global life, game_over
    for i, e in enumerate(enemies):
        e['phase'] += 0.20
        vx = player_pos[0] - e['x']
        vy = player_pos[1] - e['y']
        d = math.hypot(vx, vy)
        if d > 1e-5:
            e['x'] += (vx / d) * enemy_speed
            e['y'] += (vy / d) * enemy_speed
        r = e['base_r'] + 6.0 * math.sin(e['phase'])
        if  cheat_auto==False:
            if d < (r + 28):
                life -= 1
                print(f"Remaining Player life: {life}")
                if life <= 0:
                    game_over = True
                respawn_enemy(i)

def idle():
    global shoot_cooldown_frames
    if shoot_cooldown_frames > 0:
        shoot_cooldown_frames -= 1
    if not game_over:
        update_cheat()     # <<< enables 360° spin + auto-fire
        update_bullets()
        update_enemies()
    glutPostRedisplay()

# =====================
# Display
# =====================
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_W, WINDOW_H)

    setupCamera()
    draw_checker_grid()
    draw_boundaries()
    # draw player (hide body in first-person)
    draw_player(first_person_view=first_person)
    for e in enemies: draw_enemy(e)
    for b in bullets: draw_bullet(b)


    if not game_over:
        draw_text(10, WINDOW_H - 30, f"Player life remaining: {life}")
        draw_text(10, WINDOW_H - 60, f"Game Score: {score}")
        draw_text(10, WINDOW_H - 90, f"Player Bullets Missed: {bullets_missed}/{MAX_MISSED}")

    if first_person and cheat_auto:
        draw_text(10, WINDOW_H - 90,"")
    if game_over:
        draw_text(10, WINDOW_H - 30, f"Game is Over. Your Score is : {score}")
        draw_text(10, WINDOW_H - 60, 'Please Press "R" to restart')



    glutSwapBuffers()


def init_gl():
    glClearColor(0.05, 0.05, 0.08, 1)
    glEnable(GL_DEPTH_TEST)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(300, 50)
    glutCreateWindow(b"Bullet Frenzy OpenGL")

    init_gl()
    reset_game()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()
