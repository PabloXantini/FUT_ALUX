import cv2
import numpy as np
import math

from utils.r_context import RobotContext
from sandbox.sim_actuators import MockMotorController
from sandbox.virtual_camera import VirtualCamera

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

        # Delegar responsabilidades de renderizado a la cámara virtual
        self.camera = VirtualCamera(width=self.frame_width, height=self.frame_height, fov_degrees=100)

    def link_robot(self, robot_entity):
        self.robot = robot_entity

    def compute(self, ball_entity=None, robots=None):
        if not self.robot or not ball_entity: return False
        if robots is None: robots = []
        
        # Excluir a sí mismo de los objetos a dibujar
        other_robots = [r for r in robots if r is not self.robot]
        
        # Encargar la renderización 3D/FishEye a la VirtualCamera
        frame = self.camera.render(
            observer_x=self.robot.x,
            observer_y=self.robot.y,
            observer_angle=self.robot.rangle,
            ball_entity=ball_entity,
            other_robots=other_robots
        )

        # Evaluar la visión sobre la imagen resultante (con distorsión inyectada)
        self._detectar_pelota(frame)
        return True

    def show_debug(self):
        window_name = "Robot Vision"
        if self.robot:
            if self.robot.team_color == (0, 0, 255):
                window_name = "Robot Vision - Blue Team"
            elif self.robot.team_color == (255, 255, 0):
                window_name = "Robot Vision - Yellow Team"
            else:
                window_name = f"Robot Vision - {id(self.robot)}"
        super().show_debug(window_name=window_name)

    def cleanup(self):
        super().cleanup()
