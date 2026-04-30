import math

import numpy as np

from utils.config import Config
from utils.distance import GPSData, distance_meters
from src.utils.logger import log_message


def lerp(a: GPSData, b: GPSData, t: float):
    return GPSData(
        {
            "lat": float((1 - t) * a["lat"] + t * b["lat"]),
            "lon": float((1 - t) * a["lon"] + t * b["lon"]),
            "alt": float((1 - t) * a["alt"] + t * b["alt"]),
            "hdg": float((1 - t) * a["hdg"] + t * b["hdg"]),
        }
    )


def cross(o: GPSData, a: GPSData, b: GPSData) -> float:
    """2D cross product of OA and OB vectors, i.e., z-component of (a - o) × (b - o)"""
    return (a["lon"] - o["lon"]) * (b["lat"] - o["lat"]) - (a["lat"] - o["lat"]) * (
        b["lon"] - o["lon"]
    )


def midpoint(a: GPSData, b: GPSData) -> GPSData:
    return GPSData(
        {
            "lat": (a["lat"] + b["lat"]) / 2,
            "lon": (a["lon"] + b["lon"]) / 2,
            "alt": (a["alt"] + b["alt"]) / 2,
            "hdg": (a["hdg"] + b["hdg"]) / 2,
        }
    )


def get_centroid(config: Config):
    return GPSData(
        {
            "lat": sum(p["lat"] for p in config.airdrop) / 4,
            "lon": sum(p["lon"] for p in config.airdrop) / 4,
            "alt": config.airdrop_alt,
            "hdg": 0,
        }
    )


def sort_counter_clockwise(config: Config):
    """Sort points in counter-clockwise order around the centroid"""
    centroid = get_centroid(config)
    return sorted(
        config.airdrop,
        key=lambda p: math.atan2(
            p["lon"] - centroid["lon"], p["lat"] - centroid["lat"]
        ),
    )


def is_point_in_airdrop(config: Config, point: GPSData) -> bool:
    """Check if point is inside convex quadrilateral defined by quad"""
    quad = sort_counter_clockwise(config)

    for i in range(4):
        a = quad[i]
        b = quad[(i + 1) % 4]
        if cross(a, b, point) < 0:
            return False
    return True


def get_longer_bisector(config: Config):
    [a, b, c, d] = sort_counter_clockwise(config)

    bisector1 = (midpoint(a, b), midpoint(c, d))
    bisector2 = (midpoint(a, d), midpoint(b, c))

    length1 = distance_meters(*bisector1)
    length2 = distance_meters(*bisector2)

    if length1 > length2:
        return bisector1, length1
    else:
        return bisector2, length2


def generate_survey_waypoints(config: Config):
    (start, end), distance = get_longer_bisector(config)

    pic_len = 2 * math.tan(config.cam_vfov_rad / 2) * config.survey_alt
    overlap = 0.2  # 20% overlap
    num_pictures = math.ceil(distance / pic_len / (1 - overlap)) + 1
    points = [lerp(start, end, t) for t in np.linspace(0, 1, num_pictures)]
    log_message(f"Surveying at points {points}")

    for p in points:
        p["alt"] = config.survey_alt

    return points