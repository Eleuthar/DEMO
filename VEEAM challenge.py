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
    
    $ python dirSync.py "C:\Users\MrRobot\Documents\Homework" "C:\Users\MrRobot\Downloads\VEEAM_CLOUD\Homework" 5 M "C:\Program Files\VEEAM\logs"
    
    
    Example for synchronizing every 5 seconds with relative path:
    
    $ python dirSync.py ..\..\..\INFOSEC .\INFOSEC 5 S .\logz
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
tree[ client ] = set( )
tree[ cloud ] = set( )

    
def setup_log_path( log_path ):
# implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
    
    print( f'Validating log directory: "{ log_path }"\n' )

    # user input can end with < \\" > which will add " to the path, invalidating it
    log_path = log_path[:-1] if '"' in log_path else log_path    
   
    # folder check
    if not path.exists( log_path ):    
        
        # path delimiter
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


def reset_global():
    global client_hexmap, cloud_hexmap, tree
    client_hexmap = { }
    cloud_hexmap = { }    
    tree[ client ] = set( )
    tree[ cloud ] = set( )
    return


def extract_common_root( target, root ):
	
	# From the landing path point, the file path should be identical for both client & cloud.
	# Extract with "[ len( cloud ) : ]" the part that cannot be used by target
	# client = C:\Downloads\Pirated_MP3\<common root>
	# cloud = C:\Backup\Pirated_Music\<common root>
	# If path string starts or ends with '\' or '/' join will fail
	
    common_root = root[ len( target ) : ]    

    # remove beginning "\\" or "/"
    common_root = common_root.removeprefix('\\') if '\\' in common_root else common_root.removeprefix('/')
    
    return common_root


def generate_file_hex( target, root, filename, blocksize=8192 ):
    hh = md5()
    with open( path.join(  target, root, filename ) , "rb" ) as f:
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
        root = extract_common_root( target, directory[0] )
        
        # get a full list of all folders empty or not
        tree[ target ].add( root )
        
        # add only
        for fname in directory[2]:
            hexmap[ 'root' ].append( root )
            hexmap[ 'fname' ].append( fname )
            hx = generate_file_hex( target, root, fname )
            hexmap[ 'hex' ].append( hx )
            hexmap[ 'flag' ].append(None)
            logger.write(f"\n\n{ 85 * '-'}\n\n")
            logger.write( f"\n{ path.join( root, fname ) }\n" )
            logger.write( f"{hx}\n" )
            logger.write(f"\n\n{ 85 * '-'}\n\n")
            
    return hexmap


def extract_upper_root( root ):
# handles already extracted common path
    removed_dir = path.basename( root )
    upper_root = root[ : root.index( removed_dir ) ]    
    # remove ending "\\" or "/"
    upper_root = upper_root[: -1]
    
    if upper_root != '':        
        return upper_root
    else:
        # has reached common root
        return removed_dir
    

def mk_upper_dircloud( root, logger ):
# mirror client directories
    global cloud  
    upper = extract_upper_root( root )    
    upper_path = path.join( cloud, upper )
    
    while not path.exists( upper_path ):
        try:
            mkdir( upper_path )
            log_it( logger, f"\nCREATED DIR: {upper_path}\n" )
            return
            
        except Exception as X:
            log_it( logger, f"{X}\n\nAttempting to create the upper directory\n\n")
            mk_upper_dircloud( upper, logger )
    else:                    
        return

   
def get_removable_dir( tree, logger ):
# applicable only for cloud directories against client
    global cloud
    removable_dir = set( )
    log_it(logger, "\n\nPreparing directories for removal:\n\n")
    
    if len( tree[ cloud ] ) != 0:    
        for folder in tree[ cloud ]:            
            expected_root_path_on_client = path.join( client, folder )
            
            # remove only common root subdir
            if not path.exists( expected_root_path_on_client ) and expected_root_path_on_client != client:            
               log_it(logger, f"{folder}\n")
               removable_dir.add( path.join( cloud, folder ) )
    log_it(logger, "\n\n\n")
    return removable_dir

    
def rm_obsolete_dir( root, logger ):  
# done after file cleanup
    global cloud
    
    try:        
        log_it( logger, f"Deleting directory { root }\n" )
        rmdir( root )
        log_it( logger, f"Deleted directory { root }\n\n" )
        
    except Exception as X:
        # is already deleted, content is already deleted
        log_it( logger, f"\n{ X }\n\n" )
        
    return


