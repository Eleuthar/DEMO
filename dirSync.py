from getopt import getopt
from hashlib import md5
from sys import argv
from os import walk, listdir, path, mkdir, replace, remove, rmdir, rename, strerror
import errno
from shutil import copytree, copy2
from datetime import datetime
from time import sleep
from copy import deepcopy

from pdb import set_trace



__doc__ =  '''
    Usage: python dirSync.py -s|--source_path <source_path> -d|--destination_path <destination_path> -i|--interval <integer><S||M||H||D> -l|--log <log_path>
    
    S = SECONDS
    M = MINUTES
    H = HOURS
    D = DAYS
    
    Example for synchronizing every 5 minutes with absolute path:    
    $ python dirSync.py -s "C:\\Users\\MrRobot\\Documents\\Homework" -d "C:\\Users\\MrRobot\\Downloads\\VEEAM_CLOUD\\Homework" -i 5M -l "C:\\Program Files\\VEEAM\\logs"
    
    Example for synchronizing every 5 seconds with relative path:    
    $ python dirSync.py -s ..\\..\\..\\INFOSEC -d .\\INFOSEC -i 5S -l .\\logz
    
    !!! On Windows the script must be executed with Command Prompt, as Windows PowerShell does not handle well relative paths
       
    '''    

# global variables
client = None
cloud = None
interval = None
log_path = None
timeframe = { 
    "S" : 1,
    "M" : 60,
    "H" : 3600,
    "D" : 86400
}    
# interval translated into seconds
interval 
client_hexmap = { }
cloud_hexmap = { }
tree = {}


# opts = [long form], args = [short form]
opts, args = getopt( argv[1:], "s:d:i:l:",  [ "source_path=" , "destination_path=", "interval=", "log=" ] )

try:
    for opt, arg in opts + args:
        if opt in [ "-s", "--source_path" ]:
            client = path.realpath( arg ) if arg[-1] != '"' else arg[:-1]
        
        elif opt in [ "-d", "--destination_path" ]:
            cloud = path.realpath( arg ) if arg[-1] != '"' else arg[:-1]
        
        elif opt in [ "-i", "--interval" ]:
            quantifier = arg[:-1]
            unit = arg[-1].upper()
            
            if unit in [ 'S','M','H','D' ] and quantifier.isdigit():
                interval = int( quantifier ) * timeframe[ unit ]
            else:            
                print( __doc__ )
                exit()
            
        elif opt in [ "-l", "--log" ]:
            log_path = path.realpath( arg ) if arg[-1] != '"' else arg[:-1]
            
        else:
            print( X, "\n\n", __doc__ )
            exit()

except Exception as X:
    print( X, "\n\n", __doc__ )
    exit()    
        
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
    
    logger.write( f'\n\n\nHEXMAP for "{target}"' )
    logger.write(f"\n{ 60 * '-'}\n")
    
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
            
            logger.write( f"{ path.join( root, fname ) }\n" )
            logger.write( f"{hx}\n" )
            logger.write(f"{ 60 * '-'}\n")
            
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
            log_it( logger, f"\n{upper_path} - OK\n" )
            return
            
        except Exception as X:
            log_it( logger, f"{X}\n\n\nAttempting to create upper directory\n")
            mk_upper_dircloud( upper, logger )
    else:                    
        return

   
def get_removable_dir( tree, logger ):
# applicable only for cloud directories against client
    global cloud
    removable_dir = set( )
    log_it( logger, "\n\nPREPARING DIRECTORIES FOR REMOVAL\n```````````````````````````````````" )
    
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
# OK after file cleanup
    global cloud
    
    try:
        rmdir( root )
        log_it( logger, f"Removed directory { root }\n" )
        
    except Exception as X:
        # is already deleted, content is already deleted
        log_it( logger, f"{ X }\n" )
        
    return
 

def flag_hexmap( logger, prop, action ):
# actual sync happens here
    
    global client_hexmap, client, cloud
    
    for z in range( len(client_hexmap['hex']) ):
        
        # prop = ( dst_hex, fpath_on_cloud )
        if action == 'RENAME' and prop[0] == client_hexmap[ 'hex' ][ z ]:
            # extract the corresponding full path on client side    
            new_fname = client_hexmap[ 'fname' ][ z ]            
            new_root = client_hexmap[ 'root' ][ z ]
            new_path = path.join( cloud, new_root, new_fname )
            try:
                rename( prop[1], new_path )
                client_hexmap[ 'flag' ][ z ] = 'Z'
                log_it( logger, f"RENAMED {prop[1]} to {new_path}" )
            except Exception as X:
                log_it( logger, f"{X}\n" )
                
        
        # prop is ( dst_root, dst_fn )
        elif action == 'REPLACE' and prop[0] == client_hexmap[ 'root' ][ z ] and prop[1] == client_hexmap[ 'fname' ][ z ]:            
            try:
                fpath_on_cloud = path.join( cloud, prop[0], prop[1] )
                fpath_on_client = path.join( client, prop[0], prop[1] )
                remove( fpath_on_cloud )
                copy2( fpath_on_client, fpath_on_cloud )
                client_hexmap[ 'flag' ][ z ] = 'Z'
                log_it( logger, f"REPLACED {prop[1]} to {fpath_on_client}")
            
            except OSError as XX:
                if XX.errno == errno.ENOSPC:
                    log_it( logger, f"{strerror( XX.errno )}\n\n" )
                    exit()
            
            except Exception as X:
                log_it( logger, f"{X}\n\n" )
                
                
        # hex & path matching, prop is dst_hex
        elif action == 'PASS' and prop[0] == client_hexmap[ 'hex' ][ z ]:
            client_hexmap[ 'flag' ][ z ] = 'Z'
            log_it( logger, f"PASS {prop[1]}\n" )            
        
    return


