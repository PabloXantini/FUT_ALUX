import numpy as np
import cv2
import sys
import os

# Importar fast_math desde el directorio vision_cpp
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

    def set_light(self, light_state):
        if self.renderer:
            self.renderer.set_light(light_state)

    def set_fisheye(self, k=-0.4, zoom=1.0):
        if self.renderer:
            self.renderer.set_fisheye(k, zoom)

    def set_motion_blur(self, strength=0.5, samples=3):
        if self.renderer:
            self.renderer.set_motion_blur(strength, samples)

    def render(self, cam_state, objects):
        if not self.renderer: return None
        
        self.renderer.render(cam_state, objects)
        frame = self.renderer.get_frame().reshape((self.height, self.width, 4))
        # Convertir RGBA a BGR y flipear (OpenGL es Y-up)
        return cv2.flip(cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR), -1)
