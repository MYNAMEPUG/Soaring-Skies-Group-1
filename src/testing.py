import asyncio
from pymavlink.dialects.v20 import common

import test_motors
from utils.drone import Drone
from utils.logger import log_system
from utils.mission import Mission
from utils.takeoff import takeoff
from utils.geofence import Geofence
from helper.file_read import read_file

async def main():
    drone = Drone()
    drone.initialize_drone(parametersFile='files/settings.txt', configFile='files/config.txt')
    # await mission_picker(drone)
    # mission = Mission(drone=drone, waypointsFile='info_files/waypoints.txt')
    # fence = Geofence(drone=drone, geofenceFile='info_files/test_files/testingfence.txt')
    # coord = [-35.3628918, 149.1654175, 10]

    await asyncio.gather(
        drone.start_background_processes(),
        drone.watch_for_heartbeat(),
        # targetloc.begin_dummy_mission()
        test_motors.test_all_motors_multiple(drone=drone, num_times=3, throttle_step=5, throttle_value=20)
        # servo_test.full_spin_servo(drone, 1)
        #servo_test.servo_open_close(drone=drone, servo_value=800)
    )


if __name__ == "__main__":
    asyncio.run(main())
    # file_test()