import numpy as np

import constants
import game
import helpers
import vecs


class Engine:
    def __init__(self, forward_thrust, retro_thrust, side_thrust, ang_thrust, damp_factor, ang_damp_factor):
        self.forward_thrust = forward_thrust
        self.retro_thrust = retro_thrust
        self.side_thrust = side_thrust
        self.ang_thrust = ang_thrust
        self.damp_factor = damp_factor
        self.ang_damp_factor = ang_damp_factor

        self.forward_damping = None
        self.retro_damping = None
        self.side_damping = None
        self.ang_damping = None
        self.set_damping()

    def set_damping(self):
        self.forward_damping = self.damp_factor * self.forward_thrust
        self.retro_damping = self.damp_factor * self.retro_thrust
        self.side_damping = self.damp_factor * self.side_thrust
        self.ang_damping = self.damp_factor * self.ang_thrust

    def update_ship(self, ship, space, lat_mult, long_mult, modifier1, modifier2, dt):
        sideways = modifier1 and self.side_thrust > 0.0
        max_friction_mult = ship.mass / dt
        max_ang_friction_mult = ship.moi / dt

        sqrt_area = np.sqrt(ship.area)
        vel_dir, speed = vecs.norm_tuple(ship.vel)
        friction = (space.lin_mu1 * sqrt_area + space.lin_mu2 * ship.area * speed) * speed
        max_friction = 0.5 * max_friction_mult * speed
        if friction > max_friction:
            friction = max_friction
        perp_dir = np.array([-ship.dir[1], ship.dir[0]])
        lat_thrust = np.zeros(2) if not sideways else lat_mult * self.side_thrust * perp_dir
        long_thrust = long_mult * (self.forward_thrust if long_mult > 0.0 else self.retro_thrust)
        acc = (lat_thrust + long_thrust * ship.dir - friction * vel_dir) / ship.mass

        ship.vel += dt * acc

        area_3_2 = sqrt_area * ship.area
        ang_speed, ang_vel_sign = abs(ship.ang_vel), 1.0 if ship.ang_vel > 0.0 else -1.0
        ang_friction = (space.rot_mu1 * area_3_2 + space.rot_mu2 * area_3_2 * ship.area * ang_speed) * ang_speed
        max_ang_friction = 0.5 * max_ang_friction_mult * ang_speed
        if ang_friction > max_ang_friction:
            ang_friction = max_ang_friction
        ang_thrust = 0.0 if sideways else lat_mult * self.ang_thrust
        ang_acc = (ang_thrust - ang_vel_sign * ang_friction) / ship.moi

        ship.ang_vel += dt * ang_acc

        if modifier2:
            if self.damp_factor > 0.0:
                vel_dir, speed = vecs.norm_tuple(ship.vel)
                cos = np.dot(ship.dir, vel_dir)
                damping = self.retro_damping if cos > 0.0 else self.forward_damping
                sin_sq = 1.0 - cos * cos
                damping += (np.sqrt(sin_sq) if sin_sq > 0.0 else 0.0) * self.side_damping
                if damping > max_friction_mult * speed:
                    ship.vel = np.zeros(2)
                else:
                    ship.vel -= dt * damping / ship.mass * vel_dir

            if self.ang_damp_factor > 0.0:
                ang_speed, ang_vel_sign = abs(ship.ang_vel), 1.0 if ship.ang_vel > 0.0 else -1.0
                ang_damping = self.ang_damping
                if ang_damping > max_ang_friction_mult * ang_speed:
                    ship.ang_vel = 0.0
                else:
                    ship.ang_vel -= dt * ang_vel_sign * ang_damping / ship.moi

        ship.pos += ship.scale * dt * ship.vel
        ship.angle += dt * ship.ang_vel
        ship.angle = helpers.positive_fmod(ship.angle, constants.two_pi)


class PlayerEngine(Engine):
    def __init__(self):
        super().__init__(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.thrusters = []

    def set_thrusters(self, thrusters):
        self.thrusters = thrusters
        self.update_stats()

    def set_damp_factors(self, damp_factor, ang_damp_factor):
        self.damp_factor = damp_factor
        self.ang_damp_factor = ang_damp_factor
        self.set_damping()

    def update_stats(self):
        self.forward_thrust = 0.0
        self.retro_thrust = 0.0
        self.side_thrust = 0.0
        self.ang_thrust = 0.0

        for thruster in self.thrusters:
            self.forward_thrust += thruster.forward_thrust
            self.retro_thrust += thruster.retro_thrust
            self.side_thrust += thruster.side_thrust
            self.ang_thrust += thruster.ang_thrust

        self.set_damping()

    def update_ship(self, ship, space, lat_mult, long_mult, modifier1, modifier2, dt):
        super().update_ship(ship, space, lat_mult, long_mult, modifier1, modifier2, dt)
        game.instance.player.set_pos_vel(ship.pos, ship.vel, ship.angle, ship.ang_vel)


class NPCEngine(Engine):
    def __init__(self, forward_thrust, retro_thrust, side_thrust, ang_thrust, damp_factor, ang_damp_factor):
        super().__init__(forward_thrust, retro_thrust, side_thrust, ang_thrust, damp_factor, ang_damp_factor)
