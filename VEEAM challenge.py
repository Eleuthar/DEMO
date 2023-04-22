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
tree = {}
tree[ 'client' ] = set( )
tree[ 'cloud '] = set( )

    
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

    global tree
    
    # hexmap flag initalized with None, later marked with "Z"
    # used only for client during diff_hex
    hexmap = {
        'root': [],
        'fname': [], 
        'hex': [],
        'flag' : []
    }
    
    logger.write( f" {target} HEXMAP ".center (60, "-"))
    
    for directory in walk( target ):
    # ( 0=dirname, 1=[folder basenames], 2=[files] )   
        
        root = directory[0]
        
        # get a full list of all folders empty or not
        if len( directory[1] ) != 0:
            for folder in directory[1]:
                tree[ target ].add( path.join( root, folder ) )
            
        for fname in directory[2]:
            hexmap[ 'root' ].append( root )
            hexmap[ 'fname' ].append( fname )
            hx = generate_file_hex( root, fname )
            hexmap[ 'hex' ].append( hx )
            hexmap[ 'flag' ].append(None)
            logger.write( root )
            logger.write( fname )
            logger.write( hx )
            logger.write(f"\n\n{ 85 * '-'}\n\n")
            
    return hexmap


def extract_upper_root( root ):
    removed_dir = os.path.basename( root )        
    upper_root = root[ : root.index( removed_dir ) ]
    # remove ending "\\" or "/"
    upper_root = upper_root[: -1]    
    return upper_root
    

def extract_common_root( target, root ):
           
    common_root = root[ len( target ) : ]    

    # remove beginning "\\" or "/"
    common_root = common_root.removeprefix('\\') if '\\' in common_root else common_root.removeprefix('/')    
    return common_root


def mk_upper_dircloud( root, logger ):
# mirror client directories
    global cloud  
    upper = extract_upper_root( root )    
    while upper != cloud:        
        while not path.exists( upper ):
            try:
                mkdir( upper )
                log_it( logger, f"CREATED DIR: {upper}\n" )
                return            
            except Exception as X:
                log_it( logger, f"{X}\n\nAttempting to create the upper directory\n\n")
                mk_upper_dircloud( upper, logger )
        else:                    
            return

   
def get_removable_dir( tree, logger ):
# compare cloud directories against client

    global cloud

    removable_dir = set( )
    
    if len( tree[ 'cloud' ] ) != 0:
        for folder in tree[ 'cloud' ]:
        
            # remove cloud part from path
            common_root = extract_common_root( cloud, folder )        
            
            # add the client part for expected path
            expected_root_path_on_client = path.join( client, common_root )
            
            if not path.exists( expected_root_path_on_client ) and expected_root_path_on_client != client:
            
               log_it(logger, f"Prepared for removal: {folder}\n")
               removable_dir.add( folder )
   
    return removable_dir

    
def rm_obsolete_dir( root, logger ):  
    
    global cloud
    
    try:        
        log_it( logger, f"Deleting directory { root }\n" )
        rmdir( root )
        log_it( logger, f"Deleted directory { root }\n" )
        
        # parent directory can become empty and obsolete               
        upper_root = extract_upper_root( root )        
        upper_root_common_path = extract_common_root( cloud, upper_root )
        
        # path has reached sync target base root        
        if upper_root_common_path == '':            
            return
            
        expected_path_on_client = path.join( client, upper_root_common_path )
        
        if not path.exists( expected_path_on_client ):
            rm_obsolete_dir( upper_root, logger )
        
    except Exception as X:
        log_it( logger, f"Error: { X }\n" ) 
        
    return


def rename_it( logger, prop, fpath_on_cloud ):

    global client_hexmap, cloud
    
    old_path = fpath_on_cloud

    for z in range( len( client_hexmap[ 'hex' ] ) ):
    
        if prop == client_hexmap[ 'hex' ][ z ]:    
        
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
        log_it( logger,  f"{ X }\n" )
      
    return

    
def remove_it( logger, fpath_on_cloud ):

    try:
        print( f"DELETING {fpath_on_cloud}\n" )
        remove( fpath_on_cloud )
        log_it( logger, f"DELETED {fpath_on_cloud}\n")
        
    except Exception as X:
        log_it( logger, X )
    
    return
   

def flag_hex( prop, logger, action=None ):
    
    global client_hexmap
    
    for z in range( len(client_hexmap['hex']) ):
        
        # prop is basename to find the actual root path, supposedly the only file with this name
        if action == 'RENAME' and prop == client_hexmap[ 'fname' ][ z ]:
            client_hexmap[ 'flag' ][ z ] = 'Z'            
            
        # here prop is (common_root, dst_fn)
        elif action == 'REPLACE' and prop[0] == client_hexmap[ 'root' ][ z ] and prop[1] == client_hexmap[ 'root' ][ z ]:
            client_hexmap[ 'flag' ][ z ] = 'Z'
    
        # hex matching
        elif action == None and prop == client_hexmap[ 'hex' ][ z ]:
            client_hexmap[ 'flag' ][ z ] = 'Z'            
        
    return

  
