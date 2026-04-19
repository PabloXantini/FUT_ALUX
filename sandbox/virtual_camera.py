import numpy as np
import cv2
import math

class VirtualCamera:
    """
    Motor gráfico encargado de generar frames de visión sintéticos en 2D.
    Soporta perspectiva, distancia, oclusión (Painter's Algorithm) y distorsión
    de lente estilo Ojo de Pescado (Barrel Distortion).
    """
    def __init__(self, width=320, height=240, fov_degrees=100, 
                 pitch=15.0, yaw=0.0, roll=0.0, camera_height=20.0):
        self.width = width
        self.height = height
        self.fov = math.radians(fov_degrees)
        
        # Orientación de la cámara (en radianes)
        self.pitch = math.radians(pitch)
        self.yaw_off = math.radians(yaw)
        self.roll = math.radians(roll)
        self.camera_height = camera_height

        # Precomputar parámetros de proyección
        # f = (width / 2) / tan(fov / 2)
        self.focal_length = (self.width / 2.0) / math.tan(self.fov / 2.0)
        self.cx = self.width / 2.0
        self.cy = self.height / 2.0
        
        # Precomputar mapas de remapeo para Ojo de Pescado (Fisheye Barrel Distortion)
        x, y = np.meshgrid(np.arange(self.width), np.arange(self.height))
        x_c = x - self.width / 2.0
        y_c = y - self.height / 2.0
        r = np.sqrt(x_c**2 + y_c**2)
        
        # Factor de compresión (k)
        k = 0.000015 
        
        # Calcular el radio máximo en las esquinas para estirar (hacer zoom) y tapar bordes negros
        max_r = np.sqrt((self.width / 2.0)**2 + (self.height / 2.0)**2)
        zoom_factor = 1 + k * max_r**2
        
        r_s = r * (1 + k * r**2)
        # Zoom-in dividiendo según cuánto se encogieron las orillas
        r_s = r_s / zoom_factor
        
        scale = r_s / np.maximum(r, 1e-5)
        self.map_x = (self.width / 2.0 + x_c * scale).astype(np.float32)
        self.map_y = (self.height / 2.0 + y_c * scale).astype(np.float32)
        
    def project_3d(self, x_world, y_world, z_world, observer):
        """Transforma coordenadas de mundo a coordenadas de imagen (u, v) y profundidad Z."""
        dx = x_world - observer.x
        dy = y_world - observer.y
        dz = z_world - self.camera_height
        
        # 1. Rotación por el Yaw total del robot + offset de cámara
        total_yaw = observer.rangle + self.yaw_off
        
        # En el motor de juego, rangle=0 apunta hacia la derecha (+X).
        # El vector frente (forward) es (cos, sin) y el vector derecha (right) es (-sin, cos).
        cos_y = math.cos(total_yaw)
        sin_y = math.sin(total_yaw)
        
        # Proyectar el vector relativo (dx, dy) sobre los ejes locales del robot
        # y_rel (adelante) = dx*cos + dy*sin
        # x_rel (derecha) = -dx*sin + dy*cos
        y_rel = dx * cos_y + dy * sin_y
        x_rel = -dx * sin_y + dy * cos_y
        z_rel = dz
        
        # Ahora y_rel es "adelante", x_rel es "derecha", z_rel es "arriba".
        
        # 2. Rotación por Pitch (inclinación x-axis local)
        cos_p = math.cos(self.pitch)
        sin_p = math.sin(self.pitch)
        
        # El pitch rota alrededor de x_rel. Afecta a y_rel y z_rel.
        # Si pitch > 0 (mirar hacia abajo), el suelo (z_rel bajo) se mueve hacia el centro.
        y_p = y_rel * cos_p - z_rel * sin_p
        z_p = y_rel * sin_p + z_rel * cos_p
        
        # 3. Mapeo a espacio de cámara OpenCV (Z adelante, X derecha, Y abajo)
        x_cam = x_rel
        y_cam = -z_p
        z_cam = y_p
        
        if z_cam <= 0.1: # Detrás de la cámara o muy cerca
            return None
            
        # 4. Proyección a píxeles
        u = (self.focal_length * x_cam / z_cam) + self.cx
        v = (self.focal_length * y_cam / z_cam) + self.cy
        
        return int(u), int(v), z_cam

    def _project_entity(self, observer, entity, color_bgr, shape_type="circle", base_size=12.0):
        """Calcula las coordenadas y métricas visuales para una entidad usando proyección 3D."""
        # Centro de la base en el suelo (Z=0)
        res_base = self.project_3d(entity.x, entity.y, 0, observer)
        if not res_base:
            return None
            
        u_base, v_base, z_dist = res_base
        
        # Punto superior (Z = z_height) para calcular la escala vertical real
        z_phys = getattr(entity, 'z_height', base_size)
        res_top = self.project_3d(entity.x, entity.y, z_phys, observer)
        
        if not res_top:
            # Si el tope está fuera pero la base no, aproximamos
            h_pix = (self.focal_length * z_phys / z_dist)
            v_top = int(v_base - h_pix)
        else:
            _, v_top, _ = res_top
            
        screen_h = abs(v_base - v_top)
        
        # Ancho basado en el tamaño físico (diámetro del robot o radio de la pelota)
        screen_w = (base_size * 2.0 * self.focal_length / z_dist)
        
        if screen_h > 0 and -self.width < u_base < self.width * 2: # Filtro básico de visibilidad
            return {
                'dist': z_dist,
                'u': int(u_base),
                'v_base': int(v_base),
                'v_top': int(v_top),
                'w': int(screen_w),
                'h': int(screen_h),
                'color': color_bgr,
                'shape': shape_type
            }
        return None

    def render(self, observer, state):
        """
        Calcula una imagen RGB representando lo que el agente ve físicamente.
        Soporta Polimorfismo Geométrico y Perspectiva 3D Real.
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # 1. Fondo: Cielo y Pasto dinámicos según el Pitch
        # Calculamos donde quedaría el horizonte (Z infinito, en el suelo)
        horizon_res = self.project_3d(observer.x + math.cos(observer.rangle)*10000, 
                                     observer.y + math.sin(observer.rangle)*10000, 
                                     0, observer)
        
        horizon_v = horizon_res[1] if horizon_res else -1
        
        # Llenar cielo y suelo
        if horizon_v < 0:
            frame[:, :] = (50, 100, 30) # Todo suelo si miramos muy hacia abajo
        elif horizon_v >= self.height:
            frame[:, :] = (30, 30, 30) # Todo cielo si miramos muy hacia arriba
        else:
            frame[:horizon_v, :] = (30, 30, 30) # Cielo
            frame[horizon_v:, :] = (50, 100, 30) # Suelo
        
        # 2. Dibujar rejilla de suelo proyectada para dar sensación de profundidad
        grid_color = (40, 80, 20)
        # Líneas Longitudinales (paralelas a la dirección del robot aproximadamente)
        for dx_grid in range(-1000, 1001, 100):
            points = []
            for dy_grid in range(0, 2001, 100):
                # Punto relativo al robot en su orientación actual
                gx = observer.x + dx_grid * math.cos(observer.rangle - math.pi/2) + dy_grid * math.cos(observer.rangle)
                gy = observer.y + dx_grid * math.sin(observer.rangle - math.pi/2) + dy_grid * math.sin(observer.rangle)
                res = self.project_3d(gx, gy, 0, observer)
                if res and 0 <= res[0] <= self.width and 0 <= res[1] <= self.height:
                    points.append((res[0], res[1]))
            if len(points) > 1:
                cv2.polylines(frame, [np.array(points)], False, grid_color, 1)

        # 3. Proyectar Objetos
        objects_to_draw = []
        
        if state.ball:
            proj = self._project_entity(observer, state.ball, (0, 100, 255), "circle", state.ball.radius)
            if proj: objects_to_draw.append(proj)
            
        for r in state.robots:
            v_mult = 0.15
            color_bgr = (int(r.team_color[2] * v_mult), 
                         int(r.team_color[1] * v_mult), 
                         int(r.team_color[0] * v_mult))
            proj = self._project_entity(observer, r, color_bgr, "rect", r.radius)
            if proj: objects_to_draw.append(proj)
            
        for g in state.goals:
            color_bgr = (int(g.team_color[2]), int(g.team_color[1]), int(g.team_color[0]))
            
            # Determinar el plano de la "boca" de la portería (heurística basada en posición)
            # El centro de la portería 2D es (g.x + g.width/2, g.y + g.height/2)
            # Pero la boca está en el borde que da al campo.
            mouth_x = g.x + g.width if g.x < 100 else g.x
            mouth_y_center = g.y + g.height / 2.0
            
            # Dimensiones de la cara frontal
            w_mouth = g.height
            h_mouth = g.z_height
            
            # Vértices: Base Izq, Base Der, Tope Der, Tope Izq
            v1 = self.project_3d(mouth_x, mouth_y_center - w_mouth/2, 0, observer)
            v2 = self.project_3d(mouth_x, mouth_y_center + w_mouth/2, 0, observer)
            v3 = self.project_3d(mouth_x, mouth_y_center + w_mouth/2, h_mouth, observer)
            v4 = self.project_3d(mouth_x, mouth_y_center - w_mouth/2, h_mouth, observer)
            
            # Solo dibujar si al menos un punto es visible (z > 0)
            visible_pts = [v for v in [v1, v2, v3, v4] if v is not None]
            if len(visible_pts) >= 2:
                # Usar la distancia media para el Painter's Algorithm
                z_avg = sum(v[2] for v in visible_pts) / len(visible_pts)
                
                # Para simplificar, si no son todos visibles, no dibujamos el polígono completo
                # pero en un simulador real haríamos clipping. Por ahora, si todos visibles:
                if len(visible_pts) == 4:
                    pts = np.array([[v1[0], v1[1]], [v2[0], v2[1]], [v3[0], v3[1]], [v4[0], v4[1]]], np.int32)
                    objects_to_draw.append({
                        'dist': z_avg,
                        'pts': pts,
                        'color': color_bgr,
                        'shape': 'poly'
                    })

        # 4. Painter's Algorithm: Ordenar por distancia (Z)
        objects_to_draw.sort(key=lambda obj: obj['dist'], reverse=True)
        
        # 5. Dibujar entidades
        for obj in objects_to_draw:
            if obj['shape'] == "poly":
                # Dibujar la cara frontal de la portería
                cv2.fillPoly(frame, [obj['pts']], obj['color'])
                # Borde sutil
                cv2.polylines(frame, [obj['pts']], True, (255, 255, 255), 2)
                continue

            u, v_base, v_top = obj['u'], obj['v_base'], obj['v_top']
            w, h = obj['w'], obj['h']
            
            if obj['shape'] == "circle":
                # Dibujar un círculo/elipse que represente la pelota
                # Usamos la altura calculada para el radio vertical
                cv2.circle(frame, (u, v_base - h // 2), h // 2, obj['color'], -1)
            else:
                # Dibujar un rectángulo vertical apoyado en el suelo
                top_left = (u - w // 2, v_top)
                bottom_right = (u + w // 2, v_base)
                cv2.rectangle(frame, top_left, bottom_right, obj['color'], -1)
                # Añadir un borde sutil
                cv2.rectangle(frame, top_left, bottom_right, (255, 255, 255), 1)

        # 6. Aplica la lente Fisheye
        #frame = cv2.remap(frame, self.map_x, self.map_y, cv2.INTER_LINEAR, 
        #                  borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
                          
        return frame
