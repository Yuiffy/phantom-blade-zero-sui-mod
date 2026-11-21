"""Rasterize atlas triangles and measure their occupied texels."""

import cv2
import numpy as np


def raster_surface(uv, triangles, points, shape):
    """Return one rest-space position per covered pixel center."""
    height, width = shape
    index = np.full(shape, -1, np.int32)
    position = np.zeros((*shape, 3), np.float32)
    for i, corners in enumerate(uv):
        a, b = corners[1:] - corners[0]
        det = np.cross(np.r_[a, 0], np.r_[b, 0])[2]
        if abs(det) < 1e-7:
            continue
        left, top = np.maximum(0, np.ceil(corners.min(axis=0)).astype(int))
        right, bottom = np.minimum([width - 1, height - 1], np.floor(corners.max(axis=0)).astype(int))
        x, y = np.meshgrid(np.arange(left, right + 1), np.arange(top, bottom + 1))
        dx, dy = x - corners[0, 0], y - corners[0, 1]
        u = (dx * b[1] - dy * b[0]) / det
        v = (a[0] * dy - a[1] * dx) / det
        inside = (u >= -1e-7) & (v >= -1e-7) & (u + v <= 1.0000001)
        px, py = x[inside], y[inside]
        if len(px):
            position[py, px] = np.column_stack((1 - u[inside] - v[inside], u[inside], v[inside])) @ points[triangles[i]]
            index[py, px] = i
    return index, position


def uv_footprint(uv, shape):
    mask = np.zeros(shape, np.uint8)
    for corners in uv:
        cv2.fillConvexPoly(mask, np.rint(corners * 16).astype(np.int32), 1, shift=4)
    return mask.astype(bool)
