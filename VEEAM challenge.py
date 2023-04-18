

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
    $ python dir_sync.py "C:\\Users\\MrRobot\\Documents\\Homework\\" "C:\\Users\\MrRobot\\Downloads\\VEEAM_CLOUD\\Homework\\" 5 minutes "C:\\Program Files\\VEEAM\\logs\\"
    
    Example for synchronizing every 5 seconds with relative path:
    $ python ..\INFOSEC .\INFOSEC 5 SECONDS .\logz
    '''
    

if len(argv) != 5 or argv[3].isdigit() != True or argv[4].upper() not in ['S','M','H','D']:        
    print(__doc__)
    exit()

set_trace()


def validate_log_path(path):
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
            return False
      
    else:
        return True
        

def setup_log_file(log_path, ymd_now):
    # Logs are stored under <log_path>\<currentYear>\<currentMonth>\ directory
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    
    if validate_path(log_path) == False:
        os.mkdir(log_path)
    
    year_dirname = os.path.join(log_path, year)    
    month_dirname = os.path.join(year_dirname, month)
    
    # If there is no file matching the current day under current month directory, make one
    if os.path.exists(year_dirname) == False:
        os.mkdir(year_dirname)
    
    # If there is no current month directory, make one
    if os.path.exists(month_dir) == False:
        os.mkdir(month_dirname)

    # File name format: dirSync_2023-04-18.txt    
    current_day_log = f"dirSync_{ymd_now}.txt"
    
    if current_day_log not in listdir(month_dirname):
        os.path.join(month_dirname, current_day_log)
    
    return current_day_log  


def one_way_sync(current_day_log):
    global client, cloud    
    sync_start = datetime.now()
    
    # hash can be changed by: dir name, inner file name, inner file content, file permission? 
    
    hex_digest = md5(b'').hexdigest()
    
    
    sync_finish = datetime.now()
    return (sync_finish - sync_start).seconds
    
    
def main(client, cloud, interval):
    
    # setup log file
    ymd_now = datetime.now().strftime('%Y-%m-%d')
    current_day_log = setup_log_file(log_path, ymd_now)
    
    # sync
    sync_duration = one_way_sync(current_day_log)
    
    # determine last sync duration to cut from the interval sleep time until next sync
    sync_delta = sync_duration - interval)
    
    if sync_delta <= 0:
        main(client, cloud, interval)
    else:
        sleep(sync_delta)
        main(client, cloud, interval)
    
   
# time expressed seconds
timeframe = {
    "s" : 1,
    "m" : 60,
    "h" : 3600,
    "d" : 86400
}

client = argv[1]

cloud = argv[2]

# interval translated into seconds
interval = (argv[3] * timeframe[argv[4]])

log_path = argv[5]
