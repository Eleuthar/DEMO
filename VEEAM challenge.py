from hashlib import md5
from sys import argv
from os import walk, listdir, path, mkdir, replace, remove, rmdir, rename
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
    $ python dir_sync.py "C:\\Users\\MrRobot\\Documents\\Homework" "C:\\Users\\MrRobot\\Downloads\\VEEAM_CLOUD\\Homework" 5 M "C:\\Program Files\\VEEAM\\logs"
    
    Example for synchronizing every 5 seconds with relative path:
    $ python ..\\INFOSEC .\\INFOSEC 5 S .\\logz
    '''
    

if len( argv ) != 6 or not argv[3].isdigit() or argv[4].upper() not in [ 'S','M','H','D' ]:
    print( __doc__ )
    exit()
    
    
# global variables    
timeframe = { 
    "S" : 1,
    "M" : 60,
    "H" : 3600,
    "D" : 86400
 }
 
 
client = path.realpath( argv[1] )
cloud = path.realpath( argv[2] )
log_path = path.realpath( argv[5] )


# interval translated into seconds
interval = ( int( argv[3] ) * timeframe[ argv[4].upper( ) ] )

client_hexmap = { }
cloud_hexmap = { }
empty_root = set( )

    
def setup_log_path( log_path ):
# implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
    
    print( f'Validating log directory: "{ log_path }"\n' )

    # user input can end with < \\" > which will add " to the path, invalidating it
    log_path = log_path[:-1] if '"' in log_path else log_path    
   
    # folder check
    if not path.exists( log_path ):    
        
        # set a unique delimiter regardless of platform (Linux\Windows)
        sep = '\\' if '\\' in log_path else '/'            
        
        split_path = log_path.split( sep )
        dir_name = split_path.pop()
        upper_dir = '/'.join( split_path )
        
        print( f'Directory "{ dir_name }" does not exist. Will create it if upper directory "{ upper_dir }" is valid.\n' )
        # upper folder check
        
        if not path.exists( upper_dir ):                
            print( f"Upper directory of { dir_name } does not exist either.\nPlease use an existing directory to store the logs." )
            exit()        
        else:
            print( f"Creating { dir_name } under { upper_dir }\n" )
            mkdir( log_path )
            return True      
    else:
        log_path = path.join ( log_path, "dirSync logs" )
        print( f"Saving logs in { log_path }\n" )
        return True


def new_log_file( log_path, ymd_now ):  
    # File name format: dirSync_2023-04-18.txt    
    log_name = f"dirSync_{ ymd_now }.txt"
    log_path = path.join( log_path, log_name )
    log_file = open( log_path, 'a', encoding = 'UTF-8' )    
    return log_file


def log_it( logger, log_item ):    
    print( log_item )
    logger.write( log_item )    
    return


def generate_file_hex( root, filename, blocksize=8192 ):
    hh = md5()
    with open( path.join( root, filename ) , "rb" ) as f:
        while buff := f.read( blocksize ):
            hh.update( buff )
    return hh.hexdigest()


def generate_hexmap( target, logger ):

    global empty_root 
    
    hexmap = { 
        'root': [],
        'fname': [], 
        'hex': []
    }
    
    logger.write( f" {target} HEXMAP ".center (60, "-"))
    
    for directory in walk( target ):
    # ( 0=dirname, 1=[folders], 2=[files] )   
        # [ len( target ) : ]
        # separate starting from basename      
        root = directory[0]        
        
        # handle empty dir
        if len( listdir( root ) ) == 0:
            empty_root.add( root )
            
        for fname in directory[2]:
            hexmap[ 'root' ].append( root )
            hexmap[ 'fname' ].append( fname )
            hx = generate_file_hex( root, fname )
            hexmap[ 'hex' ].append( hx )            
            logger.write( root )
            logger.write( fname )
            logger.write( hx )
            logger.write(f"\n\n{60*'-'}\n\n")            
    return hexmap


def rename_it( logger, prop, fpath_on_cloud ):

    global client_hexmap, cloud
    
    old_path = fpath_on_cloud

    for z in range( len( client_hexmap[ 'hex' ] ) ):
    
        if prop == client_hexmap[ 'hex' ][ z ]:    
        
            set_trace()
            # extract the corresponding full path on client side    
            new_fname = client_hexmap[ 'fname' ][ z ]            
            new_root = client_hexmap[ 'root' ][ z ][ len( client ) : ]
            
            new_root = new_root.removeprefix('\\') if '\\' in new_root else new_root.removeprefix('/')
            
            new_path = path.join( cloud, new_root, new_fname )    
            
            try:
                log_it( logger, f"RENAMING {old_path} to {new_path}\n")
                rename( new_path, old_path )
                log_it( logger, f"RENAMED {old_path} to {new_path}\n")
                
            except Exception as X:
                log_it( logger, f"{X}\n" )
                
            return


def replace_it( logger, expected_path_on_client, fpath_on_cloud ):
            
    try:                    
        log_it( logger, f"UPDATING { fpath_on_cloud }\n" )        
        remove( fpath_on_cloud )        
        copy2( expected_path_on_client, fpath_on_cloud )        
        log_it( logger, f"UPDATED { fpath_on_cloud }\n" )
        
    except Exception as X:
        log_it( logger,  f"Error: { X }\n" )
      
    return

    
def remove_it( logger, fpath_on_cloud ):

    try:
        print( f"DELETING {fpath_on_cloud}\n" )
        remove( fpath_on_cloud )
        log_it( logger, f"DELETED {fpath_on_cloud}\n")
        
    except Exception as X:
        log_it( logger, X )
    
    return
    
    
def rm_obsolete_dir( root, logger ):      
    try:
        set_trace()
        log_it( logger, f"Deleting directory { root }\n" )
        rmdir( root )
        log_it( logger, f"Deleted directory { root }\n" )
        
        # parent directory can become empty and obsolete
        removed_dir = os.path.basename( root ) 
        upper_dir = root[ : removed_dir ]
        
        upper_dir_common_path = upper_dir[ len( client ) : ].removeprefix(' \\ ') if '\\' in upper_dir else upper_dir.removeprefix('/')
        
        expected_path_on_client = path.join( client, upper_dir_common_path )
        
        if not path.exists( expected_path_on_client ):
            rm_obsolete_dir( expected_path_on_client, logger )
        
    except Exception as X:
        log_it( logger, f"Error: { X }\n" )    
    return
        

def diff_hex( logger ):
    # start from the client deepest root    
    # if root not in cloud ['root'], review content recursively to remove\move\keep\update, then add to set for final cleanup
    
    global client, cloud, client_hexmap, cloud_hexmap        
    dir_to_rm = set( )

    set_trace( )
        
    # compare cloud against client
    for mpty in empty_root:
    
        # remove cloud part from path        
        common_root = mpty[ len( cloud ) : ]
        common_root = common_root.removeprefix('\\') if '\\' in common_root else common_root.removeprefix('/')
        
        # add the client part for expected path
        expected_root_path_on_client = path.join( client, common_root )
        
        if not path.exists( expected_root_path_on_client ) and expected_root_path_on_client != client:
           dir_to_rm.add( mpty )
        
    
    for hx_tgt in reversed( cloud_hexmap['hex'] ):
    
        index = cloud_hexmap['hex'].index( hx_tgt )
        
        dst_root = cloud_hexmap[ 'root' ][ index ]
        dst_fn = cloud_hexmap[ 'fname' ][ index ] 
        dst_hex = cloud_hexmap[ 'hex' ][ index ]
        
        fpath_on_cloud = path.join( dst_root, dst_fn )
        
        if dst_root not in client_hexmap[ 'root' ]:
            dir_to_rm.add( dst_root )
        
        # from the landing path point, the file path should be identical for both client & cloud
        # extract with "[ len( cloud ) : ]" the part that cannot be used by target
        # client = C:\Downloads\Pirated_MP3\<common root>
        # cloud = C:\Backup\Pirated_Music\<common root>
        # if path string starts or ends with '\' or '/' join will fail
        
        common_root_fn = path.join( dst_root[ len( cloud ) : ], dst_fn )        
        common_root_fn = common_root_fn.removeprefix('\\') if '\\' in common_root_fn else common_root_fn.removeprefix('/')
        
        expected_path_on_client = path.join(client, common_root_fn)
        
        # same hex
        if dst_hex in client_hexmap['hex']:
        
            # same path > PASS
            if path.exists( expected_path_on_client ):
                log_it( logger, f"PASS { fpath_on_cloud }\n" )
                
            # different path > RENAME
            else:                
                rename_it( logger, dst_hex, fpath_on_cloud )            
       
       # no hex match
        else:
        
            # same path > REPLACED
            if path.exists( expected_path_on_client ):
                replace_it( logger, expected_path_on_client, fpath_on_cloud )
                                
            # same filename but different root > RENAME
            elif not path.exists( expected_path_on_client ) and dst_fn in client_hexmap['fname']:                
                rename_it( logger, dst_root, fpath_on_cloud )
                
            # no path match > DELETE
            else:
                remove_it( logger, fpath_on_cloud )          
            
    return dir_to_rm


def dump_to_cloud( logger ):

    global client, cloud
    
    log_it( logger, f"Performing full sync\n" )

    for item in listdir(client):    
        try:
            src = path.join( client, item )
            dst = path.join( cloud, item )
            
            if path.isdir( src ):                
                copytree(src, dst )
            else:
                copy2( src, dst )
                
            log_it( logger, f"Copied { item }\n" )
            
        except Exception as X:
            log_it( logger,  f"Error: { X }\n" )
    return


def one_way_sync( logger ):
# triggered by main if hexmap diff
    
    global client, cloud, client_hexmap, cloud_hexmap
    
    sync_start = datetime.now()
     
    log_it( logger, f"Starting sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
    
    # get the source directory hash map
    client_hexmap = generate_hexmap( client, logger )
    
    # full dump to cloud storage
    if len( listdir( cloud ) ) == 0 and len( listdir( client ) ) != 0:
        dump_to_cloud( logger )
        cloud_hexmap = deepcopy(client_hexmap)
        
    else:
        # get the destination directory hash map
        cloud_hexmap = generate_hexmap( cloud, logger )    
        # compare with cloud storage hexmap: root fname hex
        obsolete_dirs = diff_hex( logger )
        for obsolete_dir in obsolete_dirs:
            rm_obsolete_dir( obsolete_dir, logger)
    
    sync_finish = datetime.now()
    
    log_it( logger, f"Finished sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
    
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
    
    log_it( logger, f"Last sync took { sync_duration }\n" )
    
    if sync_delta <= 0:
        sleep( interval )
        main(log_path_set, logger)
    else:
        sleep( sync_delta )
        main(log_path_set, logger)


if __name__ == '__main__':
    main()
