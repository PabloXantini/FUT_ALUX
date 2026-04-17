import pygame
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from sandbox.entities import Ball, Goal

class GameController:
    def __init__(self, width=800, height=600, debug=False):
        self.debug = debug
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("FUT_ALUX - 2D Match Sandbox")
        self.clock = pygame.time.Clock()
        self.running = True

        self.score = {"blue": 0, "yellow": 0}

        # Entidades globales
        self.ball = Ball(width / 2, height / 2)
        
        # Meta Aliada = Azul, Meta Enemiga = Amarilla
        self.ally_goal = Goal(0, height / 2 - 75, 40, 150, (30, 80, 200)) # Azul Izq
        self.enemy_goal = Goal(width - 40, height / 2 - 75, 40, 150, (220, 220, 20)) # Amarillo Der

    def check_goals(self):
        # Evitar goles fantasma si el usuario está sosteniendo/arrastrando la pelota con el mouse
        if self.ball.dragging:
            return
        # Lógica de juego: ¿La pelota tocó el rectángulo de gol?
        if self.ally_goal.rect.collidepoint(self.ball.x, self.ball.y):
            self.score["yellow"] += 1
            self.reset_ball()
        elif self.enemy_goal.rect.collidepoint(self.ball.x, self.ball.y):
            self.score["blue"] += 1
            self.reset_ball()

    def reset_ball(self):
        self.ball.x = self.width / 2
        self.ball.y = self.height / 2
        self.ball.vx = 0
        self.ball.vy = 0

    def step(self, robots):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        self.ball.update(self)
        for robot in robots:
            robot.update(self)
            
        self.check_goals()

    def render(self, robots):
        # Campo verde oscuro
        self.screen.fill((30, 100, 40))
        
        # Dibujo de las líneas de la cancha
        pygame.draw.line(self.screen, (255, 255, 255), (self.width // 2, 0), (self.width // 2, self.height), 2)
        pygame.draw.circle(self.screen, (255, 255, 255), (self.width // 2, self.height // 2), 60, 2)
        
        self.ally_goal.draw(self.screen)
        self.enemy_goal.draw(self.screen)
        
        for robot in robots:
            robot.draw(self.screen, debug=self.debug)
            
        self.ball.draw(self.screen)

        # Tablero de Puntuación UI
        font = pygame.font.SysFont(None, 48)
        score_txt = font.render(f"AZUL {self.score['blue']} - {self.score['yellow']} AMARILLO", True, (255, 255, 255))
        self.screen.blit(score_txt, (self.width / 2 - score_txt.get_width() / 2, 20))

        # Interfaz de depuración (Muestra estado de cada robot si lo hay)
        if robots:
            font_small = pygame.font.SysFont(None, 24)
            y_offset = 10
            for r in robots:
                if r.context:
                    lbl = font_small.render(f"FSM Robot [{r.team_color}]: {r.context.estado_label}", True, (255, 255, 255))
                    self.screen.blit(lbl, (10, y_offset))
                    y_offset += 25

        pygame.display.flip()
        self.clock.tick(60) # 60 FPS
        
    def cleanup(self):
        pygame.quit()
