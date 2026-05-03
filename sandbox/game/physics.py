import math
import pygame

class PhysicsEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def apply_kinematics(self, robots):
        for r in robots:
            if r.ban_timer > 0:
                continue

            if r.context:
                v_turn = r.context.motors.v_turn
                v_fwd = r.context.motors.v_forward
                v_lat = r.context.motors.v_lateral
            else:
                v_turn = v_fwd = v_lat = 0.0

            f_x = math.cos(r.rangle)
            f_y = math.sin(r.rangle)
            r_x = -f_y
            r_y = f_x
            
            r.rangle += v_turn
            r._last_x = r.x
            r._last_y = r.y
            r.x += (f_x * v_fwd) + (r_x * v_lat)
            r.y += (f_y * v_fwd) + (r_y * v_lat)
            
            r.x = max(r.radius, min(self.width - r.radius, r.x))
            r.y = max(r.radius, min(self.height - r.radius, r.y))

    def update_ball(self, ball):
        mx, my = pygame.mouse.get_pos()
        mb1, _, _ = pygame.mouse.get_pressed()

        if mb1:
            dist_to_mouse = math.hypot(mx - ball.x, my - ball.y)
            if dist_to_mouse < 30 or ball.dragging:
                ball.dragging = True
                ball.x, ball.y = mx, my
                ball.vx = 0
                ball.vy = 0
                ball.last_kicked_by = None
        else:
            ball.dragging = False

        if not ball.dragging:
            ball.x += ball.vx
            ball.y += ball.vy
            ball.vx *= 0.90
            ball.vy *= 0.90
            
            # Rebotes en paredes del campo
            if ball.x < ball.radius: ball.x = ball.radius; ball.vx *= -0.8
            if ball.x > self.width - ball.radius: ball.x = self.width - ball.radius; ball.vx *= -0.8
            if ball.y < ball.radius: ball.y = ball.radius; ball.vy *= -0.8
            if ball.y > self.height - ball.radius: ball.y = self.height - ball.radius; ball.vy *= -0.8

    def resolve_collisions(self, ball, robots, goals):
        # Robot-Goal walls
        for r in robots:
            if r.ban_timer > 0: continue
            for g in goals:
                for wall in g.get_walls(thickness=4):
                    closest_x = max(wall.left, min(r.x, wall.right))
                    closest_y = max(wall.top, min(r.y, wall.bottom))
                    dx, dy = r.x - closest_x, r.y - closest_y
                    dist = math.hypot(dx, dy)
                    if 0 < dist < r.radius:
                        overlap = r.radius - dist
                        nx, ny = dx/dist, dy/dist
                        r.x += nx * overlap
                        r.y += ny * overlap

        # Ball-Goal walls
        if not ball.dragging:
            for g in goals:
                for wall in g.get_walls(thickness=4):
                    closest_x = max(wall.left, min(ball.x, wall.right))
                    closest_y = max(wall.top, min(ball.y, wall.bottom))
                    dx, dy = ball.x - closest_x, ball.y - closest_y
                    dist = math.hypot(dx, dy)
                    if 0 < dist < ball.radius:
                        overlap = ball.radius - dist
                        nx, ny = dx/dist, dy/dist
                        ball.x += nx * overlap
                        ball.y += ny * overlap
                        dot = ball.vx * nx + ball.vy * ny
                        if dot < 0:
                            ball.vx -= 1.6 * dot * nx
                            ball.vy -= 1.6 * dot * ny

        # Robot-Robot
        for i in range(len(robots)):
            r1 = robots[i]
            if r1.ban_timer > 0: continue
            for j in range(i + 1, len(robots)):
                r2 = robots[j]
                if r2.ban_timer > 0: continue
                
                dx, dy = r2.x - r1.x, r2.y - r1.y
                dist = math.hypot(dx, dy)
                if 0 < dist < r1.radius + r2.radius:
                    overlap = (r1.radius + r2.radius - dist) / 2
                    nx, ny = dx / dist, dy / dist
                    r1.x -= nx * overlap; r1.y -= ny * overlap
                    r2.x += nx * overlap; r2.y += ny * overlap

        # Robot-Ball
        for r in robots:
            if r.ban_timer > 0: continue
            dr_x = ball.x - r.x
            dr_y = ball.y - r.y
            dist_rb = math.hypot(dr_x, dr_y)
            sum_radios = r.radius + ball.radius
            
            if 0 < dist_rb < sum_radios:
                overlap = sum_radios - dist_rb
                nx, ny = dr_x / dist_rb, dr_y / dist_rb
                
                if not ball.dragging:
                    ball.last_kicked_by = r
                    ball.x += nx * overlap
                    ball.y += ny * overlap
                    
                    robot_vx = r.x - getattr(r, '_last_x', r.x)
                    robot_vy = r.y - getattr(r, '_last_y', r.y)
                    
                    rel_vx = ball.vx - robot_vx
                    rel_vy = ball.vy - robot_vy
                    vel_along_normal = rel_vx * nx + rel_vy * ny
                    
                    if vel_along_normal < 0:
                        restitution = 0.8
                        impulse = -(1 + restitution) * vel_along_normal
                        ball.vx += impulse * nx
                        ball.vy += impulse * ny
                    else:
                        ball.vx += nx * 0.5
                        ball.vy += ny * 0.5
                else:
                    r.x -= nx * overlap
                    r.y -= ny * overlap

    def step(self, dt, ball, robots, goals):
        self.apply_kinematics(robots)
        self.update_ball(ball)
        self.resolve_collisions(ball, robots, goals)
