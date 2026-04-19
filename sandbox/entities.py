from pygame.color import Color
import math
import pygame
from sandbox.sim_cache import SimState

class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, game):
        pass

    def draw(self, screen):
        pass

class Goal(Entity):
    def __init__(self, x, y, width, height, team_color):
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.z_height = 60.0  # Altura tridimensional de la portería
        self.team_color = team_color  # Color de equipo (ej. (0,0,255) Azul)
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        # Dibujar la portería de forma semitransparente o caja con borde
        pygame.draw.rect(screen, self.team_color, self.rect, 0) # Relleno
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2) # Borde blanco

class Ball(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = 8
        self.z_height = 8.0  # Pelota esférica, altura tridimensional == radio
        self.vx = 0.0
        self.vy = 0.0
        self.dragging = False

    def update(self, game):
        mx, my = pygame.mouse.get_pos()
        mb1, _, _ = pygame.mouse.get_pressed()

        if mb1:
            dist_to_mouse = math.hypot(mx - self.x, my - self.y)
            if dist_to_mouse < 30 or self.dragging:
                self.dragging = True
                self.vx = mx - self.x
                self.vy = my - self.y
                self.x = mx
                self.y = my
        else:
            self.dragging = False

        if not self.dragging:
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.90
            self.vy *= 0.90
            
            # Rebotes en paredes
            if self.x < self.radius: self.x = self.radius; self.vx *= -0.8
            if self.x > game.width - self.radius: self.x = game.width - self.radius; self.vx *= -0.8
            if self.y < self.radius: self.y = self.radius; self.vy *= -0.8
            if self.y > game.height - self.radius: self.y = game.height - self.radius; self.vy *= -0.8

    def draw(self, screen):
        pygame.draw.circle(screen, Color(255, 100, 0), (int(self.x), int(self.y)), self.radius)

class Robot(Entity):
    def __init__(self, x, y, team_color):
        super().__init__(x, y)
        self.radius = 23
        self.z_height = 40.0  # Altura tridimensional del robot
        self.rangle = 0.0
        self.team_color = team_color  # Atributo del color de equipo al que pertenece
        
        self.machine = None
        self.context = None

    def attach_agent(self, machine, context):
        """Inyecta el cerebro del FSM para que forme parte intrínseca de esta entidad"""
        self.machine = machine
        self.context = context
        self.context.link_robot(self)

    def update(self, game, robots=None):
        # 1. Ejecutar Lógica de Agente FSM (Autonomía)
        if self.machine and self.context:
            sim_state = SimState(
                ball=game.ball, 
                robots=robots or [], 
                goals=[game.ally_goal, game.enemy_goal]
            )
            self.context.compute(sim_state)
            self.machine.run(self.context)
        
        # 2. Cinematica / Física (usar actuador proveniente de Contexto)
        if self.context:
            v_turn = self.context.motors.v_turn
            v_fwd = self.context.motors.v_forward
            v_lat = self.context.motors.v_lateral
        else:
            v_turn = v_fwd = v_lat = 0.0

        f_x = math.cos(self.rangle)
        f_y = math.sin(self.rangle)
        r_x = -f_y
        r_y = f_x
        
        self.rangle += v_turn
        self.x += (f_x * v_fwd) + (r_x * v_lat)
        self.y += (f_y * v_fwd) + (r_y * v_lat)
        
        self.x = max(self.radius, min(game.width - self.radius, self.x))
        self.y = max(self.radius, min(game.height - self.radius, self.y))

        # 3. Colisiones físicas con la pelota
        ball = game.ball
        dr_x = ball.x - self.x
        dr_y = ball.y - self.y
        dist_rb = math.hypot(dr_x, dr_y)
        sum_radios = self.radius + ball.radius
        
        if dist_rb < sum_radios and dist_rb > 0:
            overlap = sum_radios - dist_rb
            nx, ny = dr_x / dist_rb, dr_y / dist_rb
            
            if not ball.dragging:
                ball.x += nx * overlap
                ball.y += ny * overlap
                
                # Transferencia de momento
                robot_vx = self.x - getattr(self, '_last_x', self.x)
                robot_vy = self.y - getattr(self, '_last_y', self.y)
                ball.vx += robot_vx * 0.5 + nx * 2.0
                ball.vy += robot_vy * 0.5 + ny * 2.0
            else:
                self.x -= nx * overlap
                self.y -= ny * overlap
                
        self._last_x = self.x
        self._last_y = self.y

    def draw(self, screen, debug=False):
        # Dibujar cono de visión si estamos en debug
        if debug:
            fov = math.radians(100) # Apertura visual abierta al igual que en la cámara sintética
            max_dist = 600
            p1 = (self.x, self.y)
            p2 = (self.x + math.cos(self.rangle - fov/2) * max_dist, 
                  self.y + math.sin(self.rangle - fov/2) * max_dist)
            p3 = (self.x + math.cos(self.rangle + fov/2) * max_dist, 
                  self.y + math.sin(self.rangle + fov/2) * max_dist)
            
            # Para que Pygame soporte la transparencia (Alpha), necesitamos dibujar en un Surface especial temporal
            transparent_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            # Dibujamos relleno semitransparente (Alpha = 60, es decir bastante tenue)
            pygame.draw.polygon(transparent_surf, (50, 180, 60, 60), [p1, p2, p3], 0)
            # Dibujamos las fronteras del cono visual opacas
            pygame.draw.polygon(transparent_surf, (50, 150, 60, 200), [p1, p2, p3], 2)
            
            # Pegamos nuestra capa transparente en la pantalla final
            screen.blit(transparent_surf, (0, 0))
            
        # Cuerpo del robot color equipo
        pygame.draw.circle(screen, self.team_color, (int(self.x), int(self.y)), self.radius, 4)
        
        # Dirección "Frente" (Línea central indicadora)
        end_x = self.x + math.cos(self.rangle) * (self.radius * 1.2)
        end_y = self.y + math.sin(self.rangle) * (self.radius * 1.2)
        pygame.draw.line(screen, (255, 255, 255), (self.x, self.y), (end_x, end_y), 3)
