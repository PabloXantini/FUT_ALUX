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

    def get_walls(self, thickness=4):
        walls = []
        if self.rect.x < 80: # Left Goal
            walls.append(pygame.Rect(self.rect.left - thickness, self.rect.top - thickness, thickness, self.rect.height + thickness*2)) # Back
            walls.append(pygame.Rect(self.rect.left, self.rect.top - thickness, self.rect.width, thickness)) # Top
            walls.append(pygame.Rect(self.rect.left, self.rect.bottom, self.rect.width, thickness)) # Bottom
        else: # Right Goal
            walls.append(pygame.Rect(self.rect.right, self.rect.top - thickness, thickness, self.rect.height + thickness*2)) # Back
            walls.append(pygame.Rect(self.rect.left, self.rect.top - thickness, self.rect.width, thickness)) # Top
            walls.append(pygame.Rect(self.rect.left, self.rect.bottom, self.rect.width, thickness)) # Bottom
        return walls

    def draw(self, screen):
        # Dibujar la portería de forma semitransparente o caja con borde
        pygame.draw.rect(screen, self.team_color, self.rect, 0) # Relleno
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2) # Borde blanco

class Pitch(Entity):
    """
    Entidad que representa el campo de juego y sus reglas espaciales.
    """
    def __init__(self, width, height, padding=40):
        super().__init__(width / 2, height / 2)
        self.width = width
        self.height = height
        self.padding = padding # Distancia al frente de las porterías
        self.penalty_h = 260
        self.penalty_w = 80
        self.ally_penalty_zone = pygame.Rect(self.padding, self.height//2 - self.penalty_h//2, self.penalty_w, self.penalty_h)
        self.enemy_penalty_zone = pygame.Rect(self.width - (self.padding + self.penalty_w), self.height//2 - self.penalty_h//2, self.penalty_w, self.penalty_h)
        self.safe_zone = pygame.Rect(self.padding, self.padding, self.width - self.padding * 2, self.height - self.padding * 2)
        
        # Atributos estéticos compartidos
        self.main_color = (255, 255, 255)
        self.main_thick = 4
        self.safe_color = (200, 200, 200)
        self.safe_thick = 2

    def check_bounds(self, ball, goals):
        """Verifica si la pelota ha salido de la zona segura."""
        if ball.dragging: return False
        
        if not self.safe_zone.collidepoint(ball.x, ball.y):
            # Si no es un gol (no colisiona con el área de la portería extendida), es fuera
            # Extendemos el área de la portería para que no castigue si pega en los postes
            is_goal = False
            for g in goals:
                extended_goal = g.rect.inflate(20, 20)
                if extended_goal.collidepoint(ball.x, ball.y):
                    is_goal = True
                    break
                    
            if not is_goal:
                return True # Debe resetearse
        return False

    def draw(self, screen):
        # Campo verde oscuro
        screen.fill((30, 100, 40))
        
        # Línea Central y Círculo
        pygame.draw.line(screen, self.main_color, (self.width // 2, 0), (self.width // 2, self.height), self.main_thick)
        pygame.draw.circle(screen, self.main_color, (self.width // 2, self.height // 2), 100, self.main_thick)
        
        # PENALTY AREAS
        # Área Izquierda
        pygame.draw.rect(screen, self.main_color, self.ally_penalty_zone, self.main_thick)
        # Área Derecha
        pygame.draw.rect(screen, self.main_color, self.enemy_penalty_zone, self.main_thick)
        
        # SAFE ZONE
        pygame.draw.rect(screen, self.safe_color, self.safe_zone, self.safe_thick)

class Ball(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.radius = 8
        self.z_height = 8.0  # Pelota esférica, altura tridimensional == radio
        self.vx = 0.0
        self.vy = 0.0
        self.dragging = False
        self.last_kicked_by = None

    def update(self, game):
        # La lógica de arrastre y cinemática básica ahora se maneja en physics.py
        pass

    def draw(self, screen):
        pygame.draw.circle(screen, Color(255, 100, 0), (int(self.x), int(self.y)), self.radius)

class Robot(Entity):
    def __init__(self, color, brain, kickoff_x=None, kickoff_y=None):
        import random
        self.is_random_kickoff = (kickoff_x is None) or (kickoff_y is None)
        self.kickoff_x = kickoff_x if kickoff_x is not None else random.uniform(100, 700)
        self.kickoff_y = kickoff_y if kickoff_y is not None else random.uniform(100, 500)
        super().__init__(self.kickoff_x, self.kickoff_y)
        self.radius = 30
        self.z_height = 60.0  # Altura tridimensional del robot
        self.rangle = 0.0
        self.color = color  # Atributo del color de equipo al que pertenece
        self.ban_timer = 0.0
        self.attach_agent(brain)

    def attach_agent(self, brain):
        machine, context = brain
        """Inyecta el cerebro del FSM para que forme parte intrínseca de esta entidad"""
        self.machine = machine
        self.context = context
        self.name = context.name
        self.team = context.team_color
        self.context.link_robot(self)

    def update(self, game, robots=None):
        if self.ban_timer > 0:
            self.ban_timer -= 1/60.0
            if self.ban_timer < 0:
                self.ban_timer = 0
            return  # Inactive robot

        # Ejecutar Lógica de Agente FSM (Autonomía)
        if self.machine and self.context:
            sim_state = SimState(
                ball=game.ball, 
                robots=robots or [], 
                goals=[game.ally_goal, game.enemy_goal],
                pitch=game.pitch
            )
            self.context.compute(sim_state)
            self.machine.run(self.context)
            
        # La física se delega a physics.py

    def draw(self, screen, debug=False):
        if self.ban_timer > 0:
            return # Desaparece del tablero si está baneado
            
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
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius, 4)
        
        # Dirección "Frente" (Línea central indicadora)
        end_x = self.x + math.cos(self.rangle) * (self.radius * 1.2)
        end_y = self.y + math.sin(self.rangle) * (self.radius * 1.2)
        pygame.draw.line(screen, (255, 255, 255), (self.x, self.y), (end_x, end_y), 3)
