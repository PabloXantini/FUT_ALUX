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

    machine, ctx = build_machine(debug=args.debug, sandbox=args.sandbox)

    try:
        while True:
            if not ctx.compute():
                break                      # cámara sin frames → salir
            machine.run(ctx)               # FSM: evalúa transición + ejecuta
            ctx.show_debug()               # muestra frame con overlay
            if args.debug and not args.sandbox:
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        pass
    finally:
        ctx.cleanup()


if __name__ == "__main__":
    main()