def diff_hex( logger ):
    # start from the client deepest root    
    # if root not in cloud ['root'], review content recursively to remove\move\keep\update, then add to set for final cleanup
    
    global client, cloud, client_hexmap, cloud_hexmap, tree
    
    dir_to_rm = get_removable_dir( tree, logger )
    
    log_it( logger, "TARGET DIRECTORY CLEANUP\n````````````````````````" )
    
    # cloud-side cleanup
    for hx_tgt in reversed( cloud_hexmap['hex'] ):
        
        index = cloud_hexmap['hex'].index( hx_tgt )
        
        dst_root = cloud_hexmap[ 'root' ][ index ]
        dst_fn = cloud_hexmap[ 'fname' ][ index ] 
        dst_hex = cloud_hexmap[ 'hex' ][ index ]
        
        common_root_fn = path.join( dst_root, dst_fn )
        fpath_on_cloud = path.join( cloud, common_root_fn )
        expected_path_on_client = path.join( client, common_root_fn )
        
        
        # same hex & path > PASS
        if dst_hex in client_hexmap[ 'hex' ] and path.exists( expected_path_on_client ) and path.exists( fpath_on_cloud ):
            
            flag_hexmap(logger, ( dst_hex, fpath_on_cloud ), action = 'PASS' )            
            
            
        # same hex & different path > RENAME
        elif dst_hex in client_hexmap[ 'hex' ] and not path.exists( expected_path_on_client ) and dst_fn in client_hexmap[ 'fname' ]  and path.exists( fpath_on_cloud ):
        
            flag_hexmap( logger, ( dst_hex, fpath_on_cloud ), action = 'RENAME' )
            
            
       # no hex match & same path + fname > REPLACE
        elif path.exists( expected_path_on_client ) and path.exists( fpath_on_cloud ):
            
            flag_hexmap( logger, ( dst_root, dst_fn ), action = 'REPLACE' )
            
        
        #  no hex match & no path match > DELETE
        elif path.exists( fpath_on_cloud ) and not path.exists( expected_path_on_client ) and dst_root not in client_hexmap[ 'root' ] and dst_fn not in client_hexmap[ 'fname' ]:
        
            try:                
                remove( fpath_on_cloud )               
                log_it( logger, f"REMOVED {fpath_on_cloud}" )
                
            except Exception as X:
                log_it( logger, f"{X}\n\n" )
                
            
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
            
        except OSError as XX:
                if XX.errno == errno.ENOSPC:
                    log_it( logger, f"{strerror( XX.errno )}\n\n" )
                    exit()
            
        except Exception as X:
            log_it( logger,  f"Error: { X }\n" )
            
    log_it( logger, f"\n\nFINISHED FULL SYNC\n\n" )
    
    return


def selective_dump_to_cloud( logger ):

    global client_hexmap, cloud
       
    for q in range( len( client_hexmap[ 'hex' ] ) ):        
        # unhandled files are not flagged
        if client_hexmap[ 'flag' ][ q ] == None:
            try:
                # validate common_root on cloud
                client_root = client_hexmap[ 'root' ][ q ]
                client_file = client_hexmap[ 'fname' ][ q ]
                src = path.join( client, client_root, client_file )
                dst = path.join( cloud, client_root, client_file )
                
                if not path.exists( dst ):
                    copy2( src, dst )
                    client_hexmap[ 'flag' ][ q ] = 'Z'
                    log_it( logger, f"{path.join( client_root, client_file )}\n" )                
                else:
                    log_it( logger, f"PASS {dst}\n" )
                    
            except OSError as XX:
                if XX.errno == errno.ENOSPC:
                    log_it( logger, f"{strerror( XX.errno )}\n\n" )
                    exit()
                
            except Exception as X:
                log_it( logger, f"{X}\n" )
    return
    

def one_way_sync( logger ):
# triggered by main if hexmap diff
    
    global client, cloud, client_hexmap, cloud_hexmap, tree
    
    sync_start = datetime.now()
     
    log_it( logger, f"\nStarting sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n\n" )
    
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
        log_it( logger, "UPDATING DESTINATION TREE\n`````````````````````\n" )
        for client_dir in tree[ client ]:
        
            cloud_dirpath = path.join( cloud, client_dir )
            
            if client_dir not in tree[ cloud ] and not path.exists( cloud_dirpath ):
                
                try:
                    mkdir( cloud_dirpath )
                    log_it( logger, f"{cloud_dirpath}" 
                    
                except Exception as X:                
                    log_it( logger, f"{X}\n" )
                    # build upper tree
                    mk_upper_dircloud( cloud_dirpath, logger )
                
        # cleanup on cloud storage
        obsolete_dirs = diff_hex( logger )
        
        # remove empty dirs after file cleanup
        log_it( logger, "\n\nREMOVING OBSOLETE DIRECTORIES\n``````````````````````````````" )
        for obsolete_dir in obsolete_dirs:
            rm_obsolete_dir( obsolete_dir, logger)
            
        # dump left-overs from client
        log_it( logger, "\n\nADDING NEW CONTENT\n```````````````````" )
        selective_dump_to_cloud( logger )
    
    sync_finish = datetime.now()
    
    log_it( logger, f"\nFinished sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
    
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
    sync_delta = interval - sync_duration
    
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
    # On lack of disk space the program will exit
    main()