def rename_it( logger, hexx, fpath_on_cloud ):

    global client_hexmap, cloud
    
    old_path = fpath_on_cloud

    for z in range( len( client_hexmap[ 'hex' ] ) ):
    
        if hexx == client_hexmap[ 'hex' ][ z ]:    
        
            # extract the corresponding full path on client side    
            new_fname = client_hexmap[ 'fname' ][ z ]            
            new_root = client_hexmap[ 'root' ][ z ][ len( client ) : ]
            
            new_root = new_root.removeprefix('\\') if '\\' in new_root else new_root.removeprefix('/')
            
            new_path = path.join( cloud, new_root, new_fname )    
            
            try:
                log_it( logger, f"\nRENAMING {old_path} to {new_path}\n")
                rename( new_path, old_path )
                log_it( logger, f"\nRENAMED {old_path} to {new_path}\n")
                
            except Exception as X:
                log_it( logger, f"\n{X}\n" )
                
            return


def replace_it( logger, expected_path_on_client, fpath_on_cloud ):
    
    try:
        log_it( logger, f"\nUPDATING { fpath_on_cloud }\n" )        
        remove( fpath_on_cloud )        
        copy2( expected_path_on_client, fpath_on_cloud )        
        log_it( logger, f"\nUPDATED { fpath_on_cloud }\n" )
        
    except Exception as X:
        log_it( logger, f"\n{X}\n" )
      
    return

    
def remove_it( logger, fpath_on_cloud ):

    try:
        print( f"\nDELETING {fpath_on_cloud}\n" )
        remove( fpath_on_cloud )
        log_it( logger, f"\nDELETED {fpath_on_cloud}\n")
        
    except Exception as X:
        log_it( logger, f"\n{X}\n" )
    
    return
   

def flag_hexxed( prop, action=None ):
    
    global client_hexmap
    
    for z in range( len(client_hexmap['hex']) ):
        
        # prop is basename to find the actual root path, being the only file with this name
        if action == 'RENAME' and prop == client_hexmap[ 'fname' ][ z ]:
            client_hexmap[ 'flag' ][ z ] = 'Z'            
            
        # prop is (common_root, dst_fn)
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
    
    
    log_it( logger, "\nTARGET DIRECTORY CLEANUP\n\n" )
    # cloud-side cleanup
    for hx_tgt in reversed( cloud_hexmap['hex'] ):
        set_trace()
        index = cloud_hexmap['hex'].index( hx_tgt )
        
        dst_root = cloud_hexmap[ 'root' ][ index ]
        dst_fn = cloud_hexmap[ 'fname' ][ index ] 
        dst_hex = cloud_hexmap[ 'hex' ][ index ]
        
        common_root_fn = path.join( dst_root, dst_fn )
        fpath_on_cloud = path.join( cloud, common_root_fn )               
        )
        expected_path_on_client = path.join( client, common_root_fn )
        
        
        # same hex & path > PASS
        if dst_hex in client_hexmap[ 'hex' ] and path.exists( expected_path_on_client ) and path.exists( fpath_on_cloud ):
            
            flag_hexxed( dst_hex )        
            log_it( logger, f"\nPASS { fpath_on_cloud }\n" )
            
                
        # same hex & different path > RENAME
        elif dst_hex in client_hexmap[ 'hex' ] and not path.exists( expected_path_on_client ) and dst_fn in client_hexmap[ 'fname' ]  and path.exists( fpath_on_cloud ): 
        
            rename_it( logger, dst_hex, fpath_on_cloud ) 
            
       
       # no hex match & same path > REPLACE
        elif path.exists( expected_path_on_client ) and path.exists( fpath_on_cloud ):
            
            flag_hexxed( ( dst_root, dst_fn ), action = 'REPLACE' )
            replace_it( logger, expected_path_on_client, fpath_on_cloud )


        # no hex match & same unique filename but different root > RENAME
        elif not path.exists( expected_path_on_client ) and path.exists( fpath_on_cloud ) and dst_root not in client_hexmap[ 'root' ] and dst_fn in client_hexmap[ 'fname' ] and client_hexmap[ 'fname' ].count( dst_fn ) == 1:
        
            flag_hexxed( dst_fn, action = 'RENAME' )           
            rename_it( logger, dst_root, fpath_on_cloud )

                
        #  no hex match & no path match > DELETE
        elif path.exists( fpath_on_cloud ) and not path.exists( expected_path_on_client ) and dst_root not in client_hexmap[ 'root' ] and dst_fn not in client_hexmap[ 'fname' ]:
        
            remove_it( logger, fpath_on_cloud )
            
    # hexmap > tree[ cloud ] > removable_dir set() > dir_to_rm > obsolete_dirs
    return dir_to_rm


