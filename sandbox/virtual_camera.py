import numpy as np
import cv2
import math
import os
import sys

# Importar componentes modulares
from .vision_py.python_renderer import OpenCVRenderer
from .vision_py.cpp_wrapper import OpenGLRenderer

# Asegurar acceso a tipos de rvision
sys.path.append(os.path.join(os.path.dirname(__file__), "vision_cpp"))
try:
    import rvision as rv
except ImportError:
    rv = None

class VirtualCamera:
    """ Fachada para el sistema de visión """
    def __init__(self, width=320, height=240, fov_degrees=45, pitch=30.0, camera_height=15.0):
        self.width = width
        self.height = height
        self.fov_degrees = fov_degrees
        
        fov_rad = math.radians(fov_degrees)
        self.focal_length = width / (2 * math.tan(fov_rad / 2))
            
        self.cx = width // 2
        self.cy = height // 2
        self.camera_height = camera_height

        self.pitch = math.radians(pitch)   
        self.yaw = 0.0
        self.roll = 0.0
        
        self._near = 1.0
        self._far = 2000.0
        
        self.cpp_backend = OpenGLRenderer(width, height)
        self.py_backend = OpenCVRenderer(width, height, self.focal_length)
        
        # Fisheye: el C++ backend lo aplica via GPU shader siempre.
        # El Python backend lo aplica via cv2.remap cuando este flag es True.
        self.ENABLE_FISHEYE = True
        self._init_fisheye_maps() # Inicializar siempre para tener los mapas listos

    def _init_fisheye_maps(self):
        K = np.array([[self.focal_length, 0, self.cx], [0, self.focal_length, self.cy], [0, 0, 1]], dtype=np.float32)
        D = np.array([0.08, 0, 0, 0], dtype=np.float32) # k1 > 0 -> barrel distortion in this mapping
        self.map_x, self.map_y = cv2.fisheye.initUndistortRectifyMap(K, D, np.eye(3), K, (self.width, self.height), cv2.CV_32FC1)

    def set_light_level(self, ambient=0.4, diffuse=0.8, x=320, y=240, z=500):
        if rv and self.cpp_backend.is_available():
            light = rv.LightState()
            light.ambient = ambient
            light.diffuse = diffuse
            light.position = rv.Vec3(x, y, z)
            self.cpp_backend.set_light(light)

    def set_fisheye_params(self, k=-0.4, zoom=1.0):
        # Ajusta los parámetros del lente de ojo de pescado en tiempo real.
        # - k < 0  → Distorsión de barril (convexo, típico de fish-eye)
        # - k > 0  → Distorsión de cojín (pincushion)
        # - zoom   → Factor de zoom del resultado final
        self.cpp_backend.set_fisheye(k, zoom)

    def set_motion_blur(self, strength=0.5, samples=3):
        # Ajusta el efecto de desenfoque de movimiento.
        # - strength: 0.0 (apagado) a 1.0 (máximo rastro)
        # - samples: cantidad de frames de historial (1 a 7)
        self.cpp_backend.set_motion_blur(strength, samples)

    def render(self, observer, state):
        if rv and self.cpp_backend.is_available():
            cam = rv.CameraState()
            cam.x, cam.y, cam.z = observer.x, observer.y, self.camera_height
            cam.roll = self.roll
            cam.yaw = observer.rangle + self.yaw
            cam.pitch = self.pitch
            cam.focal_length = self.focal_length
            cam.cx, cam.cy = self.cx, self.cy
            cam.width, cam.height = self.width, self.height
            cam.near_plane, cam.far_plane = self._near, self._far
            
            objects = self._prepare_mesh_objects(state)
            frame = self.cpp_backend.render(cam, objects)
        else:
            maps = (self.map_x, self.map_y) if self.ENABLE_FISHEYE else None
            frame = self.py_backend.render(observer, state, {}, fisheye_maps=maps)
            if self.ENABLE_FISHEYE:
                frame = cv2.remap(frame, self.map_x, self.map_y, cv2.INTER_LINEAR)
        return frame

    def _add_quad(self, vertices, p1, p2, p3, p4, normal):
        v1 = rv.Vertex(p1[0], p1[1], p1[2], normal[0], normal[1], normal[2])
        v2 = rv.Vertex(p2[0], p2[1], p2[2], normal[0], normal[1], normal[2])
        v3 = rv.Vertex(p3[0], p3[1], p3[2], normal[0], normal[1], normal[2])
        v4 = rv.Vertex(p4[0], p4[1], p4[2], normal[0], normal[1], normal[2])
        vertices.extend([v1, v2, v3, v1, v3, v4])

    def _prepare_mesh_objects(self, state):
        objects = []
        if not rv: return objects
        
        # 1. Campo (Pasto)
        if state.pitch:
            w, h = state.pitch.width, state.pitch.height
            obj = rv.RenderObject()
            obj.type = rv.RenderType.MESH
            obj.color = rv.Vec4(0.05, 0.25, 0.05, 1.0)
            verts = []
            self._add_quad(verts, [0,0,0], [w,0,0], [w,h,0], [0,h,0], [0,0,1])
            obj.vertices = verts
            objects.append(obj)
            
            # 2. Líneas del Campo
            line_color = rv.Vec4(1.0, 1.0, 1.0, 1.0)
            p = state.pitch.padding
            t = 6.0 # espesor líneas según Pitch.main_thick
            z_off = 0.1
            
            line_obj = rv.RenderObject()
            line_obj.type = rv.RenderType.MESH
            line_obj.color = line_color
            line_verts = []
            
            # Bordes Exteriores (Rectángulo seguro)
            sz = state.pitch.safe_zone
            self._add_quad(line_verts, [sz.left, sz.top, z_off], [sz.right, sz.top, z_off], [sz.right, sz.top+t, z_off], [sz.left, sz.top+t, z_off], [0,0,1])
            self._add_quad(line_verts, [sz.left, sz.bottom-t, z_off], [sz.right, sz.bottom-t, z_off], [sz.right, sz.bottom, z_off], [sz.left, sz.bottom, z_off], [0,0,1])
            self._add_quad(line_verts, [sz.left, sz.top, z_off], [sz.left+t, sz.top, z_off], [sz.left+t, sz.bottom, z_off], [sz.left, sz.bottom, z_off], [0,0,1])
            self._add_quad(line_verts, [sz.right-t, sz.top, z_off], [sz.right, sz.top, z_off], [sz.right, sz.bottom, z_off], [sz.right-t, sz.bottom, z_off], [0,0,1])
            
            # Línea Central
            mid_x = w / 2
            self._add_quad(line_verts, [mid_x-t/2, p, z_off], [mid_x+t/2, p, z_off], [mid_x+t/2, h-p, z_off], [mid_x-t/2, h-p, z_off], [0,0,1])
            
            # Círculo Central
            r_circle = 100.0 # según Pitch.draw
            segments = 32
            for i in range(segments):
                a1 = (i / segments) * 2 * math.pi
                a2 = ((i + 1) / segments) * 2 * math.pi
                v2 = [mid_x + r_circle * math.cos(a1), h/2 + r_circle * math.sin(a1), z_off]
                v3 = [mid_x + r_circle * math.cos(a2), h/2 + r_circle * math.sin(a2), z_off]
                v2_inner = [mid_x + (r_circle-t) * math.cos(a1), h/2 + (r_circle-t) * math.sin(a1), z_off]
                v3_inner = [mid_x + (r_circle-t) * math.cos(a2), h/2 + (r_circle-t) * math.sin(a2), z_off]
                self._add_quad(line_verts, v2_inner, v2, v3, v3_inner, [0,0,1])
            
            # Áreas de Penalti
            for pz in [state.pitch.ally_penalty_zone, state.pitch.enemy_penalty_zone]:
                # Top
                self._add_quad(line_verts, [pz.left, pz.top, z_off], [pz.right, pz.top, z_off], [pz.right, pz.top+t, z_off], [pz.left, pz.top+t, z_off], [0,0,1])
                # Bottom
                self._add_quad(line_verts, [pz.left, pz.bottom-t, z_off], [pz.right, pz.bottom-t, z_off], [pz.right, pz.bottom, z_off], [pz.left, pz.bottom, z_off], [0,0,1])
                # Side
                if pz.left < w/2: # Izquierda
                    self._add_quad(line_verts, [pz.right-t, pz.top, z_off], [pz.right, pz.top, z_off], [pz.right, pz.bottom, z_off], [pz.right-t, pz.bottom, z_off], [0,0,1])
                else: # Derecha
                    self._add_quad(line_verts, [pz.left, pz.top, z_off], [pz.left+t, pz.top, z_off], [pz.left+t, pz.bottom, z_off], [pz.left, pz.bottom, z_off], [0,0,1])

            line_obj.vertices = line_verts
            objects.append(line_obj)

        # 3. Porterías
        goal_exterior_verts = []
        for g in state.goals:
            c = rv.Vec4(g.team_color[0]/255, g.team_color[1]/255, g.team_color[2]/255, 1)
            gw, gh, gzh = g.width, g.height, g.z_height
            is_left = g.x < 100
            goal_obj = rv.RenderObject()
            goal_obj.type = rv.RenderType.MESH
            goal_obj.color = c
            gv = []
            x0, x1 = g.x, g.x + gw
            y0, y1 = g.y, g.y + gh
            z0, z1 = 0, gzh
            eps = 0.5 # Offset para paredes exteriores
            
            # --- INTERIOR (Color de equipo) ---
            # Techo (Normal hacia abajo)
            self._add_quad(gv, [x0,y0,z1], [x1,y0,z1], [x1,y1,z1], [x0,y1,z1], [0,0,-1])
            # Fondo (Normal hacia el campo)
            if is_left: self._add_quad(gv, [x0,y0,z0], [x0,y1,z0], [x0,y1,z1], [x0,y0,z1], [1,0,0])
            else: self._add_quad(gv, [x1,y0,z0], [x1,y1,z0], [x1,y1,z1], [x1,y0,z1], [-1,0,0])
            # Lados (Normal hacia el centro de la portería)
            self._add_quad(gv, [x0,y0,z0], [x1,y0,z0], [x1,y0,z1], [x0,y0,z1], [0,1,0])
            self._add_quad(gv, [x0,y1,z0], [x1,y1,z0], [x1,y1,z1], [x0,y1,z1], [0,-1,0])
            
            goal_obj.vertices = gv
            objects.append(goal_obj)
            
            # --- EXTERIOR (Negro) ---
            # Techo (Normal hacia arriba)
            self._add_quad(goal_exterior_verts, [x0,y0,z1+eps], [x1,y0,z1+eps], [x1,y1,z1+eps], [x0,y1,z1+eps], [0,0,1])
            # Fondo (Normal hacia afuera del campo)
            if is_left: self._add_quad(goal_exterior_verts, [x0-eps,y0,z0], [x0-eps,y1,z0], [x0-eps,y1,z1], [x0-eps,y0,z1], [-1,0,0])
            else: self._add_quad(goal_exterior_verts, [x1+eps,y0,z0], [x1+eps,y1,z0], [x1+eps,y1,z1], [x1+eps,y0,z1], [1,0,0])
            # Lados (Normal hacia afuera de la portería)
            self._add_quad(goal_exterior_verts, [x0,y0-eps,z0], [x1,y0-eps,z0], [x1,y0-eps,z1], [x0,y0-eps,z1], [0,-1,0])
            self._add_quad(goal_exterior_verts, [x0,y1+eps,z0], [x1,y1+eps,z0], [x1,y1+eps,z1], [x0,y1+eps,z1], [0,1,0])

        # 4. Pelota (Billboard CIRCLE)
        if state.ball:
            b = rv.RenderObject()
            b.type = rv.RenderType.CIRCLE
            b.color = rv.Vec4(1.0, 0.4, 0.0, 1.0)
            # Centro en Z = radio para que toque el suelo
            b.position = rv.Vec3(state.ball.x, state.ball.y, state.ball.radius)
            b.size = rv.Vec3(state.ball.radius*2, state.ball.radius*2, state.ball.radius*2)
            objects.append(b)

        # 5. Robots (RECT / Cubos)
        dark_factor = 0.1
        for r in state.robots:
            if r.ban_timer > 0: continue
            ro = rv.RenderObject()
            ro.type = rv.RenderType.CYLINDER
            ro.color = rv.Vec4(r.color[0]/255*dark_factor, r.color[1]/255*dark_factor, r.color[2]/255*dark_factor, 1)
            # Altura 60, centro en Z=30
            ro.position = rv.Vec3(r.x, r.y, 30)
            ro.size = rv.Vec3(r.radius*2, r.radius*2, 60)
            objects.append(ro)
            
        # 6. Paredes
        if state.pitch:
            w, h = state.pitch.width, state.pitch.height
            wall_h = 60.0
            eps = 1.0 # Margen para evitar Z-fighting
            wall_obj = rv.RenderObject()
            wall_obj.type = rv.RenderType.MESH
            wall_obj.color = rv.Vec4(0.0, 0.0, 0.0, 1.0)
            wall_verts = []
            # Pared Izquierda (x=-eps)
            self._add_quad(wall_verts, [-eps,-eps,0], [-eps,h+eps,0], [-eps,h+eps,wall_h], [-eps,-eps,wall_h], [1,0,0])
            # Pared Derecha (x=w+eps)
            self._add_quad(wall_verts, [w+eps,-eps,0], [w+eps,h+eps,0], [w+eps,h+eps,wall_h], [w+eps,-eps,wall_h], [-1,0,0])
            # Pared Superior (y=-eps)
            self._add_quad(wall_verts, [-eps,-eps,0], [w+eps,-eps,0], [w+eps,-eps,wall_h], [-eps,-eps,wall_h], [0,1,0])
            # Pared Inferior (y=h+eps)
            self._add_quad(wall_verts, [-eps,h+eps,0], [w+eps,h+eps,0], [w+eps,h+eps,wall_h], [-eps,h+eps,wall_h], [0,-1,0])
            
            # Añadir exteriores de portería
            wall_verts.extend(goal_exterior_verts)
            
            wall_obj.vertices = wall_verts
            objects.append(wall_obj)

        return objects
