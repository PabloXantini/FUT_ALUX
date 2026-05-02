from fsm import Machine
from utils.r_context import RobotContext
from utils.r_states import (
    Search, 
    LookBall, 
    GotoBall, 
    LookForShot,
    GotoEnemyGoal,
    RedirectBall,
    AvoidAllyGoal
)
from utils.r_rules import (
    BallDetected,
    BallLost,
    BallOffCenter,
    BallCentered,
    BallClose,
    BallEnemyGoalAligned,
    BallAllyGoalAligned,
    NotBallEnemyGoalAligned,
    NotBallAllyGoalAligned,
    NoGoals
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
    g_goal = GotoEnemyGoal()
    r_ball = RedirectBall()
    a_goal = AvoidAllyGoal()

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
    machine.add(l_shot, a_goal, NotBallAllyGoalAligned())
    machine.add(l_shot, a_goal, BallAllyGoalAligned())
    machine.add(l_shot, r_ball, NoGoals())
    machine.add(l_shot, g_goal, BallClose())
    machine.add(l_shot, l_ball, BallOffCenter())
    machine.add(l_shot, search, BallLost())
    # GOTOGOAL
    machine.add(g_goal, l_ball, BallOffCenter())
    machine.add(g_goal, search, BallLost())
    # REDIRECTBALL
    machine.add(r_ball, l_ball, BallOffCenter())
    machine.add(r_ball, search, BallLost())
    # AVOIDALLYGOAL
    machine.add(a_goal, l_ball, BallOffCenter())
    machine.add(a_goal, search, BallLost())

    return machine, ctx
