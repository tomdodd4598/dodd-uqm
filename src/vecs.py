import numba
import numpy as np


@numba.njit
def normalize(vec):
    norm = np.linalg.norm(vec)
    return vec if norm == 0.0 else vec / norm


@numba.njit
def norm_tuple(vec):
    norm = np.linalg.norm(vec)
    return (vec if norm == 0.0 else vec / norm), norm


@numba.njit
def rotate(vec, angle):
    x, y = vec[0], vec[1]
    cos, sin = np.cos(angle), np.sin(angle)
    return np.array([x * cos - y * sin, x * sin + y * cos])
