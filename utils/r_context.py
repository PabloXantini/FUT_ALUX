import cv2
import numpy as np
from fsm import MContext
from utils.r_actuators import MotorController
from utils.r_cv import CVDetector, ColorSegmentator
 
 
# ── Parámetros de visión ──────────────────────────────────────────────────────
 
CAMERA_SOURCE  = 0
CAP_BACKEND    = cv2.CAP_V4L2
SCALE_PERCENT  = 0.50
FLIP_FRAME     = True
 
# ORANGE BALL
LOWER_BALL = np.array([0, 20, 0], dtype=np.uint8)
UPPER_BALL = np.array([27, 255, 255], dtype=np.uint8)
BALL_AREA_MIN   = 50
BALL_AREA_MINT  = 1
 
# GOALS
# BLUE COLOR
LOWER_GOAL1 = np.array([77, 123, 50], dtype=np.uint8)
UPPER_GOAL1 = np.array([120, 255, 200], dtype=np.uint8)
# YELLOW COLOR
LOWER_GOAL2 = np.array([28, 171, 139], dtype=np.uint8)
UPPER_GOAL2 = np.array([41, 255, 255], dtype=np.uint8)
GOAL_AREA_MIN = 80
 
# ── Parámetros de comportamiento ──────────────────────────────────────────────
 
FRANJA_CENTRAL = 30   # píxeles de tolerancia lateral
RADIO_OBJETIVO = 18   # radio mínimo para considerar la pelota "cerca"
 
 
class RobotContext(MContext):
    """
    Contexto compartido entre todos los estados.
    Almacena el estado de percepción en self.info y expone motores.
    """
 
    def __init__(self, debug: bool = False, name: str = 'robot', team_color: str = "blue"):
        super().__init__()
        self.debug = debug
        self.name = name
        self.team_color = team_color.lower()
        self.team_color_rgb = (255, 0, 0) if self.team_color == "blue" else (0, 255, 255)
        self.motors = MotorController()
        self.cap    = cv2.VideoCapture(CAMERA_SOURCE, CAP_BACKEND)
 
        # Diccionario central de percepción
        self.info = {
            'ball': {'detected': False, 'offset_x': None, 'radius': 0},
            'ally_goal': {'detected': False, 'offset_x': None, 'radius': 0},
            'enemy_goal': {'detected': False, 'offset_x': None, 'radius': 0}
        }

        self.frame_debug          = None
        self.frame_width: int     = 0
        self.frame_height: int    = 0
 
        # Estado legible para overlay
        self.estado_label: str    = "Iniciando..."
        
        # Configurar colores según equipo
        if self.team_color == "blue":
            ally_l, ally_u = LOWER_GOAL1, UPPER_GOAL1
            enemy_l, enemy_u = LOWER_GOAL2, UPPER_GOAL2
        else:
            ally_l, ally_u = LOWER_GOAL2, UPPER_GOAL2
            enemy_l, enemy_u = LOWER_GOAL1, UPPER_GOAL1
 
        # Inicializar Segmentadores
        ball_seg = ColorSegmentator(LOWER_BALL, UPPER_BALL, BALL_AREA_MINT)
        ally_seg = ColorSegmentator(ally_l, ally_u, GOAL_AREA_MIN)
        enemy_seg = ColorSegmentator(enemy_l, enemy_u, GOAL_AREA_MIN)
 
        # Orquestador
        self.vision = CVDetector(ball_seg, ally_seg, enemy_seg, franja_central=FRANJA_CENTRAL)
 
    def compute(self):
        """Captura y procesa un frame."""
        ret, frame = self.cap.read()
        if not ret: return False
 
        if FLIP_FRAME:
            frame = cv2.flip(frame, 0)
 
        w = int(frame.shape[1] * SCALE_PERCENT)
        h = int(frame.shape[0] * SCALE_PERCENT)
        frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_NEAREST)
 
        self.frame_width  = w
        self.frame_height = h
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        self.info, self.frame_debug = self.vision.detect(frame, hsv, self.debug)
        
        return True
 
    # ── Debug visual ──────────────────────────────────────────────────────────
 
    def get_debug_frame(self, window_name="POV:"):
        if self.debug and self.frame_debug is not None:
            frame = self.frame_debug.copy()
            # Combina el nombre de la ventana y el estado para mostrar en el mosaico/ventana
            cv2.putText(frame, f"{self.name} ({window_name})", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.team_color_rgb, 2)
            cv2.putText(frame, f"E: {self.estado_label}",
                        (10, self.frame_height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            return frame
        return None

    def show_debug(self, window_name="POV:"):
        frame = self.get_debug_frame(window_name)
        if frame is not None:
            cv2.imshow(f"{window_name} {self.name}", frame)
 
    # ── Limpieza ──────────────────────────────────────────────────────────────
 
    def cleanup(self):
        self.motors.cleanup()
        self.cap.release()
        cv2.destroyAllWindows()