import cv2
import numpy as np
from fsm import MContext
from utils.r_actuators import MotorController
 
 
# ── Parámetros de visión ──────────────────────────────────────────────────────
 
CAMERA_SOURCE  = 0
CAP_BACKEND    = cv2.CAP_V4L2
SCALE_PERCENT  = 0.50
FLIP_FRAME     = True
 
# Rango HSV de la pelota (naranja/rojo)
LOWER_BALL = np.array([0,   120,   0], dtype=np.uint8)
UPPER_BALL = np.array([20,  255, 255], dtype=np.uint8)
KERNEL     = np.ones((5, 5), np.uint8)
AREA_MIN   = 50
 
# ── Parámetros de comportamiento ──────────────────────────────────────────────
 
FRANJA_CENTRAL = 40   # píxeles de tolerancia lateral
RADIO_OBJETIVO = 30   # radio mínimo para considerar la pelota "cerca"
 
 
class RobotContext(MContext):
    """
    Contexto compartido entre todos los estados.
    Captura el frame, detecta la pelota y expone los datos
    (offset_x, radius, ball_detected) + acceso a los motores.
    """
 
    def __init__(self, debug: bool = False):
        super().__init__()
        self.debug = debug
        self.motors = MotorController()
        self.cap    = cv2.VideoCapture(CAMERA_SOURCE, CAP_BACKEND)
 
        # Datos de percepción (actualizados en compute)
        self.ball_detected: bool  = False
        self.offset_x: int | None = None
        self.radius: int          = 0
        self.frame_debug          = None
        self.frame_width: int     = 0
        self.frame_height: int    = 0
 
        # Estado legible para overlay
        self.estado_label: str    = "Iniciando..."
 
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
        self._detectar_pelota(frame)
        return True
 
    # ── Detección ─────────────────────────────────────────────────────────────
 
    def _detectar_pelota(self, frame):
        hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER_BALL, UPPER_BALL)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  KERNEL, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
 
        debug = frame.copy() if self.debug else None
        img_cx = frame.shape[1] // 2
        self.ball_detected = False
        self.offset_x      = None
        self.radius        = 0
 
        if contours:
            c    = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            if area > AREA_MIN:
                self.ball_detected = True
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    self.offset_x = cx - img_cx
                    (x, y), rf   = cv2.minEnclosingCircle(c)
                    self.radius  = int(rf)
                    
                    if self.debug:
                        cv2.drawContours(debug, [c], -1, (255, 0, 0), 2)
                        cv2.circle(debug, (cx, cy), 5, (0, 255, 0), -1)
                        cv2.circle(debug, (int(x), int(y)), self.radius,
                                   (0, 0, 255), 2)
 
        if self.debug:
            # Franja central de referencia
            lx = img_cx - FRANJA_CENTRAL
            rx = img_cx + FRANJA_CENTRAL
            cv2.line(debug, (lx, 0), (lx, frame.shape[0]), (255, 255, 255), 1)
            cv2.line(debug, (rx, 0), (rx, frame.shape[0]), (255, 255, 255), 1)
 
        self.frame_debug = debug
 
    # ── Debug visual ──────────────────────────────────────────────────────────
 
    def show_debug(self):
        if self.debug and self.frame_debug is not None:
            cv2.putText(self.frame_debug, self.estado_label,
                        (10, self.frame_height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.imshow("Robot Vision", self.frame_debug)
 
    # ── Limpieza ──────────────────────────────────────────────────────────────
 
    def cleanup(self):
        self.motors.cleanup()
        self.cap.release()
        cv2.destroyAllWindows()