import pygame as pg


key_number_map = {
    pg.K_0: 0,
    pg.K_1: 1,
    pg.K_2: 2,
    pg.K_3: 3,
    pg.K_4: 4,
    pg.K_5: 5,
    pg.K_6: 6,
    pg.K_7: 7,
    pg.K_8: 8,
    pg.K_9: 9,
    pg.K_KP_0: 0,
    pg.K_KP_1: 1,
    pg.K_KP_2: 2,
    pg.K_KP_3: 3,
    pg.K_KP_4: 4,
    pg.K_KP_5: 5,
    pg.K_KP_6: 6,
    pg.K_KP_7: 7,
    pg.K_KP_8: 8,
    pg.K_KP_9: 9,
}


def equals_number(key, number):
    return key_number_map.get(key) == number


def contains_up(keys):
    return keys[pg.K_UP] or keys[pg.K_w]


def contains_left(keys):
    return keys[pg.K_LEFT] or keys[pg.K_a]


def contains_down(keys):
    return keys[pg.K_DOWN] or keys[pg.K_s]


def contains_right(keys):
    return keys[pg.K_RIGHT] or keys[pg.K_d]


def contains_shift(keys):
    return keys[pg.K_RSHIFT] or keys[pg.K_LSHIFT]


def contains_ctrl(keys):
    return keys[pg.K_RCTRL] or keys[pg.K_LCTRL]


def contains_space(keys):
    return keys[pg.K_SPACE]


def contains_end(keys):
    return keys[pg.K_END]


def contains_plus(keys):
    return keys[pg.K_PLUS] or keys[pg.K_KP_PLUS]


def contains_minus(keys):
    return keys[pg.K_MINUS] or keys[pg.K_KP_MINUS]


number_key_map = {
    0: pg.K_0,
    1: pg.K_1,
    2: pg.K_2,
    3: pg.K_3,
    4: pg.K_4,
    5: pg.K_5,
    6: pg.K_6,
    7: pg.K_7,
    8: pg.K_8,
    9: pg.K_9,
}


number_keypad_map = {
    0: pg.K_KP_0,
    1: pg.K_KP_1,
    2: pg.K_KP_2,
    3: pg.K_KP_3,
    4: pg.K_KP_4,
    5: pg.K_KP_5,
    6: pg.K_KP_6,
    7: pg.K_KP_7,
    8: pg.K_KP_8,
    9: pg.K_KP_9,
}


def contains_number(keys, number):
    return keys[number_key_map[number]] or keys[number_keypad_map[number]]
