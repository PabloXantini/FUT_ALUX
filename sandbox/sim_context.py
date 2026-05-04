import cv2

from utils.r_context import RobotContext
from sandbox.sim_actuators import MockMotorController
from sandbox.virtual_camera import VirtualCamera
from sandbox.sim_cache import SimState

class SimContext(RobotContext):
    """
    Contexto simulado simplificado.
    Actúa únicamente como puente (MVC) entre el Robot físico simulado en 'game.py' y 
    los estados mentales del FSM (fsm.py).
    """
    def __init__(self, debug: bool = True, name: str = 'robot', team_color: str = "blue"):
        super().__init__(debug=debug, name=name ,team_color=team_color)
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
            fov_degrees=120,
            pitch=30.0,
            camera_height=18.0
        )
        # Iluminación
        self.camera.set_light_level(
            ambient=0.4,
            diffuse=0.8,
            x=320, y=240, z=500 # Luz cenital simulada
        )
        self.camera.set_fisheye_params(k=-1.4, zoom=1.7)
        self.camera.set_motion_blur(strength=0.3, samples=3)

    def link_robot(self, robot_entity):
        self.robot = robot_entity

    def compute(self, state=None):
        if not self.robot or not state or not state.ball: return False
        
        # Excluir a sí mismo de los objetos a dibujar
        other_robots = [r for r in state.robots if r is not self.robot]
        
        # Construir state filtrado conservando todos los elementos en la cache
        filtered_state = SimState(ball=state.ball, robots=other_robots, goals=state.goals, pitch=state.pitch)
        
        # Encargar la renderización a la VirtualCamera pasándole la cache de estado
        frame = self.camera.render(observer=self.robot, state=filtered_state)

        # Evaluar la visión sobre la imagen resultante (con distorsión inyectada)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self.info, self.frame_debug = self.vision.detect(frame, hsv, self.debug)
        
        return True

    def _get_window_name(self):
        window_name = "Robot"
        if self.robot:
            if self.robot.color == (0, 0, 255):
                window_name = "Blue"
            elif self.robot.color == (255, 255, 0):
                window_name = "Yellow"
        return window_name

    def get_debug_frame(self):
        return super().get_debug_frame(window_name=self._get_window_name())

    def show_debug(self):
        super().show_debug(window_name=self._get_window_name())

    def cleanup(self):
        super().cleanup()
