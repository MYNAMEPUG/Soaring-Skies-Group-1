import math
import numpy as np

from helper.file_read import read_waypoints
from utils.logger import log_system,bcolors
from pymavlink.dialects.v20 import common
import asyncio
from utils.drone import Drone
import utils.mode as mode
from utils.takeoff import return_to_launch
from utils.mission import Mission
import time
from pymavlink import mavutil


def lerp(a: dict, b: dict, t: float) -> dict:
    """Linear interpolation between two GPS points"""
    return {
        "lat": float((1 - t) * a["lat"] + t * b["lat"]),
        "lon": float((1 - t) * a["lon"] + t * b["lon"]),
        "alt": float((1 - t) * a["alt"] + t * b["alt"]),
        "hdg": float((1 - t) * a["hdg"] + t * b["hdg"]),
    }


def cross(o: dict, a: dict, b: dict) -> float:
    """2D cross product of OA and OB vectors, i.e., z-component of (a - o) × (b - o)"""
    return (a["lon"] - o["lon"]) * (b["lat"] - o["lat"]) - (a["lat"] - o["lat"]) * (
            b["lon"] - o["lon"]
    )


def midpoint(a: dict, b: dict) -> dict:
    """Calculate midpoint between two GPS points"""
    return {
        "lat": (a["lat"] + b["lat"]) / 2,
        "lon": (a["lon"] + b["lon"]) / 2,
        "alt": (a["alt"] + b["alt"]) / 2,
        "hdg": (a["hdg"] + b["hdg"]) / 2,
    }


def get_centroid(airdrop_points: list) -> dict:
    """Calculate centroid of 4 airdrop points"""
    return {
        "lat": sum(p["lat"] for p in airdrop_points) / 4,
        "lon": sum(p["lon"] for p in airdrop_points) / 4,
        "alt": airdrop_points[0]["alt"],
        "hdg": 0,
    }


def sort_counter_clockwise(airdrop_points: list) -> list:
    """Sort points in counter-clockwise order around the centroid"""
    centroid = get_centroid(airdrop_points)
    return sorted(
        airdrop_points,
        key=lambda p: math.atan2(
            p["lon"] - centroid["lon"], p["lat"] - centroid["lat"]
        ),
    )


def is_point_in_airdrop(airdrop_points: list, point: dict) -> bool:
    """Check if point is inside convex quadrilateral defined by airdrop_points"""
    quad = sort_counter_clockwise(airdrop_points)

    for i in range(4):
        a = quad[i]
        b = quad[(i + 1) % 4]
        if cross(a, b, point) < 0:
            return False
    return True


def distance_meters(a: dict, b: dict) -> float:
    """Calculate distance in meters between two GPS points (Haversine formula)"""
    lat1, lon1 = math.radians(a["lat"]), math.radians(a["lon"])
    lat2, lon2 = math.radians(b["lat"]), math.radians(b["lon"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a_val = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a_val))

    return 6371000 * c  # Earth radius in meters


def get_longer_bisector(airdrop_points: list) -> tuple:
    """Get the longer bisector of the airdrop quadrilateral"""
    quad = sort_counter_clockwise(airdrop_points)
    a, b, c, d = quad

    bisector1 = (midpoint(a, b), midpoint(c, d))
    bisector2 = (midpoint(a, d), midpoint(b, c))

    length1 = distance_meters(bisector1[0], bisector1[1])
    length2 = distance_meters(bisector2[0], bisector2[1])

    if length1 > length2:
        return bisector1, length1
    else:
        return bisector2, length2


def generate_survey_waypoints(
        airdrop_points: list,
        survey_alt: float,
        camera_vfov_rad: float,
        overlap: float = 0.2
) -> list:
    """
    Generate survey waypoints for image capture

    Args:
        airdrop_points: List of 4 GPS dicts defining airdrop area
        survey_alt: Altitude to survey at (meters)
        camera_vfov_rad: Camera vertical field of view in radians
        overlap: Image overlap percentage (default 0.2 = 20%)

    Returns:
        List of GPS waypoints for surveying
    """
    (start, end), distance = get_longer_bisector(airdrop_points)

    pic_len = 2 * math.tan(camera_vfov_rad / 2) * survey_alt
    num_pictures = math.ceil(distance / pic_len / (1 - overlap)) + 1
    points = [lerp(start, end, t) for t in np.linspace(0, 1, num_pictures)]

    log_system(f"Generating {num_pictures} survey waypoints",msgname='SURVEY',color=bcolors.OKCYAN)

    for p in points:
        p["alt"] = survey_alt

    return points
class Survey:
    def __init__(self, drone: Drone, boundingWaypoints: str = None):
        self.drone = drone
        raw_points = read_waypoints(boundingWaypoints)
        self.custom_points = [{"lat": p[0], "lon": p[1], "alt": p[2], "hdg": 0} for p in raw_points]
        self.mission_handler = Mission(drone=drone, waypointsFile=boundingWaypoints)
    async def upload_mission(self, rtl: bool = True):
        waypoints = generate_survey_waypoints(self.custom_points, 10, 0.7854)
        home_pos = await self.drone.get_home_position_deg()
        waypoints_list = [[wp["lat"], wp["lon"], wp["alt"]] for wp in waypoints]
        waypoints_list.append([home_pos["lat"], home_pos["long"], home_pos["alt"]])
        await self.mission_handler.upload_mission(waypoints=waypoints_list, begin_immediately=False, rtl=rtl)
        await self.mission_handler.begin_mission(rtl=False)
        if rtl:
            await return_to_launch(self.drone)