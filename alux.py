"""
main.py – Robot de fútbol con FSM
==================================
Para añadir un nuevo comportamiento:
  1. Crea un State en utils/r_states.py
  2. Crea las Rule(s) en utils/r_rules.py
  3. Construye tu FSM en build_machine() abajo
"""

from __future__ import annotations

import cv2
import argparse
from fsm import Machine
from utils.r_context import RobotContext
from utils.r_states import (
    Search, 
    LookBall, 
    GotoBall, 
    LookForShot,
    GotoGoal
)
from utils.r_rules import (
    BallDetected,
    BallLost,
    BallOffCenter,
    BallCentered,
    BallClose,
    BallEnemyGoalAligned,
    NotBallEnemyGoalAligned
)

def build_machine(debug: bool = False, sandbox: bool = False, name: str = "aluxe", team_color: str = "blue") -> tuple[Machine, object]:
    if sandbox:
        from sandbox.sim_context import SimContext
        ctx = SimContext(debug=debug, name=name, team_color=team_color)
    else:
        from utils.r_context import RobotContext
        ctx = RobotContext(debug=debug, name=name, team_color=team_color)

    # ── Instanciar estados ────────────────────────────────────────────────────
    search = Search()
    l_ball = LookBall()
    g_ball = GotoBall()
    l_shot  = LookForShot()
    g_goal = GotoGoal()

    # ── Máquina (estado inicial: búsqueda) ────────────────────────────────────
    machine = Machine(search)

    # ── Transiciones ──────────────────────────────────────────────────────────
    #  Desde       → Hacia        Cuando
    # SEARCH
    machine.add(search, l_ball, BallDetected())
    # LOOKBALL
    machine.add(l_ball, g_ball, BallCentered())
    machine.add(l_ball, search, BallLost())
    machine.add(l_ball, l_shot, BallClose())
    # GOTOBALL
    machine.add(g_ball, l_ball, BallOffCenter())
    machine.add(g_ball, search, BallLost())
    machine.add(g_ball, l_shot, BallClose())
    # WAITFORSHOT
    machine.add(l_shot, g_goal, BallEnemyGoalAligned())
    machine.add(l_shot, l_ball, NotBallEnemyGoalAligned())
    machine.add(l_shot, g_goal, BallClose())
    machine.add(l_shot, l_ball, BallOffCenter())
    # GOTOGOAL
    machine.add(g_goal, l_ball, BallOffCenter())
    machine.add(g_goal, search, BallLost())

    return machine, ctx

def main():
    parser = argparse.ArgumentParser(description="Robot Agent Alpha 1")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (UI)")
    parser.add_argument("--sandbox", action="store_true", help="Run FSM in Pygame 2D simulator")
    parser.add_argument("--split-cams", action="store_true", help="Muestra ventanas individuales para la visión en lugar del mosaico")
    args = parser.parse_args()

    if args.sandbox:
        import math
        from sandbox.game import GameController
        from sandbox.entities import Robot
        
        game = GameController(debug=args.debug, mosaic=not args.split_cams)
        
        team_colors = {
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0)
        }

        # TEAM BLUE
        # Robot 1 (Aliado - Azul) - Empieza en la izquierda mirando a la derecha
        brain1 = build_machine(debug=args.debug, sandbox=True, name='Cuau', team_color="blue")
        robot1 = Robot(x=200, y=150, color=team_colors['blue'], brain=brain1)

        brain2 = build_machine(debug=args.debug, sandbox=True, name='Sanchez', team_color="blue")
        robot2 = Robot(x=200, y=450, color=team_colors['blue'], brain=brain2)

        # TEAM YELLOW
        # Robot 2 (Enemigo - Amarillo) - Empieza en la derecha mirando a la izquierda
        brain3 = build_machine(debug=args.debug, sandbox=True, name='Messi', team_color="yellow")
        robot3 = Robot(x=600, y=150, color=team_colors['yellow'], brain=brain3)
        robot3.rangle = math.pi # Rotar 180 grados inicial

        brain4 = build_machine(debug=args.debug, sandbox=True, name='Cristiano', team_color="yellow")
        robot4 = Robot(x=600, y=450, color=team_colors['yellow'], brain=brain4)
        robot4.rangle = math.pi # Rotar 180 grados inicial

        robots = [robot1, robot2, robot3, robot4]

        try:
            while game.running:
                game.step(robots)
                game.render(robots)
                
                # Renderizar todas las cámaras simuladas en OpenCV si estamos en modo debug
                if args.debug:
                    game.show_virtual_cameras(robots)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        game.running = False
        except KeyboardInterrupt:
            pass
        finally:
            game.cleanup()
            cv2.destroyAllWindows()
    else:
        machine, ctx = build_machine(debug=args.debug, sandbox=False)
        try:
            while True:
                if not ctx.compute():
                    break
                machine.run(ctx)
                ctx.show_debug()
                if args.debug:
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        except KeyboardInterrupt:
            pass
        finally:
            ctx.cleanup()


if __name__ == "__main__":
    main()
