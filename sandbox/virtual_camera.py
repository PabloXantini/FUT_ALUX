import numpy as np
import cv2
import math

try:
    from sandbox.cpp_vision import fast_math
    HAS_FAST_MATH = True
except ImportError:
    HAS_FAST_MATH = False

class VirtualCamera:
    """
    Motor gráfico encargado de generar frames de visión sintéticos en 2D.
    Soporta perspectiva, distancia, oclusión (Painter's Algorithm) y distorsión
    de lente estilo Ojo de Pescado (Barrel Distortion).
    """
    ENABLE_FISHEYE = True
    def __init__(self, width=320, height=240, fov_degrees=100, 
                 pitch=0.0, yaw=0.0, roll=0.0, camera_height=20.0):
        self.width = width
        self.height = height
        self.fov = math.radians(fov_degrees)
        
        # Frustum
        self._near = 0.05
        self._far = 1000.0
        
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
        
    def project_3d_vectorized(self, points, observer):
        """
        Versión vectorizada de project_3d para procesar múltiples puntos (N, 3).
        Retorna (N, 3) con (u, v, z_cam).
        """
        if HAS_FAST_MATH:
            pts = np.atleast_2d(points).astype(np.float64)
            return fast_math.project_3d_vectorized(
                pts, float(observer.x), float(observer.y), float(observer.rangle),
                float(self.camera_height), float(self.yaw_off), float(self.pitch),
                float(self._near), float(self._far), float(self.focal_length), float(self.cx), float(self.cy)
            )

        pts = np.atleast_2d(points)
        dx = pts[:, 0] - observer.x
        dy = pts[:, 1] - observer.y
        dz = pts[:, 2] - self.camera_height
        
        total_yaw = observer.rangle + self.yaw_off
        cos_y = math.cos(total_yaw)
        sin_y = math.sin(total_yaw)
        
        # Proyectar sobre ejes locales del robot
        y_rel = dx * cos_y + dy * sin_y
        x_rel = -dx * sin_y + dy * cos_y
        z_rel = dz
        
        # Rotación por Pitch
        cos_p = math.cos(self.pitch)
        sin_p = math.sin(self.pitch)
        
        y_p = y_rel * cos_p - z_rel * sin_p
        z_p = y_rel * sin_p + z_rel * cos_p
        
        # Espacio OpenCV
        x_cam = x_rel
        y_cam = -z_p
        z_cam = y_p
        
        # Proyección (manejar z_cam usando frustum near y far)
        mask = (z_cam > self._near) & (z_cam < self._far)
        u = np.zeros_like(z_cam)
        v = np.zeros_like(z_cam)
        
        u[mask] = (self.focal_length * x_cam[mask] / z_cam[mask]) + self.cx
        v[mask] = (self.focal_length * y_cam[mask] / z_cam[mask]) + self.cy
        
        # Retornar (N, 3) con u, v, z_cam. Los inválidos tienen u=v=0, z=0.
        res = np.stack([u, v, z_cam], axis=1)
        res[~mask] = 0
        return res

    def project_3d(self, x_world, y_world, z_world, observer):
        """Transforma coordenadas de mundo a coordenadas de imagen (u, v) y profundidad Z."""
        if HAS_FAST_MATH:
            u, v, z = fast_math.project_3d_scalar(
                float(x_world), float(y_world), float(z_world),
                float(observer.x), float(observer.y), float(observer.rangle),
                float(self.camera_height), float(self.yaw_off), float(self.pitch),
                float(self._near), float(self._far), float(self.focal_length), float(self.cx), float(self.cy)
            )
            if z == 0.0:
                return None
            return int(u), int(v), z

        res = self.project_3d_vectorized([[x_world, y_world, z_world]], observer)
        if res[0, 2] == 0:
            return None
        return int(res[0, 0]), int(res[0, 1]), res[0, 2]

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

    def _project_quad(self, observer, v_world, color_in, color_out=None):
        """ Proyecta un quad 3D (4 vértices) y determina color según su normal """
        v_world = np.array(v_world)
        center = np.mean(v_world, axis=0)
        vec_to_cam = np.array([observer.x, observer.y, self.camera_height]) - center
        
        v10 = v_world[1] - v_world[0]
        v20 = v_world[2] - v_world[0]
        normal = np.cross(v10, v20)
        norm_len = np.linalg.norm(normal)
        if norm_len > 0:
            normal = normal / norm_len
            
        dot = np.dot(normal, vec_to_cam)
        color = color_in if dot >= 0 else (color_out if color_out else color_in)
        
        res_v = self.project_3d_vectorized(v_world, observer)
        mask_visible = res_v[:, 2] > 0
        
        if np.sum(mask_visible) >= 3:
            valid_pts = res_v[mask_visible, :2].astype(np.int32)
            z_avg = np.mean(res_v[mask_visible, 2])
            return {
                'dist': z_avg,
                'pts': valid_pts,
                'color': color,
                'shape': 'poly'
            }
        return None

    def render(self, observer, state):
        """
        Calcula una imagen RGB representando lo que el agente ve físicamente.
        Soporta Polimorfismo Geométrico y Perspectiva 3D Real.
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # 1. Fondo: Cielo y Pasto dinámicos según el Pitch
        horizon_dist = self._far * 0.95
        horizon_res = self.project_3d(observer.x + math.cos(observer.rangle) * horizon_dist, 
                                     observer.y + math.sin(observer.rangle) * horizon_dist, 
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
        
        # 2. Dibujar líneas del campo (Pitch)
        if hasattr(state, 'pitch') and state.pitch is not None:
            if not hasattr(self, '_cached_lines_data'):
                pad = state.pitch.padding
                w = state.pitch.width
                h = state.pitch.height
                pw = state.pitch.penalty_w
                ph = state.pitch.penalty_h
                py = h / 2 - ph / 2
                
                lines_data = []
                
                safe_color = getattr(state.pitch, 'safe_color', (200, 200, 200))
                safe_thick = getattr(state.pitch, 'safe_thick', 1) 
                main_color = getattr(state.pitch, 'main_color', (255, 255, 255))
                main_thick = getattr(state.pitch, 'main_thick', 2)

                # Safe zone
                lines_data.append({'pts': np.linspace([pad, pad, 0], [w-pad, pad, 0], 25, dtype=np.float64), 'color': safe_color, 't': safe_thick})
                lines_data.append({'pts': np.linspace([w-pad, pad, 0], [w-pad, h-pad, 0], 25, dtype=np.float64), 'color': safe_color, 't': safe_thick})
                lines_data.append({'pts': np.linspace([w-pad, h-pad, 0], [pad, h-pad, 0], 25, dtype=np.float64), 'color': safe_color, 't': safe_thick})
                lines_data.append({'pts': np.linspace([pad, h-pad, 0], [pad, pad, 0], 25, dtype=np.float64), 'color': safe_color, 't': safe_thick})
                # Middle line
                lines_data.append({'pts': np.linspace([w / 2, pad, 0], [w / 2, h - pad, 0], 25, dtype=np.float64), 'color': main_color, 't': main_thick})  
                # Circle
                angles = np.linspace(0, 2*np.pi, 45)
                circle_pts = np.zeros((45, 3), dtype=np.float64)
                circle_pts[:, 0] = w / 2 + np.cos(angles) * 100
                circle_pts[:, 1] = h / 2 + np.sin(angles) * 100
                circle_pts[:, 2] = 0
                lines_data.append({'pts': circle_pts, 'color': main_color, 't': main_thick})
                
                # Ally penalty
                lines_data.append({'pts': np.linspace([pad, py, 0], [pad+pw, py, 0], 10, dtype=np.float64), 'color': main_color, 't': main_thick})
                lines_data.append({'pts': np.linspace([pad+pw, py, 0], [pad+pw, py+ph, 0], 15, dtype=np.float64), 'color': main_color, 't': main_thick})
                lines_data.append({'pts': np.linspace([pad+pw, py+ph, 0], [pad, py+ph, 0], 10, dtype=np.float64), 'color': main_color, 't': main_thick})
                
                # Enemy penalty
                lines_data.append({'pts': np.linspace([w-pad, py, 0], [w-pad-pw, py, 0], 10, dtype=np.float64), 'color': main_color, 't': main_thick})
                lines_data.append({'pts': np.linspace([w-pad-pw, py, 0], [w-pad-pw, py+ph, 0], 15, dtype=np.float64), 'color': main_color, 't': main_thick})
                lines_data.append({'pts': np.linspace([w-pad-pw, py+ph, 0], [w-pad, py+ph, 0], 10, dtype=np.float64), 'color': main_color, 't': main_thick})
                
                self._cached_lines_data = lines_data

            # Proyectar y dibujar cada línea segmento por segmento para perspectiva de grosor
            for line_dict in self._cached_lines_data:
                line_pts = line_dict['pts']
                c = line_dict['color']
                base_t = line_dict['t']

                res = self.project_3d_vectorized(line_pts, observer)
                mask = (res[:, 2] > 0)
                
                for i in range(len(line_pts) - 1):
                    if mask[i] and mask[i+1]:
                        p1 = res[i, :2].astype(np.int32)
                        p2 = res[i+1, :2].astype(np.int32)
                        z_avg = (res[i, 2] + res[i+1, 2]) / 2.0
                        
                        # Calcular grosor en pantalla en función de la distancia
                        t = int(max(1, base_t * self.focal_length / z_avg))
                        cv2.line(frame, tuple(p1), tuple(p2), c, t)

        # 3. Proyectar Objetos
        objects_to_draw = []
        
        if state.ball:
            proj = self._project_entity(observer, state.ball, (0, 100, 255), "circle", state.ball.radius)
            if proj: objects_to_draw.append(proj)
            
        for r in state.robots:
            if r.ban_timer > 0:
                continue
            
            v_mult = 0.10
            color_bgr = (int(r.color[2] * v_mult), 
                         int(r.color[1] * v_mult), 
                         int(r.color[0] * v_mult))
            proj = self._project_entity(observer, r, color_bgr, "rect", r.radius)
            if proj: objects_to_draw.append(proj)
            
        # Paredes del Campo (Pitch Walls)
        if hasattr(state, 'pitch') and state.pitch is not None:
            pw_z = 40.0
            w = state.pitch.width
            h = state.pitch.height
            wall_color = (10, 10, 10) # Negro/Gris oscuro
            # Top Wall
            proj = self._project_quad(observer, [[0, 0, 0], [w, 0, 0], [w, 0, pw_z], [0, 0, pw_z]], wall_color)
            if proj: objects_to_draw.append(proj)
            # Bottom Wall
            proj = self._project_quad(observer, [[w, h, 0], [0, h, 0], [0, h, pw_z], [w, h, pw_z]], wall_color)
            if proj: objects_to_draw.append(proj)
            # Left Wall
            proj = self._project_quad(observer, [[0, h, 0], [0, 0, 0], [0, 0, pw_z], [0, h, pw_z]], wall_color)
            if proj: objects_to_draw.append(proj)
            # Right Wall
            proj = self._project_quad(observer, [[w, 0, 0], [w, h, 0], [w, h, pw_z], [w, 0, pw_z]], wall_color)
            if proj: objects_to_draw.append(proj)

        for g in state.goals:
            color_in = (int(g.team_color[2]), int(g.team_color[1]), int(g.team_color[0]))
            color_out = (10, 10, 10) # Negro para el exterior
            
            front_x = g.x + g.width if g.x < 80 else g.x
            back_x = g.x if g.x < 80 else g.x + g.width
            min_y = g.y
            max_y = g.y + g.height
            z0 = 0
            z1 = g.z_height
            
            v0 = [back_x, min_y, z0]
            v1 = [front_x, min_y, z0]
            v2 = [front_x, max_y, z0]
            v3 = [back_x, max_y, z0]
            v4 = [back_x, min_y, z1]
            v5 = [front_x, min_y, z1]
            v6 = [front_x, max_y, z1]
            v7 = [back_x, max_y, z1]

            if g.x < 80: # Left Goal
                face_top = [v7, v6, v5, v4]
                face_back = [v0, v3, v7, v4]
                face_side1 = [v1, v0, v4, v5]
                face_side2 = [v3, v2, v6, v7]
            else: # Right Goal
                face_top = [v4, v5, v6, v7]
                face_back = [v3, v0, v4, v7]
                face_side1 = [v0, v1, v5, v4]
                face_side2 = [v2, v3, v7, v6]

            proj = self._project_quad(observer, face_top, color_in, color_out)
            if proj: objects_to_draw.append(proj)
            
            proj = self._project_quad(observer, face_back, color_in, color_out)
            if proj: objects_to_draw.append(proj)
            
            proj = self._project_quad(observer, face_side1, color_in, color_out)
            if proj: objects_to_draw.append(proj)
            
            proj = self._project_quad(observer, face_side2, color_in, color_out)
            if proj: objects_to_draw.append(proj)

        # 4. Painter's Algorithm: Ordenar por distancia (Z)
        objects_to_draw.sort(key=lambda obj: obj['dist'], reverse=True)
        
        # 5. Dibujar entidades
        for obj in objects_to_draw:
            if obj['shape'] == "poly":
                # Dibujar la cara frontal de la portería
                cv2.fillPoly(frame, [obj['pts']], obj['color'])
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
                # cv2.rectangle(frame, top_left, bottom_right, (255, 255, 255), 1)

        # 6. Aplica la lente Fisheye (Solo si está habilitado)
        if self.ENABLE_FISHEYE:
            frame = cv2.remap(frame, self.map_x, self.map_y, cv2.INTER_LINEAR, 
                              borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
                          
        return frame
