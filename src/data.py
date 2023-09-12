import math

import numpy as np

import assets
import helpers
import spaces

from dataclasses import dataclass
from helpers import MinMax
from thrusters import Thruster
from typing import Any


@dataclass
class SystemData:
    name: str
    coords: np.ndarray
    color: str
    temperature: float
    size: str
    radius: float
    luminosity: float
    mass: float
    planets: list
    planet_orbit_mm: MinMax
    planet_radius_mm: MinMax


@dataclass
class PlanetData:
    name: str
    is_moon: bool
    number: int
    type_name: str
    surface: str
    orbit: float
    atmosphere: float
    temperature: float
    weather: int
    tectonics: int
    mass: float
    radius: float
    gravity: float
    day: float
    tilt: int
    fuel_use: float
    minerals: list
    lifeforms: list
    moons: list
    direction: int
    initial_angle: float
    moon_orbit_mm: MinMax
    moon_radius_mm: MinMax
    system: Any


@dataclass
class MineralDepositData:
    name: str
    quality: int
    latitude: int
    longitude: int


@dataclass
class LifeformInstanceData:
    name: str


def parse_planet_data(data, system_name, is_moon):
    parts = data.split('::' if is_moon else '??')
    number = int(parts[0])
    suffix = f'-{helpers.to_letter(number)}' if is_moon else f' {helpers.roman_numeral_map[number]}'
    name = f'{system_name}{suffix}'
    type_name = parts[1]
    surface = parts[2]
    orbit = float(parts[3])
    atmosphere = float(parts[4])
    temperature = float(parts[5])
    weather = int(parts[6])
    tectonics = int(parts[7])
    mass = float(parts[8])
    radius = float(parts[9])
    gravity = float(parts[10])
    day = float(parts[11])
    tilt = int(parts[12])
    fuel_use = float(parts[13])
    minerals = []
    mineral_data = parts[14]
    if mineral_data:
        for part in mineral_data.split(';;'):
            info = part.split(',')
            mineral_name = info[0]
            quality = int(info[1])
            latitude = int(info[2])
            longitude = int(info[3])
            minerals.append(MineralDepositData(mineral_name, quality, latitude, longitude))
    lifeforms = []
    lifeform_data = parts[15]
    if lifeform_data:
        for part in lifeform_data.split(';;'):
            lifeforms.append(LifeformInstanceData(part))
    moon_data = parts[16]
    moons = []
    moon_orbit_mm = MinMax()
    moon_radius_mm = MinMax()
    if not is_moon:
        moon_orbit_mm.update(15.0 * radius ** 0.125)
        moon_radius_mm.update(0.08 * radius)
        if moon_data:
            for part in moon_data.split('^^'):
                moon = parse_planet_data(part, name, True)
                moons.append(moon)
                moon_orbit_mm.update(moon.orbit)
                moon_radius_mm.update(moon.radius)
    direction = int(parts[17])
    initial_angle = float(parts[18])

    return PlanetData(
        name,
        is_moon,
        number,
        type_name,
        surface,
        orbit,
        atmosphere,
        temperature,
        weather,
        tectonics,
        mass,
        radius,
        gravity,
        day,
        tilt,
        fuel_use,
        minerals,
        lifeforms,
        moons,
        direction,
        initial_angle,
        moon_orbit_mm,
        moon_radius_mm,
        None,
    )


systems = {}
system_search_names: set


def load_systems():
    def add_system(parts):
        name = parts[0]
        coords = np.array([float(parts[1]), float(parts[2])])
        color = parts[3]
        temperature = float(parts[4])
        size = parts[5]
        radius = float(parts[6])
        luminosity = float(parts[7])
        mass = float(parts[8])
        planet_data = parts[9]
        planets = []
        planet_orbit_mm = MinMax()
        planet_radius_mm = MinMax()
        planet_orbit_mm.update(0.025 * math.sqrt(radius))
        planet_radius_mm.update(0.16)
        if planet_data:
            for data in planet_data.split('||'):
                planet = parse_planet_data(data, name, False)
                planets.append(planet)
                planet_orbit_mm.update(planet.orbit)
                planet_radius_mm.update(planet.radius)

        systems[name] = SystemData(
            name,
            coords,
            color,
            temperature,
            size,
            radius,
            luminosity,
            mass,
            planets,
            planet_orbit_mm,
            planet_radius_mm,
        )

    with open(assets.get_data('systems')) as file:
        lines = file.readlines()
        for line in lines:
            line = line.rstrip()
            if len(line) > 0:
                add_system(line.split('&&'))

    for s in systems.values():
        for p in s.planets:
            p.system = s
            for m in p.moons:
                m.system = p

    global system_search_names
    system_search_names = {x.upper() for x in systems.keys()}


@dataclass
class RaceData:
    name: str
    side: str
    ship_name: str
    soi_pos: np.ndarray
    soi_radius: float

    def is_ally(self):
        return self.side == 'Ally'

    def get_ship_image(self, space):
        if space == spaces.hyperspace and not self.is_ally():
            return assets.get_hyperspace_ship_hole()
        else:
            return assets.get_ship(self.ship_name, space)


races = {}
race_list: list


def load_races():
    def add_race(parts):
        race_name = parts[0]
        side = parts[1]
        ship = parts[2]
        soi_pos = helpers.coords_to_pos((float(parts[3]), float(parts[4])))
        soi_radius = 500.0 * float(parts[5])

        races[race_name] = RaceData(race_name, side, ship, soi_pos, soi_radius)

    with open(assets.get_data('races')) as file:
        lines = file.readlines()
        for line in lines:
            line = line.rstrip()
            if len(line) > 0:
                add_race(line.split('&&'))

    global race_list
    race_list = [x for x in races.values()]


@dataclass
class ShipData:
    name: str
    captains: int
    first_officers: int
    helm_officers: int
    weapons_officers: int
    medical_officers: int
    security_officers: int
    xenotech_experts: int
    systems_engineers: int
    maintenance_engineers: int
    mass: float
    moi: float
    area: float
    thrust: float
    ang_thrust: float
    battery: float
    battery_regen: float


ships = {}


def load_ships():
    def add_ship(parts):
        ship_name = parts[0]
        args = [ship_name]
        args.extend(int(part) for part in parts[1].split('??'))
        args.extend(float(part) for part in parts[2:9])

        ships[ship_name] = ShipData(*tuple(args))

    with open(assets.get_data('ships')) as file:
        lines = file.readlines()
        for line in lines:
            line = line.rstrip()
            if len(line) > 0:
                add_ship(line.split('&&'))


thrusters = {}


def load_thrusters():
    def add_thruster(parts):
        thruster_name = parts[0]
        args = [thruster_name]
        args.extend(float(part) for part in parts[1:5])

        thrusters[thruster_name] = Thruster(*tuple(args))

    with open(assets.get_data('thrusters')) as file:
        lines = file.readlines()
        for line in lines:
            line = line.rstrip()
            if len(line) > 0:
                add_thruster(line.split('&&'))


def load_dynamos():
    pass


def load():
    load_systems()
    load_races()
    load_ships()
    load_thrusters()
    load_dynamos()