def full_dump_to_cloud( logger ):

    global client, cloud
    
    log_it( logger, f"\n\n\nSTARTING FULL SYNC\n\n" )
    
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
            
    log_it( logger, f"\n\n\nFINISHED FULL SYNC\n\n" )
    log_it( logger, f"{ 80 * '~'\n\n" )
    
    return


def selective_dump_to_cloud( logger ):

    global client_hexmap, cloud
       
    for q in range( len( client_hexmap[ 'hex' ] ) ):        
        # unhandled files are not flagged
        if client_hexmap[ 'flag' ][ q ] == None:
            try:
                # validate common_root on cloud
                client_root = client_hexmap[ 'root '][ q ]
                client_file = client_hexmap[ 'fname' ][ q ]
                
                src = path.join( client, client_root, client_file )                      
                dst = path.join( cloud, client_root, client_file )
                
                log_it( logger, f"\nADDING {dst} from {src}\n" )
                copy2( src, dst )
                client_hexmap[ 'flag' ][ q ] = 'Z'
                log_it( logger, "DONE\n" )
                
            except Exception as X:
                log_it( logger, f"{X}\n")
    return
    

def one_way_sync( logger ):
# triggered by main if hexmap diff
    
    global client, cloud, client_hexmap, cloud_hexmap, tree
    
    sync_start = datetime.now()
     
    log_it( logger, f"\n\n\nStarting sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n\n" )
    
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
        # both tree sets have only the common root extracted during hexmap generation
        for client_dir in tree[ client ]:
        
            cloud_dirpath = path.join( cloud, client_dir )
            
            if client_dir not in tree[ cloud ] and not path.exists( cloud_dirpath ):
                
                try:
                    log_it( logger, f"\n\nMaking new DIR: {cloud_dirpath}\n" )
                    mkdir( cloud_dirpath )
                    log_it( logger, "DONE\n" )
                    
                except Exception as X:                
                    log_it( logger, X, )
                    # build upper tree
                    mk_upper_dircloud( cloud_dirpath, logger )
                
        # cleanup on cloud storage
        obsolete_dirs = diff_hex( logger )
        
        # remove empty dirs after file cleanup
        log_it( logger, "\n\n\nREMOVING OBSOLETE DIRECTORIES\n\n" )
        for obsolete_dir in obsolete_dirs:
            rm_obsolete_dir( obsolete_dir, logger)
            
        # dump left-overs from client
        log_it( logger, f"\n\n\nDUMPING REMAINING SOURCE ITEMS\n\n" )
        selective_dump_to_cloud( logger )
    
    sync_finish = datetime.now()
    
    log_it( logger, f"Finished sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
    
    return ( sync_finish - sync_start ).seconds

    
def main( log_path_set=False ):    
    
    global client, cloud, client_hexmap, log_path, interval    
    
    # log file timeframe
    ymd_now = datetime.now().strftime( '%Y-%m-%d' )    
    
    # setup log file
    if not log_path_set:
        log_path_set = setup_log_path( log_path )
    
    logger = new_log_file( log_path, ymd_now )
       
    # sync folders
    sync_duration = one_way_sync( logger )    
    
    # determine last sync duration to cut from the interval sleep time until next sync 
    sync_delta = sync_duration - interval
    
    log_it( logger, f"\nLast sync took { sync_duration } seconds.\n\n" )
    
    # close log file to allow reading the last sync events
    logger.close()
    
    # reset hexmap & tree
    reset_global()
     
    if sync_delta <= 0:
        sleep( interval )
        main( log_path_set )
    else:
        sleep( sync_delta )
        main( log_path_set )
    
    
if __name__ == '__main__':
    main()
