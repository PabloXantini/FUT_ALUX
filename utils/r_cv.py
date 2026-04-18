import cv2
import numpy as np

class ColorSegmentation:
    """
    Componente modular responsable de segmentar un color específico utilizando HSV.
    """
    def __init__(self, lower, upper, min_area, kernel_size=5):
        self.lower = lower
        self.upper = upper
        self.min_area = min_area
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def segment(self, hsv, frame_width):
        """Aplica la máscara y detecta el blob del color configurado de forma optimizada."""
        # 1. inRange crea la matriz original
        mask = cv2.inRange(hsv, self.lower, self.upper)
        
        # 2. Operaciones morfológicas in-place usando dst=mask para evitar alocación de memoria (vital en RPi)
        cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel, iterations=2, dst=mask)
        cv2.morphologyEx(mask, cv2.MORPH_OPEN,  self.kernel, iterations=1, dst=mask)
        
        # 3. Extraer contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Early return si no hay ruido ni objetos
        if not contours:
            return False, None, 0, None
            
        best_contour = None
        max_area = 0.0
        
        # 4. Evitar el overhead de la función key= en max() de Python para acelerar el ciclo C
        for c in contours:
            area = cv2.contourArea(c)
            if area > max_area:
                max_area = area
                best_contour = c
                
        # 5. Computar centro y offset solamente si pasa el threshold
        if max_area > self.min_area:
            M = cv2.moments(best_contour)
            m00 = M["m00"]
            if m00 != 0:
                cx = int(M["m10"] / m00)
                # Bitwise right shift es más rapido que integer division (// 2)
                offset_x = cx - (frame_width >> 1)
                
                _, rf = cv2.minEnclosingCircle(best_contour)
                return True, offset_x, int(rf), best_contour
                    
        return False, None, 0, None

class ColorDetector:
    """
    Orquestador de múltiples segmentadores de color. Gestiona al proceso central
    combinando el frame crudo y la conversión HSV para alimentar a cada segmentador de la escena.
    """
    def __init__(self, ball_segmenter, ally_goal_segmenter, enemy_goal_segmenter, franja_central=40):
        self.ball_seg = ball_segmenter
        self.ally_seg = ally_goal_segmenter
        self.enemy_seg = enemy_goal_segmenter
        self.franja_central = franja_central

    def detect(self, frame, hsv, debug=False):
        """
        Calcula las variables principales inyectando el HSV y el Frame.
        """
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        img_debug = frame.copy() if debug else None
        
        # 1. ball detection
        ball_detected, b_offset, b_radius, ball_contour = self.ball_seg.segment(hsv, frame_width)
        # 2. ally goal detection
        ally_detected, ally_offset, ally_radius, ally_contour = self.ally_seg.segment(hsv, frame_width)
        # 3. enemy goal detection
        enemy_detected, enemy_offset, enemy_radius, enemy_contour = self.enemy_seg.segment(hsv, frame_width)

        # 4. Debug mode
        if debug and img_debug is not None:
            img_cx = frame_width >> 1

            if ball_detected and ball_contour is not None:
                cv2.drawContours(img_debug, [ball_contour], -1, (255, 0, 0), 2)
                cx = img_cx + b_offset
                cv2.circle(img_debug, (cx, frame_height >> 1), 5, (0, 255, 0), -1)
                
            if ally_detected and ally_contour is not None:
                cv2.drawContours(img_debug, [ally_contour], -1, (0, 255, 0), 2)
                cx = img_cx + ally_offset
                cv2.putText(img_debug, "ALLY GOAL", (cx - 30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
            if enemy_detected and enemy_contour is not None:
                cv2.drawContours(img_debug, [enemy_contour], -1, (0, 0, 255), 2)
                cx = img_cx + enemy_offset
                cv2.putText(img_debug, "ENEMY GOAL", (cx - 40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
            lx = img_cx - self.franja_central
            rx = img_cx + self.franja_central
            cv2.line(img_debug, (lx, 0), (lx, frame_height), (255, 255, 255), 1)
            cv2.line(img_debug, (rx, 0), (rx, frame_height), (255, 255, 255), 1)

        result = {
            # ball
            'ball_detected': ball_detected,
            'offset_x': b_offset,
            'radius': b_radius,
            # ally goal
            'ally_goal_detected': ally_detected,
            'ally_goal_offset_x': ally_offset,
            'ally_goal_radius': ally_radius,
            # enemy goal
            'enemy_goal_detected': enemy_detected,
            'enemy_goal_offset_x': enemy_offset,
            'enemy_goal_radius': enemy_radius
        }
        
        return result, img_debug

