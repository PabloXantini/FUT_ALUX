from abc import ABC, abstractmethod
import numpy as np

class Vertex:
    def __init__(self, x, y, z, nx=0, ny=0, nz=1):
        self.x = x
        self.y = y
        self.z = z
        self.nx = nx
        self.ny = ny
        self.nz = nz

class RenderObject:
    """ Representa un objeto en la escena (Mesh, Círculo, Cilindro) """
    TYPE_MESH = 0
    TYPE_CIRCLE = 1
    TYPE_CYLINDER = 2

    def __init__(self, obj_type, color):
        self.type = obj_type
        self.color = color # (r, g, b, a) o (r, g, b)
        self.vertices = [] # Solo para TYPE_MESH
        self.position = [0, 0, 0] # Para primitivas
        self.size = [0, 0, 0]     # Para primitivas

class Scene(ABC):
    """ Centraliza todos los elementos visuales de la simulación """
    def __init__(self):
        self.objects = []  # Todos los objetos (Estáticos y Dinámicos)
        self.initialized = False

    @abstractmethod
    def load(self, state):
        """ Construye la geometría inicial y registra entidades """
        pass

    @abstractmethod
    def update(self, state):
        """ Actualiza los atributos de las entidades registradas """
        pass
