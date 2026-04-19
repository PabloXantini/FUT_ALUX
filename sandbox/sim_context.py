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
    def __init__(self, debug: bool = True, team_color: str = "blue"):
        super().__init__(debug=debug, team_color=team_color)
        self.motors = MockMotorController()
        
        class DummyCap:
            def release(self): pass
        self.cap = DummyCap() # Mock de cámara física
        
        self.estado_label: str    = "Iniciando Simulación..."
        self.frame_width: int     = 320
        self.frame_height: int    = 240
        self.frame_debug          = None
        
        # Enlace a la entidad cinemática
        self.robot = None

        # Delegar responsabilidades de renderizado a la cámara virtual
        self.camera = VirtualCamera(
            width=self.frame_width, 
            height=self.frame_height, 
            fov_degrees=100
        )

    def link_robot(self, robot_entity):
        self.robot = robot_entity

    def compute(self, state=None):
        if not self.robot or not state or not state.ball: return False
        
        # Excluir a sí mismo de los objetos a dibujar
        other_robots = [r for r in state.robots if r is not self.robot]
        
        # Construir state filtrado conservando todos los elementos en la cache
        from sandbox.sim_cache import SimState
        filtered_state = SimState(ball=state.ball, robots=other_robots, goals=state.goals)
        
        # Encargar la renderización a la VirtualCamera pasándole la cache de estado
        frame = self.camera.render(observer=self.robot, state=filtered_state)

        # Evaluar la visión sobre la imagen resultante (con distorsión inyectada)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        result, self.frame_debug = self.vision.detect(frame, hsv, self.debug)
        
        # Volcar estado modular de vuelta a contexto para FSM en entorno simulado
        self.ball_detected = result['ball_detected']
        self.offset_x = result['offset_x']
        self.radius = result['radius']
        
        self.ally_goal_detected = result['ally_goal_detected']
        self.ally_goal_offset_x = result['ally_goal_offset_x']
        self.ally_goal_radius = result['ally_goal_radius']
        
        self.enemy_goal_detected = result['enemy_goal_detected']
        self.enemy_goal_offset_x = result['enemy_goal_offset_x']
        self.enemy_goal_radius = result['enemy_goal_radius']
        
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
