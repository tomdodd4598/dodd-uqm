def get_data(name):
    return f'../assets/data/{name}.txt'


def get_ship(name, space):
    return f'../assets/images/ships/{name}/{space.name}.png'


def get_background_star(name, space):
    return f'../assets/images/{space}/background/star-{name}.png'


def get_truespace_background_star(name):
    return get_background_star(name, 'truespace')


def get_hyperspace_background_star(name):
    return get_background_star(name, 'hyperspace')


def get_quasispace_background_star(name):
    return get_background_star(name, 'quasispace')


def get_truespace_star(color):
    return f'../assets/images/truespace/stars/{color}.png'


def get_hyperspace_star(color, size):
    return f'../assets/images/hyperspace/stars/{color}-{size}.png'


def get_planet(name, orbit):
    file = f'gas-giant-{hash(orbit) % 9}' if name == 'Gas Giant' else name.lower()
    return f'../assets/images/truespace/planets/{file}.png'


def get_hyperspace_hole():
    return '../assets/images/hyperspace/hole.png'


def get_hyperspace_ship_hole():
    return '../assets/images/hyperspace/hole-ship.png'


def get_hyperspace_quasi_hole():
    return '../assets/images/hyperspace/hole-quasi.png'


def get_quasispace_hole():
    return '../assets/images/quasispace/hole.png'
