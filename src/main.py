import asyncio

from utils.circuittimetrial import CircuitTimeTrial
from utils.drone import Drone
from utils.logger import log_system
from utils.mission import Mission
from utils.takeoff import takeoff
from utils.geofence import Geofence
from utils.survey import Survey
from helper.file_read import read_config_file
from test_motors import test_all_motors_multiple


async def main():
    drone = Drone()
    drone.initialize_drone(parametersFile='files/settings.txt', configFile='files/config.txt')
    # mission = Mission(drone=drone, waypointsFile='files/waypoints.txt')
    fence = Geofence(drone=drone, geofenceFile='files/fence.txt')

    await asyncio.gather(
        drone.start_background_processes(),
        drone.watch_for_heartbeat(),
        fence.upload_fence(),
        mission_picker(drone)
    )


async def mission_picker(drone: Drone):
    '''Gets the missions needed to be executed via the config.txt file and executes them one after another. Supports multiple missions seperated by commans
    in the config.txt file'''
    await drone.message_stream_exists(
        msgname="Mission Picker",
        msg="Waiting for message stream before starting missions"
    )

    # Wait for home position to be set
    log_system(msgname="Mission Picker", msg="Waiting for home position...")
    while not drone.home_position['set']:
        await asyncio.sleep(0.5)
    log_system(msgname="Mission Picker", msg=f"Home position ready: {drone.home_position}")

    # Extra buffer for EKF and fence upload to settle
    await asyncio.sleep(5)

    config = drone.get_configuration()
    mission_config: str = config['mission']
    missions = []
    while True:
        if mission_config.__contains__(","):
            m = int(mission_config[0:mission_config.index(",")])
            missions.append(m)
            mission_config = mission_config[mission_config.index(",") + 1:]
        else:
            missions.append(int(mission_config))
            break

    circuitTimeTrial = CircuitTimeTrial(drone, 'files/waypoints.txt')
    await circuitTimeTrial.upload_mission(rtl=True)
    #machine_learning = Survey(drone, 'files/waypoints.txt')
    #await machine_learning.upload_mission(rtl=True)
if __name__ == "__main__":
    asyncio.run(main())
