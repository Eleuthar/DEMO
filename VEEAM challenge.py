from hashlib import md5
from sys import argv
import os
import shutil
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
    

if len( argv ) != 5 or argv[3].isdigit() != True or argv[4].upper() not in ['S','M','H','D']:
    print( __doc__ )
    exit()

#set_trace()
    
def setup_log_path( path ):
    # implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
    print( f"Validating log directory: {path}\n" )
    
    if '\\' in path:
        path.replace( '\\', '/' )
    
    if os.path.exists( path ) == False:          
        split_path = path.split( '/' )
        dir_name = split_path.pop()
        upper_dir = '/'.join( split_path )
        print( f'Directory "{dir_name}" does not exist. Will create it if the upper directory is valid.\n' )
        
        if os.path.exists( upper_dir ) != True:                
            print( f"Upper directory of {dir_name} does not exist either\n.Please use an existing directory to store the logs." )                          
            exit()
        
        else:
            print( f"Creating {dir_name} under {upper_dir}\n" )
            os.mkdir( path )
            return True
      
    else:
        print( f"Saving logs in {path}\n"
        return True
        

def new_log_file( log_path, ymd_now ):
  
    # File name format: dirSync_2023-04-18.txt    
    log_name = f"dirSync_{ymd_now}.txt"
    log_path = os.path.join( log_path, current_log_name )
    log_file = open( log_path, 'a' )
    
    return log_file


def get_file_hex( rootdir, filename, blocksize=2**20 ):    
    with open( os.path.join( rootdir, filename ) , "rb" ) as f:
        while True:
            buff = f.read( blocksize )
            if not buff:
                break
            md5.update( buff )
    return md5.hexdigest()


def get_client_hexmap( client ):
    
    for directory in os.walk( client ):
    # ( current_dir, [folders], [files] )
        for dir_item in directory:
        # map hash to digest
        
        
    hex_digest = md5( file.read() ).hexdigest()
    
    
    sync_finish = datetime.now()
    log_item = f"Finished sync at {datetime.now().strftime( '%y-%m-%d %H:%M' )}\n"
    print( log_item )
    logg.write( log_item )
    
    return ( sync_finish - sync_start ).seconds


def one_way_sync( logg ):
    # used after initial sync
    global client, cloud, log_path, interval
    
    sync_start = datetime.now()
    log_item = f"Starting sync at {datetime.now().strftime( '%y-%m-%d %H:%M' )}\n"
    print( log_item )
    logg.write( log_item )
       
    
def main( log_path_set=False, logger=None):
    
    global client, cloud, log_path, interval
    
    # log file timeframe
    ymd_now = datetime.now().strftime( '%Y-%m-%d' )
    
    # setup log file
    if log_path_set != True:        
        log_path_set = setup_log_file( log_path, ymd_now )
    
    # Check if the current log file matches the current date
    if logger == None:
        logger = new_log_file( log_path, ymd_now )
    else:
        if ymd_now not in logger.name:
            logger.close()
            logger = new_log_file( log_path, ymd_now )            
    
    # sync folders
    sync_duration = one_way_sync( logger )
    
    # determine last sync duration to cut from the interval sleep time until next sync
    sync_delta = sync_duration - interval )
    
    if sync_delta <= 0:
        main()
    else:
        sleep( sync_delta )
        main()


    
timeframe = {
    "S" : 1,
    "M" : 60,
    "H" : 3600,
    "D" : 86400
}

client = argv[1]

cloud = argv[2]

# interval translated into seconds
interval = ( argv[3] * timeframe[argv[4].upper()] )

log_path = argv[5]

client_hex_map = {}
cloud_hex_map = {}
