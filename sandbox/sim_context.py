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

    def compute(self, ball_entity=None, robots=None):
        if not self.robot or not ball_entity: return False
        if robots is None: robots = []
        
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        frame[:] = (50, 100, 30) # Fondo de cancha
        
        fov = math.radians(60) 
        objects_to_draw = []
        
        # 1. Añadir la Pelota a la lista de renderizado
        dx = ball_entity.x - self.robot.x
        dy = ball_entity.y - self.robot.y
        dist = math.hypot(dx, dy)
        angle = math.atan2(dy, dx)
        diff_angle = (angle - self.robot.rangle + math.pi) % (2 * math.pi) - math.pi
        
        if abs(diff_angle) < math.radians(90):
            pixels_per_radian = self.frame_width / fov
            img_x = int(self.frame_width / 2 + diff_angle * pixels_per_radian)
            dist_safe = max(1.0, dist)
            r_calc = 1500 / dist_safe
            radius = int(min(120.0, r_calc))
            if radius > 0:
                objects_to_draw.append({
                    'dist': dist,
                    'x': img_x,
                    'radius': radius,
                    'color': (0, 100, 255) # Naranja en OpenCV BGR
                })

        # 2. Añadir los demás Robots (enemigos u otros aliados) para oclusión
        for other_r in robots:
            if other_r is self.robot:
                continue
            dx = other_r.x - self.robot.x
            dy = other_r.y - self.robot.y
            dist = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            diff_angle = (angle - self.robot.rangle + math.pi) % (2 * math.pi) - math.pi
            
            if abs(diff_angle) < math.radians(90):
                pixels_per_radian = self.frame_width / fov
                img_x = int(self.frame_width / 2 + diff_angle * pixels_per_radian)
                dist_safe = max(1.0, dist)
                # Escalar el radio visual en base a su radio físico relativo a la pelota
                r_calc = (other_r.radius / ball_entity.radius) * 1500 / dist_safe
                radius = int(min(240.0, r_calc))
                
                if radius > 0:
                    # Invertir color RGB a BGR para OpenCV
                    v = 0.1
                    bgr_color = (other_r.team_color[2] * v, other_r.team_color[1] * v, other_r.team_color[0] * v)
                    objects_to_draw.append({
                        'dist': dist,
                        'x': img_x,
                        'radius': radius,
                        'color': bgr_color
                    })

        # 3. Painter's Algorithm: Ordenar de más lejos a más cerca
        objects_to_draw.sort(key=lambda obj: obj['dist'], reverse=True)
        
        # 4. Dibujarlo todo en orden
        for obj in objects_to_draw:
            cv2.circle(frame, (obj['x'], self.frame_height // 2), obj['radius'], obj['color'], -1)

        # Evaluar la visión sobre la imagen resultante
        self._detectar_pelota(frame)
        return True

    def show_debug(self):
        super().show_debug()

    def cleanup(self):
        super().cleanup()
