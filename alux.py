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
from tests.builder import build_machine
from tests.matchs import prepare_2v2, prepare_1v1

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
        
        robots = prepare_2v2(debug=args.debug, sandbox=args.sandbox) 

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
