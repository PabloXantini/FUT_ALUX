import math
import random
import pygame

class MatchRules:
    def __init__(self, width, height, pitch, ally_goal, enemy_goal):
        self.width = width
        self.height = height
        self.pitch = pitch
        self.ally_goal = ally_goal
        self.enemy_goal = enemy_goal

        self.score = {"blue": 0, "yellow": 0}
        self.match_minutes = 4
        self.match_seconds = 0
        self.total_match_time = self.match_minutes * 60 + self.match_seconds
        self.half_time = self.total_match_time / 2.0
        self.time_elapsed = 0.0
        self.current_half = 1

        self.ball_untouched_timer = 0.0
        self.MAX_GOAL_DIFF = 10
        self.BALL_UNTOUCHED_LIMIT = 10.0

        self.missing_team_timer = {"blue": 0.0, "yellow": 0.0}
        self.kickoff_team = random.choice(["blue", "yellow"])
        self.is_kickoff = True
        self.match_over = False

        self.RULE_PENALTY_BAN = False
        self.RULE_PENALTY_NEUTRAL = True
        self.RULE_PITCH_BOUNDS_BAN = True
        self.RULE_SAFE_LINES_BAN = True

        self.neutral_positions = {
            "blue": [(200, 150), (200, 450)],
            "yellow": [(600, 150), (600, 450)]
        }

    # --- Helpers ---
    def _get_free_neutral_points(self, r, robots):
        neutral_pts = self.neutral_positions[r.team]
        free_pts = []
        for pt in neutral_pts:
            occupied = False
            for other in robots:
                if other != r and other.team == r.team and other.ban_timer <= 0:
                    if math.hypot(other.x - pt[0], other.y - pt[1]) < other.radius * 2:
                        occupied = True
                        break
            if not occupied:
                free_pts.append(pt)
        return free_pts if free_pts else neutral_pts

    def _place_robot_at_neutral(self, r, robots, ball):
        free_pts = self._get_free_neutral_points(r, robots)
        best_pt = max(free_pts, key=lambda p: math.hypot(p[0] - ball.x, p[1] - ball.y))
        r.x, r.y = best_pt

    def _face_own_goal(self, r):
        goal_x = 0 if r.team == "blue" else self.width
        goal_y = self.height / 2
        r.rangle = math.atan2(goal_y - r.y, goal_x - r.x)

    def _face_ball(self, r, ball, variation=0.0):
        angle_to_ball = math.atan2(ball.y - r.y, ball.x - r.x)
        r.rangle = angle_to_ball + variation

    # --- Rules ---
    def _rule_pitch_bounds(self, r, is_active):
        if not is_active:
            return
        if (r.x <= r.radius + 2 or r.x >= self.width - r.radius - 2 or
            r.y <= r.radius + 2 or r.y >= self.height - r.radius - 2):
            in_goal_y = (self.ally_goal.rect.top - 20 <= r.y <= self.ally_goal.rect.bottom + 20)
            if in_goal_y and (r.x <= r.radius + 2 or r.x >= self.width - r.radius - 2):
                pass
            else:
                r.ban_timer = 60.0

    def _rule_penalty_zones(self, r, robots, ball, ban_active, neutral_active):
        r_rect = pygame.Rect(r.x - r.radius, r.y - r.radius, r.radius*2, r.radius*2)
        for zone in [self.pitch.ally_penalty_zone, self.pitch.enemy_penalty_zone]:
            if zone.contains(r_rect):
                if ban_active:
                    r.ban_timer = 60.0
            elif zone.colliderect(r_rect):
                if neutral_active:
                    for other in robots:
                        if other != r and other.team == r.team and other.ban_timer <= 0:
                            o_rect = pygame.Rect(other.x - other.radius, other.y - other.radius, other.radius*2, other.radius*2)
                            if zone.colliderect(o_rect):
                                dist_r = math.hypot(r.x - ball.x, r.y - ball.y)
                                dist_o = math.hypot(other.x - ball.x, other.y - ball.y)
                                target = r if dist_r >= dist_o else other
                                
                                free_pts = self._get_free_neutral_points(target, robots)
                                target.x, target.y = min(free_pts, key=lambda p: abs(p[1] - target.y))
                                break

    def _rule_safe_lines(self, ball, is_active):
        if not is_active:
            return
        if self.pitch.check_bounds(ball, [self.ally_goal, self.enemy_goal]):
            if ball.last_kicked_by:
                ball.last_kicked_by.ban_timer = 60.0
            self.reset_ball(ball)

    # --- Match Control ---
    def reset_match(self, robots, ball):
        self.score = {"blue": 0, "yellow": 0}
        self.time_elapsed = 0.0
        self.current_half = 1
        self.match_over = False
        self.kickoff_team = random.choice(["blue", "yellow"])
        self.setup_kickoff(robots, ball)

    def reset_ball(self, ball):
        ball.x = self.width / 2
        ball.y = self.height / 2
        ball.vx = 0
        ball.vy = 0
        ball.last_kicked_by = None
        self.ball_untouched_timer = 0.0

    def setup_kickoff(self, robots, ball):
        self.reset_ball(ball)
        self.is_kickoff = True
        
        assigned_kickoff = False
        for r in robots:
            r.ban_timer = 0.0
            r.was_banned = False
            if getattr(r, 'is_random_kickoff', False):
                r.kickoff_x = random.uniform(100, self.width - 100)
                r.kickoff_y = random.uniform(100, self.height - 100)
                
            base_x = r.kickoff_x
            base_y = r.kickoff_y
            
            if r.team == "blue":
                base_x = min(base_x, self.width / 2 - r.radius)
            else:
                base_x = max(base_x, self.width / 2 + r.radius)
            
            if r.team == self.kickoff_team:
                if not assigned_kickoff:
                    r.x = ball.x - 60 if r.team == "blue" else ball.x + 60
                    r.y = ball.y
                    assigned_kickoff = True
                else:
                    r.x = base_x + random.uniform(-10, 10)
                    r.y = base_y + random.uniform(-10, 10)
            else:
                r.x = base_x
                r.y = base_y
                dist = math.hypot(r.x - ball.x, r.y - ball.y)
                min_dist = 100 + r.radius + ball.radius
                if dist < min_dist:
                    if dist == 0:
                        dir_x, dir_y = (1, 0) if r.team == "blue" else (-1, 0)
                    else:
                        dir_x = (r.x - ball.x) / dist
                        dir_y = (r.y - ball.y) / dist
                    r.x = ball.x + dir_x * (min_dist + 5)
                    r.y = ball.y + dir_y * (min_dist + 5)

        for team in ["blue", "yellow"]:
            team_robots = [r for r in robots if r.team == team]
            if not team_robots: continue
            closest_r = min(team_robots, key=lambda r: math.hypot(r.x - ball.x, r.y - ball.y))
            for r in team_robots:
                if r == closest_r:
                    self._face_ball(r, ball, 0.0)
                else:
                    self._face_ball(r, ball, random.uniform(-math.pi/6, math.pi/6))

    def count_goals(self, team):
        match team:
            case "blue":
                diff = self.score["blue"] - self.score["yellow"]
            case "yellow":
                diff = self.score["yellow"] - self.score["blue"]
        if diff >= self.MAX_GOAL_DIFF:
            return 
        self.score[team] += 1

    def check_goals(self, ball, robots):
        if ball.dragging: return
        tolerance = 5.0
        if ((ball.x <= ball.radius + tolerance) and (self.ally_goal.rect.top <= ball.y <= self.ally_goal.rect.bottom)):
            self.count_goals("yellow")
            self.kickoff_team = "blue"
            self.setup_kickoff(robots, ball)
        elif ((ball.x >= self.width - ball.radius - tolerance) and (self.enemy_goal.rect.top <= ball.y <= self.enemy_goal.rect.bottom)):
            self.count_goals("blue")
            self.kickoff_team = "yellow"
            self.setup_kickoff(robots, ball)

    def apply_penalties(self, ball, robots):
        active_counts = {"blue": 0, "yellow": 0}
        total_counts = {"blue": 0, "yellow": 0}
        
        for r in robots:
            total_counts[r.team] += 1
            if r.ban_timer > 0: 
                r.was_banned = True
                continue
            
            if getattr(r, 'was_banned', False):
                r.was_banned = False
                self._place_robot_at_neutral(r, robots, ball)
                self._face_own_goal(r)

            active_counts[r.team] += 1
            
            self._rule_pitch_bounds(r, self.RULE_PITCH_BOUNDS_BAN)
            self._rule_penalty_zones(r, robots, ball, self.RULE_PENALTY_BAN, self.RULE_PENALTY_NEUTRAL)

        return total_counts, active_counts

    def step(self, dt, ball, robots):
        if self.match_over: return

        self.time_elapsed += dt
        
        # Check halves
        if self.current_half == 1 and self.time_elapsed >= self.half_time:
            self.current_half = 2
            self.kickoff_team = "yellow" if self.kickoff_team == "blue" else "blue"
            self.setup_kickoff(robots, ball)
        elif self.current_half == 2 and self.time_elapsed >= self.total_match_time:
            self.match_over = True
            
        total_counts, active_counts = self.apply_penalties(ball, robots)
        self.check_goals(ball, robots)

        # Bounds (Safe zone) check for ball
        self._rule_safe_lines(ball, self.RULE_SAFE_LINES_BAN)

        # Ball untouched
        if abs(ball.vx) < 0.1 and abs(ball.vy) < 0.1 and not ball.dragging:
            self.ball_untouched_timer += dt
        else:
            self.ball_untouched_timer = 0.0

        if self.ball_untouched_timer >= self.BALL_UNTOUCHED_LIMIT:
            self.ball_untouched_timer = 0.0
            assigned = {"blue": 0, "yellow": 0}
            for r in robots:
                if r.ban_timer <= 0 and assigned[r.team] < 2:
                    pos = self.neutral_positions[r.team][assigned[r.team]]
                    r.x, r.y = pos
                    assigned[r.team] += 1
            self.reset_ball(ball)

        # Missing team penalty
        for team in ["blue", "yellow"]:
            if total_counts[team] > 0 and active_counts[team] < total_counts[team]:
                self.missing_team_timer[team] += dt
                if self.missing_team_timer[team] >= 30.0:
                    self.missing_team_timer[team] = 0.0
                    other_team = "yellow" if team == "blue" else "blue"
                    self.score[other_team] += 1
            else:
                self.missing_team_timer[team] = 0.0
