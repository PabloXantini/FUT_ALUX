import cv2
import numpy as np
import math

from utils.r_context import RobotContext
from sandbox.sim_actuators import MockMotorController

class SimContext(RobotContext):
    """
    Contexto simulado simplificado.
    Actúa únicamente como puente (MVC) entre el Robot físico simulado en 'game.py' y 
    los estados mentales del FSM (fsm.py).
    """
    def __init__(self, debug: bool = True):
        self.debug = debug
        self.motors = MockMotorController()
        
        class DummyCap:
            def release(self): pass
        self.cap = DummyCap() # Mock de cámara física
        
        # Variables públicas de MContext / Perception
        self.ball_detected: bool  = False
        self.offset_x: int | None = None
        self.radius: int          = 0
        
        self.estado_label: str    = "Iniciando Simulación..."
        self.frame_width: int     = 320
        self.frame_height: int    = 240
        self.frame_debug          = None
        
        # Enlace a la entidad cinemática
        self.robot = None

    def link_robot(self, robot_entity):
        self.robot = robot_entity

    def compute(self, ball_entity=None):
        if not self.robot or not ball_entity: return False
        
        # Mapeo del entorno a la visión sintética
        dx = ball_entity.x - self.robot.x
        dy = ball_entity.y - self.robot.y
        dist = math.hypot(dx, dy)
        angle_to_ball = math.atan2(dy, dx)
        diff_angle = (angle_to_ball - self.robot.rangle + math.pi) % (2 * math.pi) - math.pi
        
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        frame[:] = (50, 100, 30)
        
        # Emulando FOV de 60 grados
        fov = math.radians(60) 
        if abs(diff_angle) < math.radians(90):
            pixels_per_radian = self.frame_width / fov
            img_x = int(self.frame_width / 2 + diff_angle * pixels_per_radian)
            
            if dist < 1.0: dist = 1.0
            r_calc = 1500 / dist
            radius = int(min(120.0, r_calc))
            
            if radius > 0:
                cv2.circle(frame, (img_x, self.frame_height // 2), radius, (0, 100, 255), -1)

        # Evaluar la visión
        self._detectar_pelota(frame)
        return True

    def show_debug(self):
        super().show_debug()

    def cleanup(self):
        super().cleanup()
