import socket
from hashlib import md5
from sys import argv
import os
from datetime import datetime
from time import sleep

from pdb import set_trace


__doc__ = '''
    Usage: python dir_sync.py <source_path> <destination_path> <integer> <S||M||H||D> <log_path>
    S = SECONDS
    M = MINUTES
    H = HOURS
    D = DAYS
    
    Example for synchronizing every 5 minutes with absolute path:   
    $ python dir_sync.py "C:\\Users\\MrRobot\\Documents\\Homework\\" "C:\\Users\\MrRobot\\Downloads\\VEEAM_CLOUD\\Homework\\" 5 M "C:\\Program Files\\VEEAM\\logs\\"
    
    Example for synchronizing every 5 seconds with relative path:
    $ python ..\INFOSEC .\INFOSEC 5 S .\logz
    '''
    

if len(argv) != 5 or argv[3].isdigit() != True or argv[4].upper() not in ['S','M','H','D']:        
    print(__doc__)
    exit()

set_trace()


def is_year_leap(year):
    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True
    else:
        return False
    

def days_in_month(year, month):
    m31 = [1,3,5,7,8,10,12]
    m30 = [2,4,6,9,11]
    if month in m31:
        return 31
    elif month in m30:
        if is_year_leap(year) and month == 2:
            return 29
        elif month == 2:
            return 28
        else:
            return 30

      
def get_yesterday(year, month, day, ymd_now):
    # compare to ymd_now like 2023-04-18
    if day == 1 and month == 1:
        year -= 1
        month = 12
        day = 31
    elif day == 1:
        month -= month
        day = days_in_month(year, month)
    elif 
        day = day-1
        month = month
        
    return datetime(year, month, day).strftime('%Y-%m-%d')
     

def setup_log_path(path):
    # implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
    print(f"Validating log directory: {path}\n")
    
    if '\\' in path:
        path.replace('\\', '/')
    
    if os.path.exists(path) == False:          
        split_path = path.split('/')
        dir_name = split_path.pop()
        upper_dir = '/'.join(split_path)
        print(f'Directory "{dir_name}" does not exist. Will create it if the upper directory is valid.\n')
        
        if os.path.exists(upper_dir) != True:                
            print(f"Upper directory of {dir_name} does not exist either\n.Please use an existing directory to store the logs.")                          
            exit()
        
        else:
            print(f"Creating {dir_name} under {upper_dir}\n")
            os.mkdir(path)
            return
      
    else:
        print(f"Saving logs in {path}\n"
        return
        

def new_log_file(log_path, ymd_now):
        
    ymd_yesterday = get_yesterday(year, month, day, ymd_now)
    
    if validate_path(log_path) == False:
        
    
    # File name format: dirSync_2023-04-18.txt    
    current_log_name = f"dirSync_{ymd_now}.txt"
    current_log_path = os.path.join(log_path, current_log_name)
    previous_log_name = f"dirSync_{ymd_yesterday}.txt"
    previous_log_path = os.path.join(log_path, previous_log_name)
    
    # previous log close check    
    if os.path.exists(previous_log_path):
        
    
    return current_log


def one_way_sync(logg):
    # used after initial sync
    global client, cloud, log_path, interval
    
    sync_start = datetime.now()
    log_item = f"Starting sync at {datetime.now().strftime('%y-%m-%d %H:%M')}\n"
    print(log_item)
    logg.write(log_item)
    
    
def get_client_hexmap(client):
    
    for directory in os.walk(client):
    # (current_dir, [folders], [files])
        for dir_item in directory:
        # map hash to digest
        
        
    hex_digest = md5(file.read()).hexdigest()
    
    
    sync_finish = datetime.now()
    log_item = f"Finished sync at {datetime.now().strftime('%y-%m-%d %H:%M')}\n"
    print(log_item)
    logg.write(log_item)
    
    return (sync_finish - sync_start).seconds
    
    
def main(today, logg=None):
    
    global client, cloud, log_path, interval
    
    # setup log file
    ymd_now = datetime.now().strftime('%Y-%m-%d')
    current_day_log = setup_log_file(log_path, ymd_now)
    
    # Check if previous day log is closed
    
    logg = open(current_day_log, 'a')
    # sync
    sync_duration = one_way_sync(logg)
    
    # determine last sync duration to cut from the interval sleep time until next sync
    sync_delta = sync_duration - interval)
    
    if sync_delta <= 0:
        main()
    else:
        sleep(sync_delta)
        main()
    
   
# time expressed seconds
today = datetime.now().day

timeframe = {
    "S" : 1,
    "M" : 60,
    "H" : 3600,
    "D" : 86400
}

client = argv[1]

cloud = argv[2]

# interval translated into seconds
interval = (argv[3] * timeframe[argv[4].upper()])

log_path = argv[5]

hex_map = []
