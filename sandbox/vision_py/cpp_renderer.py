import cv2
import sys
import os
import numpy as np

# Importar rvision desde el directorio vision_cpp
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "vision_cpp"))
try:
    import rvision as rv
except ImportError:
    rv = None

class OpenGLRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.renderer = None
        if rv:
            self.renderer = rv.Renderer(width, height)
            if not self.renderer.initialize():
                self.renderer = None

    def is_available(self):
        return self.renderer is not None

    def set_light(self, ambient, diffuse, light_pos):
        if self.renderer:
            ls = rv.LightState()
            ls.ambient = ambient
            ls.diffuse = diffuse
            ls.position = rv.Vec3(*light_pos)
            self.renderer.set_light(ls)

    def set_fisheye(self, k, zoom):
        if self.renderer:
            self.renderer.set_fisheye(k, zoom)

    def set_motion_blur(self, strength, samples):
        if self.renderer:
            self.renderer.set_motion_blur(strength, samples)

    def render(self, observer, scene, camera_params):
        if not self.renderer: return None
        
        # 1. Preparar CameraState
        cam = rv.CameraState()
        cam.x, cam.y, cam.z = observer.x, observer.y, camera_params['height']
        cam.yaw = observer.rangle + camera_params.get('yaw_off', 0.0)
        cam.pitch = camera_params['pitch']
        cam.roll = camera_params.get('roll', 0.0)
        cam.focal_length = camera_params['focal_length']
        cam.cx, cam.cy = self.width // 2, self.height // 2
        cam.width, cam.height = self.width, self.height
        cam.near_plane, cam.far_plane = 1.0, 2000.0
        cam.use_fisheye = camera_params.get('enable_fisheye', True)
        cam.use_motion_blur = camera_params.get('enable_motion_blur', True)
        
        # 2. Convertir Scene a RenderObjects de rvision
        rv_objects = []
        for pobj in (scene.static_objects + scene.dynamic_objects):
            robj = rv.RenderObject()
            robj.color = rv.Vec4(*pobj.color)
            robj.position = rv.Vec3(*pobj.position)
            robj.size = rv.Vec3(*pobj.size)
            
            if pobj.type == pobj.TYPE_MESH:
                robj.type = rv.RenderType.MESH
                verts = []
                for v in pobj.vertices:
                    verts.append(rv.Vertex(v.x, v.y, v.z, v.nx, v.ny, v.nz))
                robj.vertices = verts
            elif pobj.type == pobj.TYPE_CIRCLE:
                robj.type = rv.RenderType.CIRCLE
            elif pobj.type == pobj.TYPE_CYLINDER:
                robj.type = rv.RenderType.CYLINDER
            
            rv_objects.append(robj)
            
        # 3. Renderizar y recuperar frame
        self.renderer.render(cam, rv_objects)
        frame = self.renderer.get_frame().reshape((self.height, self.width, 4))
        # Convertir RGBA a BGR y flipear (OpenGL es Y-up)
        return cv2.flip(cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR), -1)
