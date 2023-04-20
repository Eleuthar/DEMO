from hashlib import md5
from sys import argv
from os import walk, listdir, path, mkdir, replace, remove, removedirs
from shutil import copytree, copy2
from datetime import datetime
from time import sleep
from copy import deepcopy

from pdb import set_trace


__doc__ = '''
    Usage: python dirSync.py <source_path> <destination_path> <integer> <S||M||H||D> <log_path>
    S = SECONDS
    M = MINUTES
    H = HOURS
    D = DAYS
    
    Example for synchronizing every 5 minutes with absolute path:   
    $ python dir_sync.py "C:\\Users\\MrRobot\\Documents\\Homework\\" "C:\\Users\\MrRobot\\Downloads\\VEEAM_CLOUD\\Homework\\" 5 M "C:\\Program Files\\VEEAM\\logs\\"
    
    Example for synchronizing every 5 seconds with relative path:
    $ python ..\INFOSEC .\INFOSEC 5 S .\logz
    '''
    

#if len( argv ) != 6 or argv[4].isdigit() != True or argv[4].upper() not in ['S','M','H','D']:
 #   print( __doc__ )
  #  exit()

    
def setup_log_path( log_path ):
# implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
    
    print( f"Validating log directory: {log_path}\n" )    
    # set a unique delimiter regardless of platform (Linux\Windows)
    
    # folder check
    if not path.exists( log_path ):
        if '\\' in log_path:
            log_path = log_path.replace( '\\', '/' )
        split_path = log_path.split( '/' )
        dir_name = split_path.pop()
        upper_dirname = split_path[-1]
        upper_dir = '/'.join( split_path )
        print( f'Directory "{dir_name}" does not exist. Will create it if upper directory {upper_dirname} is valid.\n' )
        # upper folder check
        if not path.exists( upper_dir ):                
            print( f"Upper directory of {dir_name} does not exist either\n.Please use an existing directory to store the logs." )
            exit()        
        else:
            print( f"Creating {dir_name} under {upper_dir}\n" )
            mkdir( log_path )
            return True      
    else:
        print( f"Saving logs in {log_path}\n" )
        return True
        

def new_log_file( log_path, ymd_now ):  
    # File name format: dirSync_2023-04-18.txt    
    log_name = f"dirSync_{ymd_now}.txt"
    log_path = path.join( log_path, log_name )
    log_file = open( log_path, 'a' )    
    return log_file


def generate_file_hex( rootdir, filename, blocksize=8192 ):
    hh = md5()
    with open( path.join( rootdir, filename ) , "rb" ) as f:
        while buff := f.read( blocksize ):
            hh.update( buff )
    return hh.hexdigest()


def generate_hexmap( client ):
    hexmap = {
        'root': [],
        'fname': [], 
        'hex': []    
    }    
    for directory in walk( client ):
    # ( 0=dirname, 1=[folders], 2=[files] )        
        root = directory[0]        
        for fname in directory[2]:
            hexmap['root'].append( root )
            hexmap['fname'].append( fname )
            hexmap['hex'].append( generate_file_hex( root, fname ) )
    return hexmap


