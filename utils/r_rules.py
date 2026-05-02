from __future__ import annotations

from fsm import Rule
from utils.r_context import (
    RobotContext, 
    FRANJA_CENTRAL, 
    RADIO_OBJETIVO
)

class BallLost(Rule):
    """Pelota dejó de verse."""
    def applies(self, ctx: RobotContext) -> bool:
        return not ctx.info['ball']['detected']

class BallDetected(Rule):
    """Pelota visible por primera vez (o de vuelta)."""
    def applies(self, ctx: RobotContext) -> bool:
        return ctx.info['ball']['detected']

class BallOffCenter(Rule):
    """Pelota visible pero no en medio."""
    def applies(self, ctx: RobotContext) -> bool:
        ball = ctx.info['ball']
        return (ball['detected']
                and ball['offset_x'] is not None
                and abs(ball['offset_x']) > FRANJA_CENTRAL)

class BallCentered(Rule):
    """Pelota en medio pero lejos."""
    def applies(self, ctx: RobotContext) -> bool:
        ball = ctx.info['ball']
        return (ball['detected']
                and ball['offset_x'] is not None
                and abs(ball['offset_x']) <= FRANJA_CENTRAL
                and ball['radius'] < RADIO_OBJETIVO)

class BallClose(Rule):
    """Pelota centrada Y suficientemente cerca para detenerse/chutar."""
    def applies(self, ctx: RobotContext) -> bool:
        ball = ctx.info['ball']
        return (ball['detected']
                and ball['offset_x'] is not None
                and abs(ball['offset_x']) <= FRANJA_CENTRAL
                and ball['radius'] >= RADIO_OBJETIVO)

class BallEnemyGoalAligned(Rule):
    """Pelota esta alineada a la porteria"""
    def applies(self, ctx: RobotContext) -> bool:
        ball = ctx.info['ball']
        enemy_goal = ctx.info['enemy_goal']
        return (ball['detected']
                and enemy_goal['detected']
                and enemy_goal['offset_x'] is not None
                and abs(ball['offset_x']) <= FRANJA_CENTRAL
                and abs(enemy_goal['offset_x']) <= FRANJA_CENTRAL)
    
class NotBallEnemyGoalAligned(Rule):
    """Pelota esta alineada a la porteria"""
    def applies(self, ctx: RobotContext) -> bool:
        ball = ctx.info['ball']
        enemy_goal = ctx.info['enemy_goal']
        return (ball['detected']
                and enemy_goal['detected']
                and enemy_goal['offset_x'] is not None
                and (abs(ball['offset_x']) > FRANJA_CENTRAL
                or abs(enemy_goal['offset_x']) > FRANJA_CENTRAL))