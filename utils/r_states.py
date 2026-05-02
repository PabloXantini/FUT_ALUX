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
        ctx.motors.adelante(vel=ctx.motors.HIGH)
 
class LookForShot(State):
    """
    Action: Think.
    """
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "CERCA! Alineando a porteria"
 
    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
 
    def execute(self, ctx: RobotContext):
        o_ball = ctx.info['ball']['offset_x']
        o_goal = ctx.info['enemy_goal']['offset_x']
        if o_ball is None or o_goal is None:
            return
        self.align = o_ball - o_goal
        if self.align > 0:
            ctx.estado_label = f"Enfocando Meta: Derecha (A={self.align})"
            ctx.motors.lateral_derecha()
        else:
            ctx.estado_label = f"Enfocando Meta: Izquierda (A={self.align})"
            ctx.motors.lateral_izquierda()
 
class GotoEnemyGoal(State):
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
        ctx.motors.adelante()

class RedirectBall(State):
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Redirigiendo pelota..."

    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
    
    def execute(self, ctx: RobotContext):
        o_ball = ctx.info['ball']['offset_x']
        if o_ball is None:
            return
        if o_ball > 0:
            ctx.estado_label = "Giro -> DER (Redirigiendo)"
            ctx.motors.lateral_izquierda(vel=ctx.motors.HIGH)
        else:
            ctx.estado_label = "Giro <- IZQ (Redirigiendo)"
            ctx.motors.lateral_derecha(vel=ctx.motors.HIGH)

class AvoidAllyGoal(State):
    def on_init(self, ctx: RobotContext):
        ctx.estado_label = "Evitando a porteria aliada..."

    def on_exit(self, ctx: RobotContext):
        ctx.motors.stop()
    
    def execute(self, ctx: RobotContext):
        o_ball = ctx.info['ball']['offset_x']
        o_goal = ctx.info['ally_goal']['offset_x']
        if o_goal is None or o_ball is None:
            return
        self.align = o_goal - o_ball
        if self.align > 0:
            ctx.estado_label = "Giro -> DER (Evitando)"
            ctx.motors.lateral_derecha(vel=ctx.motors.HIGH)
        else:
            ctx.estado_label = "Giro <- IZQ (Evitando)"
            ctx.motors.lateral_izquierda(vel=ctx.motors.HIGH)
    