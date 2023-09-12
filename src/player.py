import assets
import data

from engines import PlayerEngine
from ships import PlayerShip


class Player:
    def __init__(self):
        self.engine = PlayerEngine()
        self.pos = None
        self.vel = None
        self.angle = None
        self.ang_vel = None
        self.ship_name = None
        self.visited_systems = None

    def set_pos_vel(self, pos, vel, angle, ang_vel):
        self.pos = pos
        self.vel = vel
        self.angle = angle
        self.ang_vel = ang_vel

    def get_ship(self, scale, space):
        image = assets.get_ship(self.ship_name.lower(), space)
        ship_data = data.ships[self.ship_name]
        return PlayerShip(self, image, scale, self.pos, space, ship_data.mass, ship_data.moi, ship_data.area, self.vel, self.angle, self.ang_vel)
