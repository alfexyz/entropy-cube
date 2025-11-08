import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QVector3D
from OpenGL.GL import *
from OpenGL.GLU import *
import math


class Particle:
    def __init__(self, cube_size):
        self.radius = cube_size / 37
        self.pos = QVector3D(
            random.uniform(-cube_size, cube_size),
            random.uniform(-cube_size, cube_size),
            random.uniform(-cube_size, cube_size)
        )

        vx, vy, vz = [random.uniform(-1, 1) for _ in range(3)]
        self.vel = QVector3D(vx, vy, vz)
        if self.vel.length() != 0:
            self.vel.normalize()
        self.vel *= 0.01  # Minimum speed


class CubeWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cube_size = 1.0
        self.grid_divisions = 4
        self.particles = []
        self.speed = 1.0

        # Camera rotation
        self.rot_x = 20
        self.rot_y = 30

        # Mouse state
        self.last_mouse_pos = None
        self.is_dragging = False

        # Timer (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(8)

    k_B = 1.380649e-23  # Boltzmann constant

    def _lerp_blue_to_red(self, t: float):
        """Map t in [0,1] to blue->red. t=0 blue, t=1 red."""
        t = max(0.0, min(1.0, t))
        r = t
        g = 0.2 * (1.0 - t)  # keep some green to avoid purple mid-tones
        b = 1.0 - t
        return (r, g, b)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA) # Final color = (new_color × alpha) + (background_color × (1 - alpha))
        glEnable(GL_POINT_SMOOTH)
        glPointSize(5)
        glClearColor(0.05, 0.07, 0.1, 1.0)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL) # from now on, glColor3f will be calculated based on lighting, not color alone
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0]) # light from above, directional
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1]) # diffuse, pure white, full brightness

    # -------------------------------------------------
    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)  # for controlling camera lens
        glLoadIdentity() # resets identity matrix
        gluPerspective(45, w / max(h, 1), 0.1, 100.0) #45 degress fov, aspect ratio w / h
        glMatrixMode(GL_MODELVIEW) # MODELVIEW = moving objects themselves, not camera

    # -------------------------------------------------
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) #wipes "canvas" and resets camera to default
        glLoadIdentity()

        # Camera
        glTranslatef(0.0, 0.0, -5.0) # -5 so camera is not INSIDE the cube
        glRotatef(self.rot_x, 1, 0, 0) # rotating around x-axis
        glRotatef(self.rot_y, 0, 1, 0) # rotating around y-axis

        # Enables depth_test, allows writing to the depth buffer
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE) # For drawing solid things
        glDisable(GL_BLEND)

        # Spheres (lit)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])

        for p in self.particles:
            self.draw_sphere(p.pos.x(), p.pos.y(), p.pos.z(),
                             p.radius,
                             color=(0.0, 1, 0.2))

        # Wireframe cube (unlit)
        glDisable(GL_LIGHTING)
        self.draw_cube_wireframe(self.cube_size, color=(1, 1, 1))

        glEnable(GL_BLEND) # Turns on transparency
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)  # Depth buffering isn't used on transparent objects
        self.draw_colored_subcubes()  # lighting off for these
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)

    # -------------------------------------------------
    def draw_cube_wireframe(self, size, color=(1, 1, 1)):
        glColor3f(0.5, 0.7, 1.0)
        glBegin(GL_LINES)
        s = size
        for x in (-s, s):
            for y in (-s, s):
                glVertex3f(x, y, -s)
                glVertex3f(x, y, s)
        for x in (-s, s):
            for z in (-s, s):
                glVertex3f(x, -s, z)
                glVertex3f(x, s, z)
        for y in (-s, s):
            for z in (-s, s):
                glVertex3f(-s, y, z)
                glVertex3f(s, y, z)
        glEnd()

    # -------------------------------------------------
    def draw_colored_subcubes(self):
        """Color each subcube by local entropy contribution s_i = -k_B p_i ln p_i."""
        div = self.grid_divisions
        step = (2 * self.cube_size) / div
        start = -self.cube_size

        # Count particles per cell
        counts = [[[0 for _ in range(div)] for _ in range(div)] for _ in range(div)] #initialize matrix
        N = len(self.particles)
        if N == 0:
            # Nothing to color; draw very faint grid so you still see divisions
            glColor4f(0.2, 0.2, 0.8, 0.05)
            for i in range(div):
                for j in range(div):
                    for k in range(div):
                        x = start + i * step
                        y = start + j * step
                        z = start + k * step
                        self.draw_filled_cube(x, y, z, step)
            return

        for p in self.particles:
            i = int((p.pos.x() - start) / step)
            j = int((p.pos.y() - start) / step)
            k = int((p.pos.z() - start) / step)
            if 0 <= i < div and 0 <= j < div and 0 <= k < div:
                counts[i][j][k] += 1

        # Compute local entropy contributions s_i = -kB * p_i * ln(p_i)
        # and track max for normalization
        s_vals = [[[0.0 for _ in range(div)] for _ in range(div)] for _ in range(div)]
        s_max = 0.0
        for i in range(div):
            for j in range(div):
                for k in range(div):
                    n = counts[i][j][k]
                    if n > 0:
                        p = n / N
                        s = -self.k_B * p * math.log(p)
                    else:
                        s = 0.0
                    s_vals[i][j][k] = s
                    if s > s_max:
                        s_max = s

        # Avoid division by zero if all p_i are 0 except one (or tiny N)
        if s_max <= 0.0:
            s_max = 1.0

        # Draw cubes with alpha low so particles are clearly visible
        for i in range(div):
            for j in range(div):
                for k in range(div):
                    x = start + i * step
                    y = start + j * step
                    z = start + k * step
                    t = s_vals[i][j][k] / s_max  # normalize 0..1
                    r, g, b = self._lerp_blue_to_red(t)
                    glColor4f(r, g, b, 0.06)  # lower opacity per your request
                    self.draw_filled_cube(x, y, z, step)

    def draw_filled_cube(self, x, y, z, size):
        s = size
        x2, y2, z2 = x + s, y + s, z + s
        glBegin(GL_QUADS)

        # Front
        glVertex3f(x, y, z2); glVertex3f(x2, y, z2)
        glVertex3f(x2, y2, z2); glVertex3f(x, y2, z2)
        # Back
        glVertex3f(x, y, z); glVertex3f(x2, y, z)
        glVertex3f(x2, y2, z); glVertex3f(x, y2, z)
        # Left
        glVertex3f(x, y, z); glVertex3f(x, y, z2)
        glVertex3f(x, y2, z2); glVertex3f(x, y2, z)
        # Right
        glVertex3f(x2, y, z); glVertex3f(x2, y, z2)
        glVertex3f(x2, y2, z2); glVertex3f(x2, y2, z)
        # Top
        glVertex3f(x, y2, z); glVertex3f(x2, y2, z)
        glVertex3f(x2, y2, z2); glVertex3f(x, y2, z2)
        # Bottom
        glVertex3f(x, y, z); glVertex3f(x2, y, z)
        glVertex3f(x2, y, z2); glVertex3f(x, y, z2)
        glEnd()

    def draw_sphere(self, x, y, z, radius, color=(1.0, 0.0, 0.0)):
        """Draw a small 3D sphere at (x, y, z)."""
        glPushMatrix()
        glTranslatef(x, y, z)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 0.8, 0.6, 1.0])
        glMaterialfv(GL_FRONT, GL_SHININESS, 64)
        glColor3f(1.0, 0.3, 0.1)
        quad = gluNewQuadric()
        gluSphere(quad, radius, 16, 16) # draw the sphere out of 16 x 16 polygons
        gluDeleteQuadric(quad)
        glPopMatrix()

    # -------------------------------------------------
    def update_particles(self):
        for p in self.particles:
            p.pos += p.vel * self.speed

            # Smooth wall bounces
            if p.pos.x() < -self.cube_size + p.radius:
                p.pos.setX(-self.cube_size + p.radius)
                p.vel.setX(abs(p.vel.x()))
            elif p.pos.x() > self.cube_size - p.radius:
                p.pos.setX(self.cube_size - p.radius)
                p.vel.setX(-abs(p.vel.x()))

            if p.pos.y() < -self.cube_size + p.radius:
                p.pos.setY(-self.cube_size + p.radius)
                p.vel.setY(abs(p.vel.y()))
            elif p.pos.y() > self.cube_size - p.radius:
                p.pos.setY(self.cube_size - p.radius)
                p.vel.setY(-abs(p.vel.y()))

            if p.pos.z() < -self.cube_size + p.radius:
                p.pos.setZ(-self.cube_size + p.radius)
                p.vel.setZ(abs(p.vel.z()))
            elif p.pos.z() > self.cube_size - p.radius:
                p.pos.setZ(self.cube_size - p.radius)
                p.vel.setZ(-abs(p.vel.z()))

        # Collisions
        self.handle_collisions()
        self.update()

    def handle_collisions(self):
        n = len(self.particles)
        for i in range(n):
            for j in range(i + 1, n):
                p1 = self.particles[i]
                p2 = self.particles[j]
                diff = p1.pos - p2.pos
                dist = diff.length()

                if dist < (p1.radius + p2.radius) and dist > 0:
                    normal = diff / dist
                    v1, v2 = p1.vel, p2.vel
                    # reflects their velocity along normal
                    p1.vel = v1 - 2 * QVector3D.dotProduct(v1 - v2, normal) * normal * 0.5
                    p2.vel = v2 - 2 * QVector3D.dotProduct(v2 - v1, -normal) * (-normal) * 0.5
                    # if they are overlapping, separate them
                    overlap = 0.5 * ((p1.radius + p2.radius) - dist)
                    p1.pos += normal * overlap
                    p2.pos -= normal * overlap


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            dx = event.position().x() - self.last_mouse_pos.x()
            dy = event.position().y() - self.last_mouse_pos.y()
            self.rot_x += dy * 0.5
            self.rot_y += dx * 0.5
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False



