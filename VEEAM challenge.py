'''
Usage: python dir_sync.py <source_path> <destination_path> <integer> <MINUTES || HOURS || DAYS> <log_path>

Example for synchronizing every 5 minutes:   
$ python dir_sync.py "C:\Users\MrRobot\Documents\Homework\" "C:\Users\MrRobot\Downloads\VEEAM_CLOUD\Homework\" 5 minutes "C:\Program Files\VEEAM\logs\Captain's log.txt"

Can use relative or absolute case insensitive path.    
'''

import socket
from hashlib import md5
from sys import argv
import os
from datetime import datetime
from time import sleep
from pdb import set_trace



if __name__ == '__main__':
    set_trace() 
    
    
    if len(argv) != 5 or argv[3].isdigit() != True:        
        print(__doc__)
        exit()
  
    
    def validate_log_path(path):
               
        if '\\' in path:
            path.replace('\\', '/')
                
        print(f"Validating log directory: {path}\n")
        
        if os.path.exists(path) == False:            
            split_path = path.split('/')
            path_name = split_path.pop()
            upper_dir = '/'.join(split_path)
            print(f'Directory "{path_name}" does not exist. Will create it if the upper directory is valid.\n')
            
            if os.path.exists(upper_dir) != True:                
                print(f"Upper directory of {path_name} does not exist either\n.Please use an existing directory to store the logs.")                
                return False
            
            else:
                print(f"Creating {path_name} under {upper_dir}\n")
                return True
          
        else:
            return True  
            
    
    def new_log_file(log_path):
        
        if validate_path(log_path) == False:
            exit()          
        
        # Logs are stored under <log_path>\<currentYear>\<currentMonth>\ directory
        year = datetime.now().year
        month = datetime.now().month
        day = datetime.now().day
            
        os.mkdir(log_path)
        
        year_dirname = os.path.join(log_path,year)        
        month_dirname = os.path.join(year_dir,month)
        
        # If there is no file matching the current day under current month directory, make one
        if os.path.exists(year_dirname)) == False:
            os.mkdir(year_dirname)
        
        # If there is no current month directory, make one
        if os.path.exists(month_dir) == False:
            os.mkdir(month_dirname)

        # File name format: dirSync_2023-04-18.txt
        ymd_now = datetime.now().strftime('%Y-%m-%d')
        current_day_log = f"dirSync_{ymd_now}.txt"
        
        if current_day_log not in listdir(month_dirname):
            return os.path.join(month_dirname, current_day_log
        


    def one_way_sync(client, cloud, interval, logger):
        now = datetime.now()
        
        if 
            logger = new_log_file(log_path, now)
        
        '''
        1. find log file for current day & make new one if none
        
        '''
        
        # hash can be changed by: dir name, inner file name, inner file content, file permission? 
        digest = md5(b'').digest()    
        sleep(interval)
        



    # time expressed seconds
    timeframe = {
        "minutes" : 60
        "hours" : 3600
        "days" : 86400
    }

    client = argv[1]

    cloud = argv[2]

    interval = (argv[3] * timeframe[argv[4]])

    log_path = argv[5]


