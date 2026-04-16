from __future__ import annotations

from fsm import State
from utils.r_context import RobotContext
 
 
class SearchState(State):
    """
    Sin pelota visible → gira en círculo buscando.
    Estado inicial del robot.
    """
 
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Buscando..."
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        ctx.motors.girar_derecha()
 
 
class AlignState(State):
    """
    Pelota visible pero descentrada → gira despacio para centrarla.
    """
 
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Alineando..."
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        if ctx.offset_x is None:
            return
        if ctx.offset_x > 0:
            # Pelota a la derecha en imagen → corregir girando a la derecha
            ctx.estado_label = "Giro -> DER (Ajustando)"
            ctx.motors.girar_lento_izquierda()
        else:
            # Pelota a la izquierda en imagen → corregir girando a la izquierda
            ctx.estado_label = "Giro <- IZQ (Ajustando)"
            ctx.motors.girar_lento_derecha()
 
 
class ApproachState(State):
    """
    Pelota centrada pero lejos → avanza hacia ella.
    """
 
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Avanzando..."
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        ctx.estado_label = f"Centrada: Avanzando (R:{ctx.radius})"
        ctx.motors.adelante_lento()
 
 
class StopState(State):
    """
    Pelota muy cerca → robot detenido listo para chutar.
    Aquí puedes añadir la lógica de chute en el futuro.
    """
 
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "¡CERCA! Detenido"
        ctx.motors.stop()
 
    def on_exit(self, ctx: RobotContext):
        pass
 
    def execute(self, ctx: RobotContext):
        # Placeholder: aquí iría la lógica de chute
        ctx.estado_label = "¡CERCA! Detenido"