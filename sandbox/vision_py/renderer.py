import math
from .scene import Scene, RenderObject, Vertex
from .python_renderer import OpenCVRenderer
from .cpp_renderer import OpenGLRenderer

class Renderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Backends
        self.cpp_backend = OpenGLRenderer(width, height)
        self.py_backend = OpenCVRenderer(width, height)
        
        self.scene = Scene()
        
    def render(self, observer, state, camera_params):
        if not self.scene.initialized:
            self.load_scene(state)
        self.update_scene(state)
        
        # Preferir C++ si está disponible
        if self.cpp_backend.is_available():
           return self.cpp_backend.render(observer, self.scene, camera_params)
        else:
            return self.py_backend.render(observer, self.scene, camera_params)

    def load_scene(self, state):
        """ Construye la geometría estática del campo """
        self.scene.static_objects = []
        if not state.pitch: return
        
        w, h = state.pitch.width, state.pitch.height
        
        # 1. Pasto
        pasto = RenderObject(RenderObject.TYPE_MESH, (0.05, 0.25, 0.05, 1.0))
        self._add_quad(pasto, [0,0,0], [w,0,0], [w,h,0], [0,h,0], [0,0,1])
        self.scene.static_objects.append(pasto)
        
        # 2. Líneas
        p = state.pitch.padding
        t = 6.0 
        z_off = 0.1
        lines = RenderObject(RenderObject.TYPE_MESH, (1.0, 1.0, 1.0, 1.0))
        sz = state.pitch.safe_zone
        self._add_quad(lines, [sz.left, sz.top, z_off], [sz.right, sz.top, z_off], [sz.right, sz.top+t, z_off], [sz.left, sz.top+t, z_off], [0,0,1])
        self._add_quad(lines, [sz.left, sz.bottom-t, z_off], [sz.right, sz.bottom-t, z_off], [sz.right, sz.bottom, z_off], [sz.left, sz.bottom, z_off], [0,0,1])
        self._add_quad(lines, [sz.left, sz.top, z_off], [sz.left+t, sz.top, z_off], [sz.left+t, sz.bottom, z_off], [sz.left, sz.bottom, z_off], [0,0,1])
        self._add_quad(lines, [sz.right-t, sz.top, z_off], [sz.right, sz.top, z_off], [sz.right, sz.bottom, z_off], [sz.right-t, sz.bottom, z_off], [0,0,1])
        
        mid_x = w / 2
        self._add_quad(lines, [mid_x-t/2, p, z_off], [mid_x+t/2, p, z_off], [mid_x+t/2, h-p, z_off], [mid_x-t/2, h-p, z_off], [0,0,1])
        
        # Círculo Central
        r_circle = 100.0 
        segments = 32
        for i in range(segments):
            a1, a2 = (i/segments)*2*math.pi, ((i+1)/segments)*2*math.pi
            v1 = [mid_x + r_circle*math.cos(a1), h/2 + r_circle*math.sin(a1), z_off]
            v2 = [mid_x + r_circle*math.cos(a2), h/2 + r_circle*math.sin(a2), z_off]
            v1_in = [mid_x + (r_circle-t)*math.cos(a1), h/2 + (r_circle-t)*math.sin(a1), z_off]
            v2_in = [mid_x + (r_circle-t)*math.cos(a2), h/2 + (r_circle-t)*math.sin(a2), z_off]
            self._add_quad(lines, v1_in, v1, v2, v2_in, [0,0,1])
            
        # Áreas de Penalti
        for pz in [state.pitch.ally_penalty_zone, state.pitch.enemy_penalty_zone]:
            self._add_quad(lines, [pz.left, pz.top, z_off], [pz.right, pz.top, z_off], [pz.right, pz.top+t, z_off], [pz.left, pz.top+t, z_off], [0,0,1])
            self._add_quad(lines, [pz.left, pz.bottom-t, z_off], [pz.right, pz.bottom-t, z_off], [pz.right, pz.bottom, z_off], [pz.left, pz.bottom, z_off], [0,0,1])
            if pz.left < w/2: self._add_quad(lines, [pz.right-t, pz.top, z_off], [pz.right, pz.top, z_off], [pz.right, pz.bottom, z_off], [pz.right-t, pz.bottom, z_off], [0,0,1])
            else: self._add_quad(lines, [pz.left, pz.top, z_off], [pz.left+t, pz.top, z_off], [pz.left+t, pz.bottom, z_off], [pz.left, pz.bottom, z_off], [0,0,1])

        self.scene.static_objects.append(lines)
        
        eps = 0.5
        # 3. Porterías
        for g in state.goals:
            c = (g.team_color[0]/255, g.team_color[1]/255, g.team_color[2]/255, 1.0)
            goal = RenderObject(RenderObject.TYPE_MESH, c)
            x0, x1, y0, y1, z0, z1 = g.x, g.x+g.width, g.y, g.y+g.height, 0, g.z_height
            # Internal faces
            self._add_quad(goal, [x0,y0,z1], [x1,y0,z1], [x1,y1,z1], [x0,y1,z1], [0,0,-1])              # Ceiling
            if x0 < mid_x: self._add_quad(goal, [x0,y0,z0], [x0,y1,z0], [x0,y1,z1], [x0,y0,z1], [1,0,0])  # Bottom 
            else: self._add_quad(goal, [x1,y0,z0], [x1,y1,z0], [x1,y1,z1], [x1,y0,z1], [-1,0,0])        # Bottom
            self._add_quad(goal, [x0,y0,z0], [x1,y0,z0], [x1,y0,z1], [x0,y0,z1], [0,1,0])               # Side L
            self._add_quad(goal, [x0,y1,z0], [x1,y1,z0], [x1,y1,z1], [x0,y1,z1], [0,-1,0])              # Side R
            self.scene.static_objects.append(goal)
            # External faces
            c = (0, 0, 0, 1.0)
            goal_ext = RenderObject(RenderObject.TYPE_MESH, c)
            self._add_quad(goal_ext, [x0,y0,z1+eps], [x1,y0,z1+eps], [x1,y1,z1+eps], [x0,y1,z1+eps], [0,0,1])              # Ceiling
            if x0 < w/2: self._add_quad(goal_ext, [x0-eps,y0,z0], [x0-eps,y1,z0], [x0-eps,y1,z1], [x0-eps,y0,z1], [-1,0,0])  # Bottom 
            else: self._add_quad(goal_ext, [x1+eps,y0,z0], [x1+eps,y1,z0], [x1+eps,y1,z1], [x1+eps,y0,z1], [1,0,0])        # Bottom
            self._add_quad(goal_ext, [x0,y0-eps,z0], [x1,y0-eps,z0], [x1,y0-eps,z1], [x0,y0-eps,z1], [0,-1,0])               # Side L
            self._add_quad(goal_ext, [x0,y1+eps,z0], [x1,y1+eps,z0], [x1,y1+eps,z1], [x0,y1+eps,z1], [0,1,0])              # Side R
            self.scene.static_objects.append(goal_ext)

        # 4. Paredes
        wall_h = 60.0
        walls = RenderObject(RenderObject.TYPE_MESH, (0, 0, 0, 1.0))
        self._add_quad(walls, [-eps,-eps,0], [-eps,h+eps,0], [-eps,h+eps,wall_h], [-eps,-eps,wall_h], [1,0,0])
        self._add_quad(walls, [w+eps,-eps,0], [w+eps,h+eps,0], [w+eps,h+eps,wall_h], [w+eps,-eps,wall_h], [-1,0,0])
        self._add_quad(walls, [-eps,-eps,0], [w+eps,-eps,0], [w+eps,-eps,wall_h], [-eps,-eps,wall_h], [0,1,0])
        self._add_quad(walls, [-eps,h+eps,0], [w+eps,h+eps,0], [w+eps,h+eps,wall_h], [-eps,h+eps,wall_h], [0,-1,0])
        self.scene.static_objects.append(walls)

        self.scene.initialized = True

    def update_scene(self, state):
        """ Actualiza robots y pelota """
        self.scene.clear_dynamic()
        if state.ball:
            ball = RenderObject(RenderObject.TYPE_CIRCLE, (1.0, 0.4, 0.0, 1.0))
            ball.position = [state.ball.x, state.ball.y, state.ball.radius]
            diameter = state.ball.radius*2
            ball.size = [diameter, diameter, diameter]
            self.scene.dynamic_objects.append(ball)
            
        dark = 0.1
        for r in state.robots:
            if r.ban_timer > 0: continue
            robot = RenderObject(RenderObject.TYPE_CYLINDER, (r.color[0]/255*dark, r.color[1]/255*dark, r.color[2]/255*dark, 1.0))
            robot.position = [r.x, r.y, r.z_height/2]
            diameter = r.radius*2
            robot.size = [diameter, diameter, r.z_height]
            self.scene.dynamic_objects.append(robot)

    def _add_quad(self, obj, p1, p2, p3, p4, n):
        v1, v2, v3, v4 = Vertex(*p1, *n), Vertex(*p2, *n), Vertex(*p3, *n), Vertex(*p4, *n)
        obj.vertices.extend([v1, v2, v3, v1, v3, v4])
    
    # OPTIONS FOR RENDERING
    def set_light(self, ambient, diffuse, light_pos):
        self.cpp_backend.set_light(ambient, diffuse, light_pos)

    def set_fisheye(self, k, zoom):
        self.cpp_backend.set_fisheye(k, zoom)
        self.py_backend.set_fisheye(k, zoom)

    def set_motion_blur(self, strength, samples):
        self.cpp_backend.set_motion_blur(strength, samples)
