import numpy as np
import cv2
import math
import os
import sys

from .vision_py.renderer import Renderer

class VirtualCamera:
    """ 
    Fachada para el sistema de visión.
    Encapsula la configuración de la cámara y delega el renderizado al Renderer.
    """
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
        self.yaw_off = 0.0
        self.roll = 0.0
        
        # El Renderer se encarga de elegir entre C++ (OpenGL) y Python (OpenCV)
        self.renderer = Renderer(width, height)

    def set_light_level(self, ambient=0.4, diffuse=0.8, x=320, y=240, z=500):
        """ Ajusta la iluminación del escenario (solo C++) """
        self.renderer.set_light(ambient, diffuse, (x, y, z))

    def set_fisheye_params(self, k=-0.4, zoom=1.0):
        """ Ajusta la distorsión de barril/cojín """
        self.renderer.set_fisheye(k, zoom)

    def set_motion_blur(self, strength=0.5, samples=3):
        """ Ajusta el desenfoque de movimiento (solo C++) """
        self.renderer.set_motion_blur(strength, samples)

    def render(self, observer, state):
        """
        Renderiza la escena desde la perspectiva del observer.
        """
        camera_params = {
            'focal_length': self.focal_length,
            'height': self.camera_height,
            'pitch': self.pitch,
            'yaw_off': self.yaw_off,
            'roll': self.roll,
            'enable_fisheye': True,
            'enable_motion_blur': True
        }
        
        frame = self.renderer.render(observer, state, camera_params)
        
        return frame
