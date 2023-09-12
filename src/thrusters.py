class Thruster:
    def __init__(self, name, forward, retro, side, ang):
        self.name = name
        self.forward_thrust = forward
        self.retro_thrust = retro
        self.side_thrust = side
        # self.damp_thrust = damp
        self.ang_thrust = ang
        # self.ang_damp_thrust = ang_damp
