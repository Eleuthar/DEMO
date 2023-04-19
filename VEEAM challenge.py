from hashlib import md5
from sys import argv
from os import listdir, path, mkdir, replace, remove, removedirs
from shutil import copytree, copy2
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
    
def setup_log_path( client_path ):
# implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
    print( f"Validating log directory: {client_path}\n" )    
    # set a unique delimiter regardless of platform (Linux\Windows)
    if '\\' in client_path:
        client_path.replace( '\\', '/' )
    # folder check
    if not path.exists( client_path ):
        split_path = path.split( '/' )
        dir_name = split_path.pop()
        upper_dir = '/'.join( split_path )
        print( f'Directory "{dir_name}" does not exist. Will create it if the upper directory is valid.\n' )
        # upper folder check
        if not path.exists( upper_dir ):                
            print( f"Upper directory of {dir_name} does not exist either\n.Please use an existing directory to store the logs." )              
            exit()        
        else:
            print( f"Creating {dir_name} under {upper_dir}\n" )
            os.mkdir( client_path )
            return True      
    else:
        print( f"Saving logs in {client_path}\n"
        return True
        

def new_log_file( log_path, ymd_now ):  
    # File name format: dirSync_2023-04-18.txt    
    log_name = f"dirSync_{ymd_now}.txt"
    log_path = os.path.join( log_path, log_name )
    log_file = open( log_path, 'a' )    
    return log_file


def generate_file_hex( rootdir, filename, blocksize=8192 ):
    hh = md5()
    with open( os.path.join( rootdir, filename ) , "rb" ) as f:
        while buff := f.read( blocksize ):
            hh.update( buff )
    return hh.hexdigest()


def generate_hexmap( client ):
    hexmap = {
        'root': [],
        'fname': [], 
        'hex': []    
    }    
    for directory in os.walk( client ):
    # ( 0=dirname, 1=[folders], 2=[files] )        
        root = directory[0]        
        for fname in directory[2]:
            hexmap['root'].append( root )
            hexmap['fname'].append( fname )
            hexmap['hex'].append( generate_file_hex( root, fname ) )
    return hexmap

  
def one_way_sync( logger ):

    global client, cloud, client_hexmap, cloud_hexmap    
    
    sync_start = datetime.now()
    
    log_item = f"Starting sync at {datetime.now().strftime( '%y-%m-%d %H:%M' )}\n"
    print( log_item )
    logger.write( log_item )
    
    # get the source directory hash map
    client_hexmap = generate_hexmap( client )
    
    # initialization of cloud storage
    if listdir(cloud) == 0:
        cloud_hexmap = client_hexmap
        
        for item in listdir(client):
            copytree(item, path.join( cloud, item ) if path.isdir( item ) else copy2(item, path.join( cloud, item )
    
    # compare with cloud storage hexmap: root fname hex
    else:        
        for j in range( len( cloud_hexmap['hex'] ) ):
              
            # delete file with not matching hex & file not in source
            if (cloud_hexmap['hex'][j] not in client_hexmap['hex'] and 
                cloud_hexmap['fname'][j] not in client_hexmap['fname']and 
                path.exists( path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] ) ) ):
                
                remove( path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] ) )
                    
            # replace file if hex not matching
            elif cloud_hexmap['hex'][j] not in client_hexmap['hex'] and cloud_hexmap['fname'][j] in client_hexmap['fname'] and path.exists( path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] ) ):
            
                remove( path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] ) )
                src = path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] )
                dst = path.join( client_hexmap['root'][j], client_hexmap['fname'][j] )
                copy2(src, dst)
                
                    
    sync_finish = datetime.now()
    
    log_item = f"Finished sync at {datetime.now().strftime( '%y-%m-%d %H:%M' )}\n"
    print( log_item )
    logger.write( log_item )
    
    return ( sync_finish - sync_start ).seconds
       
    
def main( log_path_set=False, logger=None ):    
    
    global client, cloud, log_path, interval    
    
    # log file timeframe
    ymd_now = datetime.now().strftime( '%Y-%m-%d' )    
    
    # setup log file
    if not log_path_set:       
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
    
    log_item = f"Last sync took {sync_duration}\n")
    print(log_item)
    logger.write(log_item)
    
    if sync_delta <= 0:
        main(log_path_set, logger)
    else:
        sleep( sync_delta )
        main(log_path_set, logger)


# global variables    
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
client_hexmap = {}
cloud_hexmap = {}


if __name__ == '__main__':
    main()
