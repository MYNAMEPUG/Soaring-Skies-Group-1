import asyncio
from pymavlink.dialects.v20 import common

from utils.drone import Drone
import utils.mode as mode
from utils.logger import log_system, log_success,bcolors


async def arm_drone(drone: Drone, force: bool=False):
    await drone.send_command(command=common.MAV_CMD_COMPONENT_ARM_DISARM, param1=1,
                             param2=(21196 if force else 0))


async def disarm_drone(drone: Drone, force: bool = False):
    await drone.send_command(command=common.MAV_CMD_COMPONENT_ARM_DISARM, param1=0,
                             param2=(21196 if force else 0))


async def wait_for_gps_fix(drone: Drone, msgname="Takeoff Handler"):
    log_system(msgname=msgname, msg="Waiting for GPS fix...")
    while True:
        msg = await drone.get_message_stream().request_message(
            common.MAVLINK_MSG_ID_GPS_RAW_INT
        )
        if msg.fix_type >= 3 and msg.eph < 200:
            log_system(msgname=msgname, msg=f"GPS ready (type={msg.fix_type})", color=bcolors.SUCCESS)
            return
        log_system(msgname=msgname, msg=f"Waiting... fix_type={msg.fix_type} eph={msg.eph}")
        await asyncio.sleep(1)


async def arm_with_retry(drone: Drone, msgname="Takeoff Handler", max_attempts=20):
    """Retries arming until accepted or max_attempts reached"""
    for attempt in range(1, max_attempts + 1):
        log_system(msgname=msgname, msg=f"Arming attempt {attempt}/{max_attempts}...")
        ack = await drone.send_command(command=common.MAV_CMD_COMPONENT_ARM_DISARM, param1=1, param2=0)
        if ack and ack.result == common.MAV_RESULT_ACCEPTED:
            log_success(msgname=msgname, msg="Armed successfully")
            return True
        log_system(msgname=msgname, msg=f"Arm rejected (result={ack.result if ack else 'no ack'}) — retrying in 2s", color=bcolors.YELLOW)
        await asyncio.sleep(2)
    log_system(msgname=msgname, msg="Failed to arm after max attempts", color=bcolors.FAIL)
    return False


async def takeoff(drone: Drone, target_alt=None, lat=None, long=None):
    if not target_alt:
        target_alt = drone.target_alt
    if not (lat and long):
        pos = await drone.get_position_deg()
        lat = pos["lat"]
        long = pos["long"]
    await wait_for_gps_fix(drone, msgname="Takeoff Handler")
    await mode.set_mode(drone=drone, mode=mode.GUIDED)
    armed = await arm_with_retry(drone, msgname="Takeoff Handler")
    if not armed:
        return
    await drone.send_command(command=common.MAV_CMD_NAV_TAKEOFF, param5=lat, param6=long, param7=target_alt)
    await wait_for_altitude_increase(drone, target_alt, msgname="Takeoff Handler")

async def return_to_launch(drone: Drone):
    """Sets drone mode to RTL, making the drone return to its home position"""
    await mode.set_mode(drone=drone, mode=mode.RTL)
    home_pos = await drone.get_home_position_deg()
    await wait_for_altitude_decrease(drone, home_pos['alt'], msgname="RTL Handler")
    await mode.set_mode(drone=drone, mode=mode.STABILIZE)
    await disarm_drone(drone)


async def wait_for_altitude_increase(drone: Drone, target_alt, msgname="Increasing Altitude"):
    while True:
        current_pos = await drone.get_position_deg()
        if current_pos['alt'] > (1 - drone.threshholdZ) * target_alt:
            log_success(msgname=msgname, msg="Climb to target altitude complete!")
            return
        log_system(msg=f"Current Altitude: {current_pos['alt']} | Target Altitude: {target_alt}", msgname=msgname)
        await asyncio.sleep(1)


async def wait_for_altitude_decrease(drone: Drone, target_alt, msgname="Decreasing Altitude"):
    while True:
        current_pos = await drone.get_position_deg()
        if current_pos['alt'] < (1 + drone.threshholdZ) * target_alt:
            log_success(msgname=msgname, msg="Decline to target altitude complete!")
            return
        log_system(msg=f"Current Altitude: {current_pos['alt']} | Target Altitude: {target_alt}", msgname=msgname)
        await asyncio.sleep(1)