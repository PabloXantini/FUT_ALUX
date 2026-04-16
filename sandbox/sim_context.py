import math
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

import cv2
import numpy as np

from fsm import MContext
from utils.r_context import RobotContext
from sandbox.sim_actuators import MockMotorController

class SimContext(RobotContext):
    """
    Contexto simulado en 2D usando Pygame. 
    Imita el campo, genera una cámara sintética y la inyecta al _detectar_pelota REAL de OpenCV.
    """
    
    def __init__(self, debug: bool = True):
        # No usamos super().__init__() directamente para eludir cv2.VideoCapture(0)
        self.debug = debug
        self.motors = MockMotorController()
        
        class DummyCap:
            def release(self): pass
        self.cap = DummyCap() # Mock de cámara
        
        # Iniciar Pygame
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("FUT_ALUX - Sandbox Simulator")
        self.clock = pygame.time.Clock()
        
        # Variables públicas de Perception (actualizadas por _detectar_pelota de RobotContext)
        self.ball_detected: bool  = False
        self.offset_x: int | None = None
        self.radius: int          = 0
        self.estado_label: str    = "Iniciando Simulación..."
        self.frame_width: int     = 320
        self.frame_height: int    = 240
        self.frame_debug          = None
        
        # Radios físicos para colisiones y dibujado
        self.r_radius = 23  # Radio del robot (circular)
        self.b_radius = 12  # Radio de la pelota
        
        # Variables físicas simuladas
        self.rx = self.width / 2.0
        self.ry = self.height / 2.0
        self.rangle = 0.0  # Radianes (0 = derecha)
        
        self.bx = self.width / 2 + 100
        self.by = self.height / 2
        
        # Parámetros visuales de simulación "Cámara"
        self.fov = math.radians(60) # Campo de visión de 60 grados
        self.max_dist = 600.0
        
        # Estado de físicas
        self.b_vx = 0.0
        self.b_vy = 0.0
        self.dragging_ball = False

    def compute(self):
        # 1. Escuchar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Fuerza salida
        
        # 1.5 Física y arrastre de pelota
        mx, my = pygame.mouse.get_pos()
        mb1, _, _ = pygame.mouse.get_pressed()
        
        if mb1:
            dist_to_mouse = math.hypot(mx - self.bx, my - self.by)
            # Solo la agarramos si damos click cerca, o si ya la estábamos arrastrando
            if dist_to_mouse < 30 or self.dragging_ball:
                self.dragging_ball = True
                self.b_vx = mx - self.bx
                self.b_vy = my - self.by
                self.bx = mx
                self.by = my
        else:
            self.dragging_ball = False

        if not self.dragging_ball:
            # Inercia de la pelota
            self.bx += self.b_vx
            self.by += self.b_vy
            
            # Fricción del pasto
            self.b_vx *= 0.90
            self.b_vy *= 0.90
            
            # Rebote en las paredes
            if self.bx < 12: self.bx = 12; self.b_vx *= -0.8
            if self.bx > self.width - 12: self.bx = self.width - 12; self.b_vx *= -0.8
            if self.by < 12: self.by = 12; self.b_vy *= -0.8
            if self.by > self.height - 12: self.by = self.height - 12; self.b_vy *= -0.8

        # 2. Actualizar Física del robot según los motores
        robot_v_x = self.motors.v_forward * math.cos(self.rangle)
        robot_v_y = self.motors.v_forward * math.sin(self.rangle)
        
        self.rangle += self.motors.v_turn
        self.rx += robot_v_x
        self.ry += robot_v_y
        
        # Limitar robot a la pantalla
        self.rx = max(20, min(self.width - 20, self.rx))
        self.ry = max(20, min(self.height - 20, self.ry))

        # 2.5 Colisión Robot - Pelota (Circular real)
        dr_x = self.bx - self.rx
        dr_y = self.by - self.ry
        dist_rb = math.hypot(dr_x, dr_y)
        
        sum_radios = self.r_radius + self.b_radius
        if dist_rb < sum_radios and dist_rb > 0:
            overlap = sum_radios - dist_rb
            nx, ny = dr_x / dist_rb, dr_y / dist_rb
            
            if not self.dragging_ball:
                # El robot empuja la bola
                self.bx += nx * overlap
                self.by += ny * overlap
                self.b_vx += robot_v_x * 0.5 + nx * 2.0
                self.b_vy += robot_v_y * 0.5 + ny * 2.0
            else:
                # La bola detiene el robot temporalmente (bloqueo)
                self.rx -= nx * overlap
                self.ry -= ny * overlap

        # 3. Generar una vista de Cámara Sintética y mandarla a OpenCV Real
        dx = self.bx - self.rx
        dy = self.by - self.ry
        dist = math.hypot(dx, dy)
        angle_to_ball = math.atan2(dy, dx)
        diff_angle = (angle_to_ball - self.rangle + math.pi) % (2 * math.pi) - math.pi
        
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        frame[:] = (50, 100, 30) # Fondo Verde tipo cancha (BGR)
        
        # Si la bola está más o menos en el margen de 90 grados al frente
        if abs(diff_angle) < math.radians(90):
            pixels_per_radian = self.frame_width / self.fov
            img_x = int(self.frame_width / 2 + diff_angle * pixels_per_radian)
            
            if dist < 1.0: dist = 1.0
            r_calc = 1500 / dist
            radius = int(min(120.0, r_calc))
            
            if radius > 0:
                # Dibujamos en naranja intenso (0 B, 100 G, 255 R), esto en HSV es Hue ≈ 11.
                # Entrará perfecto en el rango UPPER_BALL / LOWER_BALL
                cv2.circle(frame, (img_x, self.frame_height // 2), radius, (0, 100, 255), -1)

        # === USAMOS LA LÓGICA DE DETECCIÓN REAL ===
        self._detectar_pelota(frame)

        # 4. Renderizado Visual Pygame (Opcionalmente guiado por show_debug, pero aquí lo hacemos continuo)
        self.screen.fill((30, 100, 40)) # Fondo verde "cancha"
        
        # Dibujar cono visual
        p1 = (self.rx, self.ry)
        p2 = (self.rx + math.cos(self.rangle - self.fov/2) * self.max_dist, 
              self.ry + math.sin(self.rangle - self.fov/2) * self.max_dist)
        p3 = (self.rx + math.cos(self.rangle + self.fov/2) * self.max_dist, 
              self.ry + math.sin(self.rangle + self.fov/2) * self.max_dist)
        pygame.draw.polygon(self.screen, (50, 130, 60), [p1, p2, p3])

        # Dibujar Pelota
        pygame.draw.circle(self.screen, (255, 100, 0), (int(self.bx), int(self.by)), self.b_radius)
        
        # Dibujar Robot (Circular)
        pygame.draw.circle(self.screen, (0, 0, 255), (int(self.rx), int(self.ry)), self.r_radius, 3) # Círculo azul
        
        # Orientación (Línea central)
        end_x = self.rx + math.cos(self.rangle) * (self.r_radius * 1.2)
        end_y = self.ry + math.sin(self.rangle) * (self.r_radius * 1.2)
        pygame.draw.line(self.screen, (255, 255, 255), (self.rx, self.ry), (end_x, end_y), 3)

        self.clock.tick(60) # 60 FPS
        return True

    def show_debug(self):
        # Dibujar textos informativos provenientes del FSM
        font = pygame.font.SysFont(None, 24)
        lbl = font.render(f"FSM: {self.estado_label}", True, (255, 255, 255))
        self.screen.blit(lbl, (10, 10))
        
        info = f"CV2 -> Det: {self.ball_detected} | Offset: {self.offset_x} | R: {self.radius}"
        lbl2 = font.render(info, True, (255, 255, 0))
        self.screen.blit(lbl2, (10, 40))
        
        pygame.display.flip()
        
        # Aprovechar el show_debug real si está corriendo en debug
        super().show_debug()

    def cleanup(self):
        super().cleanup()
        pygame.quit()
