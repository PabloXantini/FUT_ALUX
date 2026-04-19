import cv2
import numpy as np

class ColorSegmentator:
    """
    Componente modular responsable de segmentar un color específico utilizando HSV.
    """
    def __init__(self, lower, upper, min_area, kernel_size=5):
        self.lower = lower
        self.upper = upper
        self.min_area = min_area
        self.kernel = np.ones((kernel_size, kernel_size), np.uint8)

    def segment(self, hsv):
        """
        Aplica la máscara HSV y detecta el blob del color configurado.
        Retorna (centroid, contour, mask).
        """
        # 1. Crear máscara
        mask = cv2.inRange(hsv, self.lower, self.upper)
        
        # 2. Operaciones morfológicas
        cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel, iterations=2, dst=mask)
        cv2.morphologyEx(mask, cv2.MORPH_OPEN,  self.kernel, iterations=1, dst=mask)
        
        # 3. Extraer contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, None, mask
            
        best_contour = None
        max_area = 0.0
        """
        for c in contours:
            area = cv2.contourArea(c)
            if area > max_area:
                max_area = area
                best_contour = c
        """
        best_contour = max(contours, key=cv2.contourArea)
        max_area = cv2.contourArea(best_contour)
                
        # 4. Verificar umbral de área
        if max_area > self.min_area:
            M = cv2.moments(best_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                return (cx, cy), best_contour, mask
                    
        return None, None, mask

class CVDetector:
    """
    Orquestador de visión por computadora. Gestiona múltiples segmentadores
    y realiza cálculos geométricos de proximidad y alineación.
    """
    def __init__(self, ball_segmenter, ally_goal_segmenter, enemy_goal_segmenter, franja_central=40):
        self.ball_seg = ball_segmenter
        self.ally_seg = ally_goal_segmenter
        self.enemy_seg = enemy_goal_segmenter
        self.franja_central = franja_central

    def detect_proximity(self, contour, centroid, frame_width):
        """
        Calcula el offset horizontal y el radio (tamaño aparente) de un objeto.
        Retorna un diccionario con los valores calculados.
        """
        if centroid is None: return {
            'detected': False,
            'offset_x': None,
            'radius': 0
        }
        cx, _ = centroid
        offset_x = cx - (frame_width >> 1)
        _, radius = cv2.minEnclosingCircle(contour)
        
        return {
            'detected': True,
            'offset_x': offset_x,
            'radius': int(radius)
        }

    def detect(self, frame, hsv, debug=False):
        """
        Ejecuta la detección completa de la escena y retorna un diccionario estructurado.
        """
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        img_debug = frame.copy() if debug else None
        
        # 1. Ball Detection
        b_centroid, b_contour, _ = self.ball_seg.segment(hsv)
        ball_data = self.detect_proximity(b_contour, b_centroid, frame_width)
            
        # 2. Ally Goal Detection
        ag_centroid, ag_contour, _ = self.ally_seg.segment(hsv)
        ally_data = self.detect_proximity(ag_contour, ag_centroid, frame_width)
            
        # 3. Enemy Goal Detection
        eg_centroid, eg_contour, _ = self.enemy_seg.segment(hsv)
        enemy_data = self.detect_proximity(eg_contour, eg_centroid, frame_width)

        # 4. Debug Overlays
        if debug and img_debug is not None:
            img_cx = frame_width >> 1
            
            # Dibujar Ball
            if b_centroid:
                cv2.drawContours(img_debug, [b_contour], -1, (255, 100, 0), 2)
                cv2.circle(img_debug, b_centroid, 5, (0, 255, 0), -1)
                
            # Dibujar Ally Goal
            if ag_centroid:
                cv2.drawContours(img_debug, [ag_contour], -1, (0, 255, 0), 2)
                cv2.putText(img_debug, "ALLY", (ag_centroid[0] - 20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Dibujar Enemy Goal
            if eg_centroid:
                cv2.drawContours(img_debug, [eg_contour], -1, (0, 0, 255), 2)
                cv2.putText(img_debug, "ENEMY", (eg_centroid[0] - 25, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
            # Franja central
            lx = img_cx - self.franja_central
            rx = img_cx + self.franja_central
            cv2.line(img_debug, (lx, 0), (lx, frame_height), (255, 255, 255), 1)
            cv2.line(img_debug, (rx, 0), (rx, frame_height), (255, 255, 255), 1)

        result = {
            'ball': ball_data,
            'ally_goal': ally_data,
            'enemy_goal': enemy_data
        }
        
        return result, img_debug
