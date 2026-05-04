import pygame
import os
import random
import math
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from sandbox.game.entities import Ball, Goal, Pitch
from sandbox.game.physics import PhysicsEngine
from sandbox.game.match_rules import MatchRules

class GameController:
    def __init__(self, width=800, height=600, debug=False, mosaic=True):
        self.debug = debug
        self.mosaic = mosaic
        pygame.init()
        self.width = width
        self.height = height
        icon_app = pygame.image.load('assets/aluxeiii.ico')
        pygame.display.set_icon(icon_app)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("FUT_ALUX - 2D Match Sandbox")
        self.clock = pygame.time.Clock()
        self.running = True

        # Entidades globales
        self.pitch = Pitch(width, height, padding=40)
        self.ball = Ball(width / 2, height / 2)
        
        self.ally_goal = Goal(0, height / 2 - 100, 40, 200, (30, 80, 200))
        self.enemy_goal = Goal(width - 40, height / 2 - 100, 40, 200, (220, 220, 20))

        # Modulos de Simulación
        self.physics = PhysicsEngine(width, height)
        self.rules = MatchRules(width, height, self.pitch, self.ally_goal, self.enemy_goal)

    def step(self, robots):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.rules.match_over:
                    self.rules.reset_match(robots, self.ball)
                elif event.key == pygame.K_q:
                    self.running = False

        if self.rules.match_over:
            return

        dt = 1.0 / 60.0
        
        # 1. Update Entities AI
        self.ball.update(self)
        for r in robots:
            r.update(self, robots)

        # 2. Update Rules
        self.rules.step(dt, self.ball, robots)

        # 3. Resolve Physics
        self.physics.step(dt, self.ball, robots, [self.ally_goal, self.enemy_goal])

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

        # 4. UI: Tablero de Puntuación y Tiempo
        font = pygame.font.SysFont(None, 48)
        score_txt = font.render(f"AZUL {self.rules.score['blue']} - {self.rules.score['yellow']} AMARILLO", True, (255, 255, 255))
        self.screen.blit(score_txt, (self.width / 2 - score_txt.get_width() // 2, 50))
        
        font_small = pygame.font.SysFont(None, 32)
        mins = int(self.rules.time_elapsed // 60)
        secs = int(self.rules.time_elapsed % 60)
        time_txt = font_small.render(f"Tiempo: {mins:02d}:{secs:02d} | Mitad {self.rules.current_half}", True, (200, 200, 200))
        self.screen.blit(time_txt, (self.width / 2 - time_txt.get_width() // 2, 10))

        if self.rules.match_over:
            font_large = pygame.font.SysFont(None, 72)
            font_larger = pygame.font.SysFont(None, 80)
            font_small2 = pygame.font.SysFont(None, 36)

            if self.rules.score["blue"] > self.rules.score["yellow"]:
                result = "GANA AZUL"
            elif self.rules.score["blue"] < self.rules.score["yellow"]:
                result = "GANA AMARILLO"
            else:
                result = "EMPATE"
            over_txt = font_large.render(f"FIN DEL JUEGO", True, (255, 255, 255))
            self.screen.blit(over_txt, (self.width / 2 - over_txt.get_width() // 2, self.height / 2 - 70))
            result_txt = font_larger.render(result, True, (255, 255, 255))
            self.screen.blit(result_txt, (self.width / 2 - result_txt.get_width() // 2, self.height / 2 - 20))
            restart_txt = font_small2.render("Presiona ENTER para reiniciar", True, (200, 200, 200))
            self.screen.blit(restart_txt, (self.width / 2 - restart_txt.get_width() // 2, self.height / 2 + 40))

        # 5. UI: Depuración FSM
        if robots:
            font_small = pygame.font.SysFont(None, 24)
            y_offset = 500
            for r in robots:
                if r.context:
                    color = (255, 50, 50) if r.ban_timer > 0 else (255, 255, 255)
                    ban_text = f" [BANEADO {int(r.ban_timer)}s]" if r.ban_timer > 0 else ""
                    lbl = font_small.render(f"FSM {r.name}[{r.team}]: {r.context.estado_label}{ban_text}", True, color)
                    self.screen.blit(lbl, (10, y_offset))
                    y_offset += 25

        # 6. Actualizar Ventana y FPS (Throttled a cada 30 frames para ahorrar CPU)
        if not hasattr(self, '_fps_tick'): self._fps_tick = 0
        self._fps_tick += 1
        if self._fps_tick >= 20:
            actual_fps = self.clock.get_fps()
            pygame.display.set_caption(f"FUT_ALUX - 2D Match Sandbox | FPS: {actual_fps:.1f}")
            self._fps_tick = 0
        
        pygame.display.flip()
        self.clock.tick(60) # Limitar a 60 FPS
        
    def show_virtual_cameras(self, robots):
        """Método helper para desplegar los streams visuales de todos los robots en modo mosaico o individual"""
        if self.debug:
            import cv2
            import numpy as np
            frames = []
            for robot in robots:
                if hasattr(robot, 'context') and robot.context:
                    if not self.mosaic:
                        robot.context.show_debug()
                    else:
                        frame = robot.context.get_debug_frame()
                        if frame is not None:
                            frames.append(frame)
            
            if self.mosaic and frames:
                # Calculate grid size (e.g. 2x2 for 4 robots, 3x2 for 6)
                n = len(frames)
                cols = int(np.ceil(np.sqrt(n)))
                rows = int(np.ceil(n / cols))
                
                # Resize and pad frames to assemble a grid
                h, w, c = frames[0].shape
                grid = np.zeros((h * rows, w * cols, c), dtype=np.uint8)
                
                for idx, frame in enumerate(frames):
                    r = idx // cols
                    c_idx = idx % cols
                    grid[r*h:(r+1)*h, c_idx*w:(c_idx+1)*w] = frame

                cv2.imshow("Virtual Cameras", grid)
        
    def cleanup(self):
        pygame.quit()
