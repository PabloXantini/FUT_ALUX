import cv2
import weakref

# Importar rvision (C++ Backend)
try:
    from ..vision_cpp import rvision as rv
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
            self._cam = rv.CameraState()
            # Cache para objetos rv.RenderObject (usa el objeto de escena de Python como llave)
            self._obj_cache = weakref.WeakKeyDictionary()

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
        self._cam.x, self._cam.y, self._cam.z = observer.x, observer.y, camera_params['height']
        self._cam.yaw = observer.rangle + camera_params.get('yaw_off', 0.0)
        self._cam.pitch = camera_params['pitch']
        self._cam.roll = camera_params.get('roll', 0.0)
        self._cam.focal_length = camera_params['focal_length']
        self._cam.cx, self._cam.cy = self.width // 2, self.height // 2
        self._cam.width, self._cam.height = self.width, self.height
        self._cam.near_plane, self._cam.far_plane = 1.0, 2000.0
        self._cam.use_fisheye = camera_params.get('enable_fisheye', True)
        self._cam.use_motion_blur = camera_params.get('enable_motion_blur', True)
        
        # 2. Convertir Scene a RenderObjects de rvision
        rv_objects = []
        for pobj in scene.objects:
            if pobj in self._obj_cache:
                robj = self._obj_cache[pobj]
                # Actualizar atributos dinámicos
                # Color
                if len(pobj.color) == 4:
                    robj.color.r, robj.color.g, robj.color.b, robj.color.a = pobj.color
                else:
                    robj.color.r, robj.color.g, robj.color.b = pobj.color
                    robj.color.a = 1.0
                # Posición
                robj.position.x, robj.position.y, robj.position.z = pobj.position
                # Tamaño
                robj.size.x, robj.size.y, robj.size.z = pobj.size
            else:
                robj = rv.RenderObject()
                # Color inicial
                if len(pobj.color) == 4:
                    robj.color = rv.Vec4(*pobj.color)
                else:
                    robj.color = rv.Vec4(*pobj.color, 1.0)
                    
                robj.position = rv.Vec3(*pobj.position)
                robj.size = rv.Vec3(*pobj.size)
                
                if pobj.type == pobj.TYPE_MESH:
                    robj.type = rv.RenderType.MESH
                    verts = [rv.Vertex(v.x, v.y, v.z, v.nx, v.ny, v.nz) for v in pobj.vertices]
                    robj.vertices = verts
                elif pobj.type == pobj.TYPE_CIRCLE:
                    robj.type = rv.RenderType.CIRCLE
                elif pobj.type == pobj.TYPE_CYLINDER:
                    robj.type = rv.RenderType.CYLINDER
                
                self._obj_cache[pobj] = robj
                
            rv_objects.append(robj)
            
        # 3. Renderizar y recuperar frame
        self.renderer.render(self._cam, rv_objects)
        frame = self.renderer.get_frame().reshape((self.height, self.width, 4))
        # Convertir RGBA a BGR y flipear (OpenGL es Y-up)
        return cv2.flip(cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR), -1)
