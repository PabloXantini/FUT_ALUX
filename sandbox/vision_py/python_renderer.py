import numpy as np
import cv2
import math

class OpenCVRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cx = width // 2
        self.cy = height // 2
        
        self.map_x = None
        self.map_y = None
        self.set_fisheye(k=-0.4, zoom=1.0)

    def set_fisheye(self, k=-0.4, zoom=1.0):
        y, x = np.indices((self.height, self.width), dtype=np.float32)
        u = (x / (self.width - 1)) - 0.5
        v = (y / (self.height - 1)) - 0.5
        r2 = u*u + v*v
        factor = (1.0 - k * r2) / zoom
        self.map_x = (u * factor + 0.5) * (self.width - 1)
        self.map_y = (v * factor + 0.5) * (self.height - 1)

    def project(self, points, cam_params):
        pts = points.copy() - cam_params['pos']
        angle = math.pi/2 - cam_params['yaw']
        c, s = math.cos(angle), math.sin(angle)
        x, y = pts[:, 0].copy(), pts[:, 1].copy()
        pts[:, 0] = x * c - y * s
        pts[:, 1] = x * s + y * c
        
        # Pitch (rotación sobre X local)
        th = cam_params['pitch']
        c, s = math.cos(th), math.sin(th)
        y, z = pts[:, 1].copy(), pts[:, 2].copy()
        pts[:, 1] = y * c - z * s
        pts[:, 2] = y * s + z * c
        
        mask = pts[:, 1] > 0.1
        proj = np.zeros((len(points), 2), dtype=np.float32)
        if np.any(mask):
            proj[mask, 0] = (cam_params['focal_length'] * pts[mask, 0] / pts[mask, 1] + self.cx)
            proj[mask, 1] = (cam_params['focal_length'] * (-pts[mask, 2]) / pts[mask, 1] + self.cy)
        return proj, mask

    def render(self, observer, scene, camera_params):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Calcular línea del horizonte basada en el pitch
        horizon_y = int(self.cy - camera_params['focal_length'] * math.tan(camera_params['pitch']))
        horizon_y = max(0, min(self.height, horizon_y))
        
        frame[horizon_y:, :] = (20, 60, 20) # Pasto
        frame[:horizon_y, :] = (40, 40, 40) # Cielo
        
        cam_info = {
            'focal_length': camera_params['focal_length'],
            'pos': np.array([observer.x, observer.y, camera_params['height']], dtype=np.float32),
            'yaw': observer.rangle + camera_params.get('yaw_off', 0.0),
            'pitch': camera_params['pitch']
        }
        
        faces = []
        # --- Objetos de la Escena (Combinados) ---
        for obj in scene.objects:
            # Normalizar color a BGR
            c = obj.color
            color_bgr = (int(c[2]*255), int(c[1]*255), int(c[0]*255))
            
            if obj.type == obj.TYPE_MESH:
                for i in range(0, len(obj.vertices), 3):
                    v = [obj.vertices[i], obj.vertices[i+1], obj.vertices[i+2]]
                    pts = np.array([[vi.x, vi.y, vi.z] for vi in v], dtype=np.float32)
                    proj, mask = self.project(pts, cam_info)
                    if np.all(mask):
                        depth = np.mean(np.linalg.norm(pts - cam_info['pos'], axis=1))
                        faces.append({'type': 'poly', 'pts': proj.astype(np.int32), 'color': color_bgr, 'depth': depth})
            
            elif obj.type == obj.TYPE_CIRCLE:
                pos = np.array(obj.position, dtype=np.float32)
                dist = np.linalg.norm(pos - cam_info['pos'])
                proj, mask = self.project(np.array([pos]), cam_info)
                if mask[0]:
                    r_px = int(cam_info['focal_length'] * (obj.size[0]/2) / max(0.1, dist))
                    faces.append({'type': 'circle', 'pos': tuple(proj[0].astype(np.int32)), 'radius': r_px, 'color': color_bgr, 'depth': dist})
            
            elif obj.type == obj.TYPE_CYLINDER:
                pos, radius, height = np.array(obj.position), obj.size[0]/2, obj.size[2]
                segments = 8
                pts_b = [[pos[0] + radius*math.cos(a), pos[1] + radius*math.sin(a), pos[2]-height/2] for a in np.linspace(0, 2*math.pi, segments, endpoint=False)]
                pts_t = [[pos[0] + radius*math.cos(a), pos[1] + radius*math.sin(a), pos[2]+height/2] for a in np.linspace(0, 2*math.pi, segments, endpoint=False)]
                proj_b, mask_b = self.project(np.array(pts_b, dtype=np.float32), cam_info)
                proj_t, mask_t = self.project(np.array(pts_t, dtype=np.float32), cam_info)
                
                if np.all(mask_b) and np.all(mask_t):
                    dist = np.linalg.norm(pos - cam_info['pos'])
                    faces.append({'type': 'poly', 'pts': proj_t.astype(np.int32), 'color': color_bgr, 'depth': dist - radius})
                    for i in range(segments):
                        ni = (i + 1) % segments
                        side = np.array([proj_b[i], proj_b[ni], proj_t[ni], proj_t[i]], dtype=np.int32)
                        shade = 0.7 + 0.3 * math.cos(i / segments * 2 * math.pi)
                        faces.append({'type': 'poly', 'pts': side, 'color': [int(c*shade) for c in color_bgr], 'depth': dist})

        # Ordenar y Dibujar (Painter's Algorithm)
        faces.sort(key=lambda x: x['depth'], reverse=True)
        for f in faces:
            if f['type'] == 'poly': cv2.fillPoly(frame, [f['pts']], f['color'])
            elif f['type'] == 'circle':
                cv2.circle(frame, f['pos'], f['radius'], f['color'], -1)
                cv2.circle(frame, f['pos'], f['radius'], (255, 255, 255), 1)

        if camera_params.get('enable_fisheye', False):
            frame = cv2.remap(frame, self.map_x, self.map_y, cv2.INTER_LINEAR)

        return cv2.flip(frame, 1)