def diff_hex(client_hexmap, cloud_hexmap):
    
    '''
    diff hex	
        diff filename
            - DELETE	
        diff root
            - DELETE & COPY TO NEW ROOT

    diff filename	
        eq hex
            diff root ?	
            - RENAME
    '''
    


    for j in range( len( cloud_hexmap['hex'] ) ):
          
        # delete file with not matching hex & file not in source
        if ( cloud_hexmap['hex'][j] not in client_hexmap['hex'] and 
            cloud_hexmap['fname'][j] not in client_hexmap['fname']and 
            path.exists( path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] ) ) ):
            
            try:
                f = path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] )
                remove( f )
                log_item( f"Removed {f}\n" )
                logger.write( log_item )
                print( log_item )
            
            except Exception as X:
                log_item( f"Error: {X}\n" )
                logger.write( log_item )
                print( log_item )
            

        # replace file if hex not matching
        elif ( cloud_hexmap['hex'][j] not in client_hexmap['hex'] and 
            cloud_hexmap['fname'][j] in client_hexmap['fname'] and 
            path.exists( path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] ) ) ):
            
            try:
                f = path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] )
                remove( f )
                
                log_item( f"Removed {f}\n" )
                logger.write( log_item )
                print( log_item )
                
                src = path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] )
                dst = path.join( client_hexmap['root'][j], client_hexmap['fname'][j] )
                copy2(src, dst)
                
                log_item( f"Copied {src} to {dst}\n" )
                logger.write( log_item )
                print( log_item )
            
            except Exception as X:
                log_item( f"Error: {X}\n" )
                logger.write( log_item )
                print( log_item )
                
            
        # rename file with matching hex with different root \ filename in cloud
        elif cloud_hexmap['hex'][j] in client_hexmap['hex'] and not path.exists( path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] ) ):
            
            dst = path.join( cloud_hexmap['root'][j], cloud_hexmap['fname'][j] )
            src = path.join( client_hexmap['root'][j], client_hexmap['fname'][j] )
            
            try:
                replace( src, dst )
                log_item( f"Replaced {dst} with {src}\n" )
                logger.write( log_item )
                print( log_item )
            
            except Exception as X:
                log_item( f"Error: {X}\n" )
                logger.write( log_item )
                print( log_item )
                
                
    # delete directories not existing on cloud after digest iteration
    for j in range( len( cloud_hexmap['root'] ) ):
        
        if client_hexmap['root'][j] not in client_hexmap['root']:
        
            try:
                removedirs( cloud_hexmap['root'][j] )
                log_item = f"Deleted directory {cloud_hexmap['root'][j]}\n"
                print( log_item )
                logger.write( log_item )
            
            except Exception as X:
                log_item = f"Error: {X}\n"
                print( log_item )
                logger.write( log_item )
    


def dump_to_cloud( client, cloud, logger ):
    
    log_item = f"Performing full sync\n"
    print( log_item )
    logger.write( log_item )

    for item in listdir(client):    
        try:
            src = path.join( client, item )
            dst = path.join( cloud, item )
            
            if path.isdir( src ):                
                copytree(src, dst )
            else:
                copy2( src, dst )
                
            log_item = f"Copied {item}\n"
            print( log_item )
            logger.write( log_item )
            
        except Exception as X:
            log_item = f"Error: {X}\n"
            print( log_item )
            logger.write( log_item )            
    return


def one_way_sync( logger ):
# triggered by main if finds hexmap diff
    
    global client, cloud, client_hexmap, cloud_hexmap    
    
    sync_start = datetime.now()
     
    log_item = f"Starting sync at {datetime.now().strftime( '%y-%m-%d %H:%M' )}\n"
    print( log_item )
    logger.write( log_item )
    
    # get the source directory hash map
    client_hexmap = generate_hexmap( client )
    
    # full dump to cloud storage
    if len( listdir( cloud ) ) == 0 and len( listdir( client ) ) != 0:
        dump_to_cloud( client, cloud, logger )
        cloud_hexmap = deepcopy(client_hexmap)
        
    else:
        # get the destination directory hash map
        cloud_hexmap = generate_hexmap( cloud )    
        # compare with cloud storage hexmap: root fname hex
        diff_hex( client_hexmap, cloud_hexmap )
    
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
        log_path_set = setup_log_path( log_path )    
    
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
    sync_delta = sync_duration - interval
    
    log_item = f"Last sync took {sync_duration}\n"
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
interval = ( int(argv[3]) * timeframe[argv[4].upper()] )
log_path = argv[5]
client_hexmap = {}
cloud_hexmap = {}


if __name__ == '__main__':
    main()