class ControlPanel(QWidget):
    def __init__(self, cube_widget):
        super().__init__()
        self.cube_widget = cube_widget

        layout = QVBoxLayout()

        # Particle count
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(QLabel("Particles:"))
        self.particle_spin = QSpinBox()
        self.particle_spin.setRange(1, 200)
        self.particle_spin.setValue(50)
        self.particle_spin.valueChanged.connect(self.update_particles)
        h_layout1.addWidget(self.particle_spin)
        layout.addLayout(h_layout1)

        # Speed slider
        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(50)
        self.speed_slider.valueChanged.connect(self.update_speed)
        h_layout2.addWidget(self.speed_slider)
        layout.addLayout(h_layout2)

        self.setLayout(layout)
        self.update_particles()

    def update_particles(self):
        count = self.particle_spin.value()
        self.cube_widget.particles = [
            Particle(self.cube_widget.cube_size) for _ in range(count)
        ]

    def update_speed(self):
        self.cube_widget.speed = self.speed_slider.value() / 50


# =====================================================
# Main Application
# =====================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QWidget()
    layout = QHBoxLayout()

    cube_widget = CubeWidget()
    control_panel = ControlPanel(cube_widget)

    layout.addWidget(cube_widget, stretch=4)
    layout.addWidget(control_panel, stretch=1)

    main_window.setLayout(layout)
    main_window.resize(1000, 700)
    main_window.show()

    sys.exit(app.exec())
