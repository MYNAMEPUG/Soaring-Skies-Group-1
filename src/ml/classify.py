import time
import os
import subprocess
import sys
import asyncio


from utils.logger import log_message
from utils.survey import get_centroid, is_point_in_airdrop

"""
0: person
1: car
2: motorcycle
3: airplane
4: bus
5: boat
6: stop sign
7: umbrella
8: suitcase
9: skis
10: snowboard
11: sports ball
12: baseball bat
13: tennis racket
14: bed
"""


def read_imaging_results(config: Config, idx: int) -> GPSData:
    log_message(f"Getting imaging result {idx}")
    if not (0 <= idx < len(config.target_objects)):
        return get_centroid(config)

    result_path = os.path.join(config.odlc_save_dir, "targets.txt")
    results: dict[str, GPSData] = dict()
    target_positions: list[GPSData | None] = [None for _ in config.target_objects]

    if os.path.isfile(result_path):
        with open(result_path, "r") as f:
            for i, line in enumerate(f):
                [lat, lon, name] = line.split()  # lat lon name
                lat, lon = float(lat), float(lon)
                # results[name] = GPSData(
                #     {"lat": lat, "lon": lon, "alt": config.airdrop_alt, "hdg": 0}
                # )
                if i < len(target_positions):
                    target_positions[i] = GPSData(
                        {"lat": lat, "lon": lon, "alt": config.airdrop_alt, "hdg": 0}
                    )

    # for i, name in enumerate(config.target_objects):
    #     target_positions[i] = results.get(name)
    log_message(f"Objects {config.target_objects} found at {target_positions}")

    for i, point in enumerate(target_positions):
        if point is None or not is_point_in_airdrop(config, point):
            log_message(f"Target position {i} not valid. Setting to centroid")
            target_positions[i] = get_centroid(config)

    return target_positions[idx]


async def imaging_and_mapping(config: Config):
    log_message("Invoking imaging script")
    script_path = os.path.join("src", "ml", "utils", "read_images.py")

    try:
        log_message("Setting PYTHONPATH")
        env = os.environ.copy()
        env.setdefault("PYTHONPATH", os.pathsep.join(p for p in sys.path if p))

        log_message("Invoking subprocess")

        proc = subprocess.Popen(
            [
                sys.executable,
                script_path,
                # args
                config.image_save_dir,
                config.odlc_save_dir,
            ],
            env=env,
        )

        time_start = time.time()
        while True:
            log_message("Polling imaging script")
            if a := proc.poll() is not None:
                print(f"Exited with code {a}")
                break
            await asyncio.sleep(1)

        duration = time.time() - time_start
        log_message(f"Imaging completed in {duration} seconds")
    except Exception as e:
        print(e)