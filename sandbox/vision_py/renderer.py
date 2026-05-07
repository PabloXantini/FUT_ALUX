import math
from .scene import Scene, RenderObject, Vertex
from .python_renderer import OpenCVRenderer
from .cpp_renderer import OpenGLRenderer
from .soccer_scene import SoccerScene

class Renderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Backends
        self.cpp_backend = OpenGLRenderer(width, height)
        self.py_backend = OpenCVRenderer(width, height)
        
        self.scene = SoccerScene()
        
    def render(self, observer, state, camera_params):
        if not self.scene.initialized:
            self.scene.load(state)
        self.scene.update(state)
        
        # Preferir C++ si está disponible
        if self.cpp_backend.is_available():
           return self.cpp_backend.render(observer, self.scene, camera_params)
        else:
            return self.py_backend.render(observer, self.scene, camera_params)

    # OPTIONS FOR RENDERING
    def set_light(self, ambient, diffuse, light_pos):
        self.cpp_backend.set_light(ambient, diffuse, light_pos)

    def set_fisheye(self, k, zoom):
        self.cpp_backend.set_fisheye(k, zoom)
        self.py_backend.set_fisheye(k, zoom)

    def set_motion_blur(self, strength, samples):
        self.cpp_backend.set_motion_blur(strength, samples)
