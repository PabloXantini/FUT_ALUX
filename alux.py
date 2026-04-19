"""
main.py – Robot de fútbol con FSM
==================================
Para añadir un nuevo comportamiento:
  1. Crea un State en states.py
  2. Crea las Rule(s) en rules.py
  3. Agrega transiciones en build_machine() abajo
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
    BallGoalAligned,
    NotBallGoalAligned
)

def build_machine(debug: bool = False, sandbox: bool = False, team_color: str = "blue") -> tuple[Machine, object]:
    if sandbox:
        from sandbox.sim_context import SimContext
        ctx = SimContext(debug=debug, team_color=team_color)
    else:
        from utils.r_context import RobotContext
        ctx = RobotContext(debug=debug, team_color=team_color)

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
    machine.add(l_shot, g_goal, BallGoalAligned())
    machine.add(l_shot, l_ball, NotBallGoalAligned())
    machine.add(l_shot, l_ball, BallOffCenter())
    # GOTOGOAL
    machine.add(g_goal, l_ball, BallOffCenter())
    machine.add(g_goal, search, BallLost())
    """
    machine.add(search,   align,    BallDetectedRule())   # ve la pelota
    machine.add(align,    search,   BallLostRule())       # pierde la pelota
    machine.add(align,    approach, BallCenteredRule())   # centrada y lejos
    machine.add(align,    stop_st,  BallCloseRule())      # centrada y cerca
    machine.add(approach, align,    BallOffCenterRule())  # se descentró
    machine.add(approach, search,   BallLostRule())       # perdió la pelota
    machine.add(approach, stop_st,  BallCloseRule())      # llegó cerca
    machine.add(stop_st,  search,   BallLostRule())       # perdió la pelota
    machine.add(stop_st,  align,    BallOffCenterRule())  # se movió
    """


    return machine, ctx

def main():
    parser = argparse.ArgumentParser(description="Robot Agent Alpha 1")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (UI)")
    parser.add_argument("--sandbox", action="store_true", help="Run FSM in Pygame 2D simulator")
    args = parser.parse_args()

    if args.sandbox:
        from sandbox.game import GameController
        from sandbox.entities import RobotEntity
        
        game = GameController(debug=args.debug)
        
        # Robot 1 (Aliado - Azul) - Empieza en la izquierda mirando a la derecha
        machine1, ctx1 = build_machine(debug=args.debug, sandbox=True, team_color="blue")
        robot1 = RobotEntity(x=200, y=100, team_color=(0, 0, 255))
        robot1.attach_agent(machine1, ctx1)
        
        # Robot 2 (Enemigo - Amarillo) - Empieza en la derecha mirando a la izquierda
        machine2, ctx2 = build_machine(debug=args.debug, sandbox=True, team_color="yellow")
        robot2 = RobotEntity(x=200, y=200, team_color=(255, 255, 0))
        import math
        robot2.rangle = math.pi # Rotar 180 grados inicial
        robot2.attach_agent(machine2, ctx2)
        
        try:
            while game.running:
                game.step([robot1, robot2])
                game.render([robot1, robot2])
                
                # Renderizar todas las cámaras simuladas en OpenCV si estamos en modo debug
                if args.debug:
                    game.show_virtual_cameras([robot1, robot2])
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
