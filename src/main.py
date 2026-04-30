import asyncio

from src.utils.drone import Drone
from src.utils.logger import log_system
from src.utils.mission import Mission
from src.utils.takeoff import takeoff
from src.utils.geofence import Geofence

from src.helper.file_read import read_config_file



async def main():
    drone = Drone()
    drone.initialize_drone(parametersFile='info_files/settings.txt', configFile='info_files/config.txt')
    # mission = Mission(drone=drone, waypointsFile='info_files/waypoints.txt')
    fence = Geofence(drone=drone, geofenceFile='info_files/test_files/testingfence.txt')

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

    print(f'MISSIONS = {missions}')
    mission_list = {
        0: "NO MISSION",
        1: "WAYPOINT NAVIGATION",
        2: "CIRCUIT TIME TRIAL",
    }

    mission_files = read_config_file('info_files/mission_files.txt')

    while missions.__len__() != 0:
        current_mission = missions[0]
        print(f"starting mission {mission_list[current_mission]}")
        missions.remove(current_mission)
        read_file = mission_files[f'{current_mission}']

        mission_rtl = True if missions.__len__() == 0 else False  # if the # of missions remaining is zero, then we return to launch

        match current_mission:
            case 0:
                pass
            case 1:
                waypointNav = WaypointNavigation(drone, read_file)
                await waypointNav.upload_mission(rtl=mission_rtl)
            case 2:
                circuitTimeTrial = CircuitTimeTrial(drone, read_file)
                await circuitTimeTrial.upload_mission(rtl=mission_rtl)
