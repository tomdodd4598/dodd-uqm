class Space:
    def __init__(self, name, color, lin_mu1, lin_mu2, rot_mu1, rot_mu2):
        self.name = name
        self.color = color
        self.lin_mu1 = lin_mu1
        self.lin_mu2 = lin_mu2
        self.rot_mu1 = rot_mu1
        self.rot_mu2 = rot_mu2


truespace = Space('truespace', (0, 0, 0), 0.0, 0.1, 0.0, 0.04)
hyperspace = Space('hyperspace', (63, 15, 15), 40.0, 0.5, 1200.0, 0.2)
quasispace = Space('quasispace', (0, 208, 0), 80.0, 0.01, 2400.0, 0.1)
