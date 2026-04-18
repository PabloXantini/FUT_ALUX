import cv2
import numpy as np
from fsm import MContext
from utils.r_actuators import MotorController
from utils.r_cv import ColorDetector, ColorSegmentation
 
 
# ── Parámetros de visión ──────────────────────────────────────────────────────
 
CAMERA_SOURCE  = 0
CAP_BACKEND    = cv2.CAP_V4L2
SCALE_PERCENT  = 0.50
FLIP_FRAME     = True

# BALL
# Rango HSV de la pelota (naranja/rojo)
LOWER_BALL = np.array([0, 120, 0], dtype=np.uint8)
UPPER_BALL = np.array([20, 255, 255], dtype=np.uint8)
BALL_AREA_MIN   = 50

# GOALS
# Rango HSV de la portería (azul)
LOWER_GOAL1 = np.array([90, 50, 50], dtype=np.uint8)
UPPER_GOAL1 = np.array([130, 255, 255], dtype=np.uint8)
# Rango HSV de la portería (amarillo)
LOWER_GOAL2 = np.array([20, 100, 100], dtype=np.uint8)
UPPER_GOAL2 = np.array([30, 255, 255], dtype=np.uint8)
GOAL_AREA_MIN = 80

# ── Parámetros de comportamiento ──────────────────────────────────────────────

FRANJA_CENTRAL = 40   # píxeles de tolerancia lateral
RADIO_OBJETIVO = 30   # radio mínimo para considerar la pelota "cerca"
 
 
class RobotContext(MContext):
    """
    Contexto compartido entre todos los estados.
    Captura el frame, detecta la pelota, las porterías y expone los datos
    (offset_x, radius, etc.) + acceso a los motores.
    """
 
    def __init__(self, debug: bool = False, team_color: str = "blue"):
        super().__init__()
        self.debug = debug
        self.team_color = team_color.lower()
        self.motors = MotorController()
        self.cap    = cv2.VideoCapture(CAMERA_SOURCE, CAP_BACKEND)
 
        # Datos de percepción (actualizados en compute)
        self.ball_detected: bool  = False
        self.offset_x: int | None = None
        self.radius: int          = 0
        
        # Detección de porterías
        self.ally_goal_detected: bool  = False
        self.ally_goal_offset_x: int | None = None
        self.ally_goal_radius: int = 0
        
        self.enemy_goal_detected: bool  = False
        self.enemy_goal_offset_x: int | None = None
        self.enemy_goal_radius: int = 0

        self.frame_debug          = None
        self.frame_width: int     = 0
        self.frame_height: int    = 0
 
        # Estado legible para overlay
        self.estado_label: str    = "Iniciando..."
        
        # Configurar colores de portería según el equipo
        if self.team_color == "blue":
            ally_goal_lower = LOWER_GOAL1
            ally_goal_upper = UPPER_GOAL1
            enemy_goal_lower = LOWER_GOAL2
            enemy_goal_upper = UPPER_GOAL2
        else: # yellow
            ally_goal_lower = LOWER_GOAL2
            ally_goal_upper = UPPER_GOAL2
            enemy_goal_lower = LOWER_GOAL1
            enemy_goal_upper = UPPER_GOAL1

        # Inicializar Segmentadores - You can add kernel size here
        ball_seg = ColorSegmentation(LOWER_BALL, UPPER_BALL, BALL_AREA_MIN)
        ally_seg = ColorSegmentation(ally_goal_lower, ally_goal_upper, GOAL_AREA_MIN)
        enemy_seg = ColorSegmentation(enemy_goal_lower, enemy_goal_upper, GOAL_AREA_MIN)

        # Orquestador con todos los componentes
        self.vision = ColorDetector(ball_seg, ally_seg, enemy_seg, franja_central=FRANJA_CENTRAL)
 
    # ── Implementación MContext ───────────────────────────────────────────────
 
    def compute(self):
        """Captura y procesa un frame. Llámalo al inicio de cada ciclo."""
        ret, frame = self.cap.read()
        if not ret:
            return False
 
        if FLIP_FRAME:
            frame = cv2.flip(frame, 0)
 
        w = int(frame.shape[1] * SCALE_PERCENT)
        h = int(frame.shape[0] * SCALE_PERCENT)
        frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
 
        self.frame_width  = w
        self.frame_height = h
        
        # Análisis de Visión
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        result, self.frame_debug = self.vision.detect(frame, hsv, self.debug)
        
        # Volcar estado modular de vuelta a contexto para FSM
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

    # ── Debug visual ──────────────────────────────────────────────────────────
 
    def show_debug(self, window_name="Robot Vision"):
        if self.debug and self.frame_debug is not None:
            cv2.putText(self.frame_debug, self.estado_label,
                        (10, self.frame_height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow(window_name, self.frame_debug)
 
    # ── Limpieza ──────────────────────────────────────────────────────────────
 
    def cleanup(self):
        self.motors.cleanup()
        self.cap.release()
        cv2.destroyAllWindows()