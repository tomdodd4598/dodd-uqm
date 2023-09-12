import hashlib
import math
import numba
import numpy as np
import os
import pickle
import pygame as pg

import constants
import game


class MinMax:
    def __init__(self):
        self.min = None
        self.max = None

    def update(self, value):
        if self.min is None or self.min > value:
            self.min = value
        if self.max is None or self.max < value:
            self.max = value


roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']

roman_numeral_map = {k + 1: v for k, v in enumerate(roman_numerals)}

roman_numeral_inv_map = {v: k + 1 for k, v in enumerate(roman_numerals)}


def to_letter(x):
    return chr(64 + x)


def quantity_dict(iterable):
    d = {}
    for x in iterable:
        if x in d:
            d[x] += 1
        else:
            d[x] = 1
    return d


def rotate(image, rect, angle, center=None):
    if angle != 0.0:
        image = pg.transform.rotate(image, -angle * constants.degs)
    rect = image.get_rect(center=rect.topleft if center is None else center)
    return image, rect


@numba.njit
def extended_mod(x, y, extension):
    return (x + extension) % (y + 2 * extension) - extension


@numba.njit
def extend_bounded(x, y, extension):
    return not x < -extension and not x > y + extension


@numba.njit
def coords_to_pos(coords):
    return 500.0 * np.array([coords[0], -coords[1]])


def solar_system_width_f(system):
    return _solar_system_f_internal(system, game.screen.display_width)


def solar_system_height_f(system):
    return _solar_system_f_internal(system, game.screen.display_height)


def _solar_system_f_internal(system, orbit_mult):
    return orbit_mult * solar_system_max_orbit_f(system) + \
           2.0 * _solar_system_planet_radius_f_internal(system.planet_radius_mm.max)


def solar_system_star_f(system):
    return _solar_system_star_f_internal(system.radius)


@numba.njit
def _solar_system_star_f_internal(star_radius):
    return 2.0 * star_radius ** constants.inv_3


def solar_system_orbit_f(system, planet):
    return _solar_system_orbit_f_internal(system.radius, planet.orbit)


def solar_system_max_orbit_f(system):
    return _solar_system_orbit_f_internal(system.radius, system.planet_orbit_mm.max)


def solar_system_minimap_f(system):
    return 1.0 / _solar_system_f_internal(system, 1.0)


@numba.njit
def _solar_system_orbit_f_internal(star_radius, planet_orbit):
    return 4.0 * star_radius ** 0.125 * planet_orbit ** constants.inv_3


def solar_system_planet_radius_f(planet):
    return _solar_system_planet_radius_f_internal(planet.radius)


@numba.njit
def _solar_system_planet_radius_f_internal(planet_radius):
    return (7.16 + planet_radius) / 43.92


def planetary_system_width_f(planet):
    return _planetary_system_f_internal(planet, game.screen.display_width)


def planetary_system_height_f(planet):
    return _planetary_system_f_internal(planet, game.screen.display_height)


def _planetary_system_f_internal(planet, orbit_mult):
    return orbit_mult * (_planetary_system_orbit_f_internal(planet.radius, planet.moon_orbit_mm.max) +
                         _planetary_system_moon_radius_f_internal(planet.radius, planet.moon_radius_mm.max))


def planetary_system_planet_f(planet):
    return _planetary_system_planet_f_internal(planet.radius)


@numba.njit
def _planetary_system_planet_f_internal(planet_radius):
    return (7.16 + planet_radius) / 32.94


def planetary_system_orbit_f(planet, moon):
    return _planetary_system_orbit_f_internal(planet.radius, moon.orbit)


@numba.njit
def _planetary_system_orbit_f_internal(planet_radius, moon_orbit):
    return 0.275 * _planetary_system_planet_f_internal(planet_radius) * math.sqrt(moon_orbit)


def planetary_system_moon_radius_f(planet, moon):
    return _planetary_system_moon_radius_f_internal(planet.radius, moon.radius)


@numba.njit
def _planetary_system_moon_radius_f_internal(planet_radius, moon_radius):
    return (7.16 + planet_radius) * (0.56 + moon_radius / planet_radius) / 72.0


@numba.njit
def temperature_color(temperature):
    celsius = temperature - 273.15
    if celsius < -150.0:
        return 0x00, 0x3f, 0xef
    elif celsius < -100.0:
        return 0x1f, 0x5f, 0xcf
    elif celsius < -50.0:
        return 0x3f, 0x7f, 0xaf
    elif celsius < 0.0:
        return 0x5f, 0x9f, 0x8f
    elif celsius < 75.0:
        return 0x5f, 0xbf, 0x5f
    elif celsius < 150.0:
        return 0xbf, 0x9f, 0x3f
    elif celsius < 225.0:
        return 0xdf, 0x1f, 0x1f
    elif celsius < 300.0:
        return 0xef, 0x3f, 0x1f
    else:
        return 0xff, 0x5f, 0x1f


@numba.njit
def clamped_lerp(a, b, x):
    if x <= 0.0:
        return a
    elif x >= 1.0:
        return b
    else:
        return (1.0 - x) * a + x * b


def each(seq, start):
    for i in range(start - len(seq), start):
        yield seq[i]


def positive_fmod(x, y):
    return np.fmod(np.fmod(x, y) + y, y)


def normalize(vector):
    norm = np.linalg.norm(vector)
    return vector if norm <= 0.0 else vector / norm


def is_text(s):
    return all('\x20' <= c <= '\x7E' or c == '\x09' or c == '\x0A' or c == '\x0D' for c in s)


def single_spaces(s, retain_start, retain_end):
    retain_start = s != s.lstrip() if retain_start else False
    retain_end = s != s.rstrip() if retain_end else False
    return retain_start * ' ' + ' '.join(s.split()) + retain_end * ' '


def auto_complete(s, targets):
    return os.path.commonprefix([x for x in targets if x.startswith(s)])


def contained_prefix(s, targets):
    substr = s
    while substr:
        if substr in targets:
            return substr
        substr = substr[:-1]
    return ''


def deterministic_hash(value):
    return int.from_bytes(hashlib.sha1(pickle.dumps(value)).digest(), byteorder='little', signed=False)
