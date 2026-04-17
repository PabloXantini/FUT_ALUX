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
from utils.r_states import SearchState, AlignState, ApproachState, StopState
from utils.r_rules import (
    BallDetectedRule,
    BallLostRule,
    BallOffCenterRule,
    BallCenteredRule,
    BallCloseRule,
)

def build_machine(debug: bool = False, sandbox: bool = True) -> tuple[Machine, object]:
    if sandbox:
        from sandbox.sim_context import SimContext
        ctx = SimContext(debug=debug)
    else:
        from utils.r_context import RobotContext
        ctx = RobotContext(debug=debug)

    # ── Instanciar estados ────────────────────────────────────────────────────
    search   = SearchState()
    align    = AlignState()
    approach = ApproachState()
    stop_st  = StopState()

    # ── Máquina (estado inicial: búsqueda) ────────────────────────────────────
    machine = Machine(search)

    # ── Transiciones ──────────────────────────────────────────────────────────
    #  Desde       → Hacia        Cuando
    machine.add(search,   align,    BallDetectedRule())   # ve la pelota
    machine.add(align,    search,   BallLostRule())       # pierde la pelota
    machine.add(align,    approach, BallCenteredRule())   # centrada y lejos
    machine.add(align,    stop_st,  BallCloseRule())      # centrada y cerca
    machine.add(approach, align,    BallOffCenterRule())  # se descentró
    machine.add(approach, search,   BallLostRule())       # perdió la pelota
    machine.add(approach, stop_st,  BallCloseRule())      # llegó cerca
    machine.add(stop_st,  search,   BallLostRule())       # perdió la pelota
    machine.add(stop_st,  align,    BallOffCenterRule())  # se movió

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
        machine, ctx = build_machine(debug=args.debug, sandbox=True)
        
        # El robot defiende la meta azul (Izquierda) y mira hacia la derecha
        robot = RobotEntity(x=200, y=game.height / 2, team_color=(0, 0, 255))
        robot.attach_agent(machine, ctx)
        
        try:
            while game.running:
                game.step([robot])
                game.render([robot])
                
                # Renderizar cámara simulada en OpenCV si estamos en modo debug
                if args.debug and robot.context:
                    robot.context.show_debug()
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