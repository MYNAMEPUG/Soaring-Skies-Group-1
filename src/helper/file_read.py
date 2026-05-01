
def read_config_file(file = 'info_files/config.txt'):
    config = {}
    with open(file) as f:
        while True:
            read = f.readline()
            if read == '':
                break
            if read.__contains__('#'): # allows files to have comments
                continue
            read = read.removesuffix('\n').split('=')
            if len(read) >= 2:
                config[read[0]] = read[1]
        return config


def read_waypoints(file = 'info_files/waypoints.txt'):
    """If the altitudes are in feet, for the waypoint file write 'feet' in one of the files"""
    waypoints = []
    feet = False
    with open(file) as f:
        while True:
            read = f.readline()
            if read == '':
                break
            # Skip empty lines
            if read.strip() == '':
                continue
            if read == 'feet':
                feet = True
                continue
            if read.__contains__('#'):
                continue
            read = read.removesuffix('\n').split(',')
            # Make sure we have all 3 values (lat, lon, alt)
            if len(read) >= 3:
                try:
                    lat = float(read[0].strip())
                    lon = float(read[1].strip())
                    alt = float(read[2].strip())
                    alt = (alt / 3.281) if feet else alt
                    waypoints.append([lat, lon, alt])
                except ValueError as e:
                    print(f"Warning: Skipping invalid waypoint line: {read} - Error: {e}")
                    continue

    return waypoints

def read_geofence(file = 'info_files/fence.txt'):
    geofence = []
    with open(file) as f:
        while True:
            read = f.readline()
            if read == '':
                break
            # Skip empty lines
            if read.strip() == '':
                continue
            if read.__contains__('#'):
                continue
            read = read.removesuffix('\n').split(',')
            # Make sure we have both lat and lon
            if len(read) >= 2:
                try:
                    lat = float(read[0].strip())
                    lon = float(read[1].strip())
                    geofence.append([lat, lon])
                except ValueError as e:
                    print(f"Warning: Skipping invalid geofence line: {read} - Error: {e}")
                    continue

    return geofence

def file_to_list(file):
    items = []
    with open(file) as f:
        while True:
            read = f.readline()
            if read == '':
                return items
            # Skip empty lines
            if read.strip() == '':
                continue
            if read.__contains__("#"):
                continue
            read = read.removesuffix('\n').strip()
            if read:  # Only add non-empty lines
                items.append(read)

'''DEPRECATED: Replaced by execute_file in file_controller.py'''

def read_file(file):
    items = []
    with open(file) as f:
        while True:
            read = f.readline()
            if read == '':
                return items
            if read.__contains__('#'):
                continue
            read = read.removesuffix('\n')

            # FILE REDIRECT
            if read.__len__() >= 7 and read[0:7] == "redir->":
                print(f'redirection encountered. file name: {read[7:]}')

            # REPOSITION
            if read.__len__() >= 6 and read[0:6] == "repo->":
                target_repo = []
                read = read[6:]
                while True:
                    if not read.__contains__(","):
                        target_repo.append(float(read))
                        break
                    target_repo.append(float(read[0:read.index(',')]))
                    read = read[read.index("," ) +1:]
                print(f'reposition drone to {target_repo}')

            if read.__len__() >= 11 and read[0:11] == "altchange->":
                read = read[11:]
                alt_delta = int(read)
                print(f'changing altitude by {alt_delta} meters')

    return items