def diff_hex( logger ):
    # start from the client deepest root    
    # if root not in cloud ['root'], review content recursively to remove\move\keep\update, then add to set for final cleanup
    
    global client, cloud, client_hexmap, cloud_hexmap, tree
    
    dir_to_rm = get_removable_dir( tree, logger )
    
    # cloud-side cleanup
    for hx_tgt in reversed( cloud_hexmap['hex'] ):
    
        index = cloud_hexmap['hex'].index( hx_tgt )
        
        dst_root = cloud_hexmap[ 'root' ][ index ]
        dst_fn = cloud_hexmap[ 'fname' ][ index ] 
        dst_hex = cloud_hexmap[ 'hex' ][ index ]
        
        fpath_on_cloud = path.join( dst_root, dst_fn )
        
        common_root = extract_common_root( cloud, dst_root )
        
        # enrich list of empty removable root with ones not existing on client-side
        if common_root not in client_hexmap[ 'root' ]:
            dir_to_rm.add( dst_root )
        
        # from the landing path point, the file path should be identical for both client & cloud
        # extract with "[ len( cloud ) : ]" the part that cannot be used by target
        # client = C:\Downloads\Pirated_MP3\<common root>
        # cloud = C:\Backup\Pirated_Music\<common root>
        # if path string starts or ends with '\' or '/' join will fail
        
        common_root_fn = path.join( common_root, dst_fn )
        
        expected_path_on_client = path.join(client, common_root_fn)
        
        # same hex
        if dst_hex in client_hexmap['hex']:
        flag_hex( dst_hex, logger )
        
            # same path > PASS
            if path.exists( expected_path_on_client ):                
                log_it( logger, f"PASS { fpath_on_cloud }\n" )
                
            # different path > RENAME
            else:                
                rename_it( logger, dst_hex, fpath_on_cloud )            
       
       # no hex match
        else:
        
            # same path > REPLACE
            if path.exists( expected_path_on_client ):
            
                flag_hex( (common_root, dst_fn), logger, action='REPLACE' )
                replace_it( logger, expected_path_on_client, fpath_on_cloud )

            # same filename but different root > RENAME
            elif not path.exists( expected_path_on_client ) and dst_fn in client_hexmap['fname']:
            
                flag_hex( dst_fn, logger, action='RENAME' )            
                rename_it( logger, dst_root, fpath_on_cloud )
                
            # no path match > DELETE
            else:
                remove_it( logger, fpath_on_cloud )          
            
    # hexmap > tree['cloud'] > removable_dir set() > dir_to_rm > obsolete_dirs
    return dir_to_rm


def full_dump_to_cloud( logger ):

    global client, cloud
    
    log_it( logger, f"STARTING FULL SYNC\n" )
    
    for item in listdir(client):    
        try:
            src = path.join( client, item )
            dst = path.join( cloud, item )
            
            if path.isdir( src ):                
                copytree( src, dst )
            else:
                copy2( src, dst )
                
            log_it( logger, f"Copied { item }\n" )
            
        except Exception as X:
            log_it( logger,  f"Error: { X }\n" )
            
    log_it( logger, f"FINISHED FULL SYNC\n" )
    
    return


def selective_dump_to_cloud( logger ):
    
    global client_hexmap, cloud
    
    for q in range( len( client_hexmap[ 'hex ' ] ) ):
        
        # unhandled files are not flagged
        if client_hexmap[ 'flag' ][ q ] == None:
            
            # validate common_root on cloud
            common_root = extract_common_root( client, [client_hexmap[ 'root '][ q ] )            
            client_file = client_hexmap[ 'fname' ][ q ]             
            fpath_on_client = path.join( client, common_root, client_file )            
            dirpath_on_cloud = path.join( cloud, common_root )            
            fpath_on_cloud = path.join( dirpath_on_cloud, client_file )
            
            # target path can be too deep or is not created
            if not path.exists( dirpath_on_cloud ):
            
                try:
                    log_it( logger, f"CREATING {dirpath_on_cloud}\n" )
                    mkdir( dirpath_on_cloud )
                    
                    log_it( logger, f"ADDING {fpath_on_cloud} from {fpath_on_client}\n" )
                    copy2( fpath_on_client, fpath_on_cloud )
                    
                    log_it( logger, "DONE\n" )
                    client_hexmap[ 'flag' ][ q ] = 'Z'
                
                except Exception:
                    log_it( logger, f"{X}\n\nAttempting to create the upper directory\n\n")
                    mk_upper_dircloud( dirpath_on_cloud, logger )
                    
    return
    

def one_way_sync( logger ):
# triggered by main if hexmap diff
    
    global client, cloud, client_hexmap, cloud_hexmap, tree
    
    sync_start = datetime.now()
     
    log_it( logger, f"Starting sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
    
    # get the source directory hash map
    client_hexmap = generate_hexmap( client, logger )
    
    # initial full dump to cloud storage
    if len( listdir( cloud ) ) == 0 and len( listdir( client ) ) != 0:
        full_dump_to_cloud( logger )
        cloud_hexmap = deepcopy(client_hexmap)
        
    else:
        # get the destination directory hash map
        cloud_hexmap = generate_hexmap( cloud, logger )
        
        # mirror source dir tree in descending order
        for client_dir in tree[' client ']:
            if client_dir not in cloud_hexmap[ 'root ']:
                <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        
        # cleanup on cloud storage
        obsolete_dirs = diff_hex( logger )
        
        for obsolete_dir in obsolete_dirs:
            rm_obsolete_dir( obsolete_dir, logger)
            
        # dump left-overs from client
        selective_dump_to_cloud( logger )
    
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
