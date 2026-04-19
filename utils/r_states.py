from __future__ import annotations

from fsm import State
from utils.r_context import RobotContext
 
 
class Search(State):
    """
    Ball Detected -> Align
    Action: Spin to right
    """ 
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Buscando..."
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        ctx.motors.girar_derecha()
 
class LookBall(State):
    """
    Ball and Goal Aligned -> AproachToGoal
    Action: compute and align 
    """
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Alineando a pelota..."
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        self.align = ctx.info['ball']['offset_x']
        if self.align is None:
            return
        if self.align > 0:
            # Pelota a la derecha en imagen → corregir girando a la derecha
            ctx.estado_label = "Giro -> DER (Ajustando)"
            ctx.motors.girar_lento_izquierda()
        else:
            # Pelota a la izquierda en imagen → corregir girando a la izquierda
            ctx.estado_label = "Giro <- IZQ (Ajustando)"
            ctx.motors.girar_lento_derecha()
 
# REVISAR
class GotoBall(State):
    """
    Action: Forward
    """
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Avanzando..."
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        radius = ctx.info['ball']['radius']
        ctx.estado_label = f"Enfocando: Avanzando (R:{radius})"
        ctx.motors.adelante_lento()
 
class LookForShot(State):
    """
    Action: Think.
    """
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "¡CERCA! Alineando a porteria"
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        ctx.estado_label = "¡CERCA! Detenido"
 
class GotoGoal(State):
    """
    Domain the ball
    Action: Forward
    """
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Avanzando con balon..."
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        radius = ctx.info['ball']['radius']
        ctx.estado_label = f"CentradaMeta: Avanzando (R:{radius})"
        ctx.motors.adelante_lento()