import pygame
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from sandbox.entities import Ball, Goal, Pitch

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
        self.pitch = Pitch(width, height, padding=40)
        self.ball = Ball(width / 2, height / 2)
        
        # Meta Aliada = Azul (Izquierda), Meta Enemiga = Amarilla (Derecha)
        self.ally_goal = Goal(0, height / 2 - 100, 40, 200, (30, 80, 200))
        self.enemy_goal = Goal(width - 40, height / 2 - 100, 40, 200, (220, 220, 20))

    def check_goals(self):
        if self.ball.dragging: return
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False

        self.ball.update(self)
        for robot in robots:
            robot.update(self, robots)
            
        import math
        # Resolver colisiones físicas entre robots
        for i in range(len(robots)):
            for j in range(i + 1, len(robots)):
                r1, r2 = robots[i], robots[j]
                dx, dy = r2.x - r1.x, r2.y - r1.y
                dist = math.hypot(dx, dy)
                if 0 < dist < r1.radius + r2.radius:
                    overlap = (r1.radius + r2.radius - dist) / 2
                    nx, ny = dx / dist, dy / dist
                    r1.x -= nx * overlap; r1.y -= ny * overlap
                    r2.x += nx * overlap; r2.y += ny * overlap
            
        self.check_goals()
        # Verificar limites de campo (Zona Segura)
        if self.pitch.check_bounds(self.ball, [self.ally_goal, self.enemy_goal]):
            self.reset_ball()

    def render(self, robots):
        # 1. Dibujar Campo (Pitch)
        self.pitch.draw(self.screen)
        
        # 2. Dibujar Metas
        self.ally_goal.draw(self.screen)
        self.enemy_goal.draw(self.screen)
        
        # 3. Dibujar Entidades Dinámicas
        for robot in robots:
            robot.draw(self.screen, debug=self.debug)
        self.ball.draw(self.screen)

        # 4. UI: Tablero de Puntuación
        font = pygame.font.SysFont(None, 48)
        score_txt = font.render(f"AZUL {self.score['blue']} - {self.score['yellow']} AMARILLO", True, (255, 255, 255))
        self.screen.blit(score_txt, (self.width / 2 - score_txt.get_width() // 2, 50))

        # 5. UI: Depuración FSM
        if robots:
            font_small = pygame.font.SysFont(None, 24)
            y_offset = 10
            for r in robots:
                if r.context:
                    lbl = font_small.render(f"FSM {r.name}[{r.team}]: {r.context.estado_label}", True, (255, 255, 255))
                    self.screen.blit(lbl, (10, y_offset))
                    y_offset += 25

        # 6. Actualizar Ventana y FPS en título
        actual_fps = self.clock.get_fps()
        pygame.display.set_caption(f"FUT_ALUX - 2D Match Sandbox | FPS: {actual_fps:.1f}")
        pygame.display.flip()
        self.clock.tick(60) # Limitar a 60 FPS
        
    def show_virtual_cameras(self, robots):
        """Método helper para desplegar los streams visuales de todos los robots del motor en modo Debug"""
        if self.debug:
            for robot in robots:
                if hasattr(robot, 'context') and robot.context:
                    robot.context.show_debug()
        
    def cleanup(self):
        pygame.quit()
