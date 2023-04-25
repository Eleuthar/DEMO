from getopt import getopt
from hashlib import md5
from sys import argv
from os import walk, listdir, path, mkdir, remove, rmdir, rename, strerror
import errno
from shutil import copytree, copy2
from datetime import datetime
from time import sleep

from pdb import set_trace



__doc__ =  '''
    Usage: python dirSync.py -s|--source_path <source_path> -d|--destination_path <destination_path> -i|--interval <integer><S||M||H||D> -l|--log <log_path>
    
    S = SECONDS
    M = MINUTES
    H = HOURS
    D = DAYS
    
    Example for synchronizing every 5 minutes with absolute path:    
    $ python dirSync.py -s "C:\\Users\\MrRobot\\Documents\\Homework" -d "C:\\Users\\MrRobot\\Downloads\\VEEAM_CLOUD\\Homework" -i 5M -l "C:\\Program Files\\VEEAM\\logs"
    
    Example for synchronizing every 5 minutes with relative path:    
    $ python dirSync.py -s ..\\..\\..\\INFOSEC -d .\\INFOSEC -i 5m -l .\\logz    
    
    !!! On Windows the script must be executed with Command Prompt, as Windows PowerShell does not handle well relative paths
    !!! Do not end the source & destination path with single backslash "\\" otherwise Windows will split the path invalidating it
       
    '''

if len( argv ) == 1:
    print( __doc__ )
    exit()


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
            print("\n\n", __doc__ )
            exit()

except Exception as X:
    print( X, "\n\n", __doc__ )
    exit()    
    
tree[ client ] = set()
tree[ cloud ] = set()    

    
def setup_log_path( log_path ):
# implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
    
    print( f'Validating log directory: "{ log_path }"\n' )
   
    # folder check
    if not path.exists( log_path ):        
        dir_name = path.basename( log_path )
        parent = log_path[ : -len( dir_name ) ][: -1]
        
        print( f'Directory "{dir_name}" does not exist. Will create it if parent directory "{parent}\\" is valid.\n' )
        
        # upper folder check        
        if not path.exists( parent ):                
            print( f"Parent directory {parent} does not exist either.\nPlease use an existing directory to store the logs." )
            exit()        
        else:
            print( f"Creating {dir_name} under {parent}\n" )
            mkdir( log_path )
            return True   
    else:        
        print( f"Saving logs in {log_path}\n" )
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
    
    log_it( logger, f'\n\n\nHEXMAP for "{target}"\n{ 60 * "-"}\n' )
    
    for directory in walk( target ):    
        # ( 0=dirname, 1=[folder basenames], 2=[files] )
        # client = C:\Downloads\Pirated_MP3\<common root>
        # cloud = C:\Backup\Pirated_Music\<common root>	
        root = directory[0][ len( target ) : ]

        # remove beginning "\\" or "/" else join will fail
        root = root.removeprefix('\\') if '\\' in root else root.removeprefix('/')
        
        # get a full list of all folders empty or not
        tree[ target ].add( root )
        
        for fname in directory[2]:
            hexmap[ 'root' ].append( root )
            hexmap[ 'fname' ].append( fname )
            hx = generate_file_hex( target, root, fname )
            hexmap[ 'hex' ].append( hx )
            hexmap[ 'flag' ].append(None)
            
            log_it( logger, f"{ path.join( root, fname ) }\n" )
            log_it( logger, f"{hx}\n" )
            log_it( logger, f"{ 60 * '-'}\n" )
            
    return hexmap
    

def mk_upper_dir( root, logger ):

    global cloud
    log_it( logger, f"Attempting to create directory {root}\n" )
    current_dir = path.basename( root )
     
    # remove ending "\\" or "/"
    upper_root = root[ : -len( current_dir ) ][: -1]
        
    # '' is base root, meaning the basename has no upper directory to mirror the client
    if upper_root == '':
        upper_root = current_dir
    
    upper_path = path.join( cloud, upper_root )
    
    if not path.exists( upper_path ):
        try:
            mkdir( upper_path )
            log_it( logger, f"Created parent {upper_root}\n" )
            mkdir( root )
            log_it( logger, f"Created {root}\n" )
            return
            
        except OSError as XX:
            if XX.errno == errno.ENOENT:
                log_it( logger, f"Parent {upper_root} does not exist also.\n")
                mk_upper_dir( upper_path, logger )
            
        except Exception as X:
            log_it( logger, f"{X}" )
    else:                    
        return

   
def rm_obsolete_dir( logger ):
# applicable only for cloud directories against client
    global tree, client, cloud
        
    for folder in tree[ cloud ]:
        client_root = path.join( client, folder )
        
        if client_root != client and not path.exists( client_root ):            
            try:
                rmdir( path.join( cloud, folder ) )
                log_it( logger, f"Removed directory { root }\\ \n" )
            
            except Exception as X:            
                # is already deleted, content is already deleted
                log_it( logger, f"{ X }\n" )
        
    return


def diff_hex( logger ):
# iterate each cloud file against client and mark handled for later dump
    global client, cloud, client_hexmap, cloud_hexmap
    
    # cloud-side cleanup
    for j in range( len( cloud_hexmap[ 'hex' ] ) ):
        
        dst_root = cloud_hexmap[ 'root' ][ j ]
        dst_fname = cloud_hexmap[ 'fname' ][ j ]
        dst_hex = cloud_hexmap[ 'hex' ][ j ]        
        common_root = path.join( dst_root, dst_fname )
        fpath_on_cloud = path.join( cloud, common_root )        
        expected_path_on_client = path.join( client, common_root )        
        
        set_trace()        
        
        # same hex & path > PASS
        if dst_hex in client_hexmap[ 'hex' ] and path.exists( expected_path_on_client ):
        
            for z in range( len( client_hexmap[ 'hex' ] ) ):
            
                if client_hexmap[ 'flag' ][ z ] == None and client_hexmap[ 'hex' ][ z ] == dst_hex and client_hexmap[ 'fname' ] == dst_fname and client_hexmap[ 'root' ][ z ] == dst_root:            
                    
                    client_hexmap[ 'flag' ][ z ] = 'Z'
                    log_it( logger, f"PASS {common_root}\n" )
                    break
                        
        # same hex & different path > RENAME
        elif dst_hex in client_hexmap[ 'hex' ] and not path.exists( expected_path_on_client ):
        
            for z in range( len( client_hexmap[ 'hex' ] ) ):
                
                # same fname but different root > RENAME
                if client_hexmap[ 'flag' ][ z ] == None and client_hexmap[ 'hex' ][ z ] == dst_hex and ( client_hexmap[ 'fname' ] != dst_fname or client_hexmap[ 'root' ][ z ] != dst_root ):

                    new_root = client_hexmap[ 'root' ][ z ]
                    new_fname = client_hexmap[ 'fname' ][ z ]
                    new_path = path.join( cloud, new_root, new_fname )
                    
                    try:
                        rename( fpath_on_cloud, new_path )
                        client_hexmap[ 'flag' ][ z ] = 'Z'
                        log_it( logger, f"RENAMED {fpath_on_cloud} to {new_path}" )
                        
                    except Exception as X:
                        log_it( logger, f"{X}\n" )
                        
                    finally:
                        break            
        
        # no hex match > DELETE
        elif dst_hex not in client_hexmap[ 'hex' ]:
            try:
                remove( fpath_on_cloud )           
                log_it( logger, f"UPDATED {fpath_on_cloud}\n" )
                
            except Exception as X:
                log_it( logger, f"{X}\n" )
                
            finally:
                break                
    return


def full_dump_to_cloud( logger ):
    global client, cloud
    
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
                    log_it( logger, f"{strerror( XX.errno )}\n" )
                    exit()
            
        except Exception as X:
            log_it( logger,  f"Error: { X }\n" )
            
    return


def selective_dump_to_cloud( logger ):
# directories have been already created
# potential conflict handled in the previous stage
# dumping remaining unflagged files

    global client_hexmap, cloud
       
    for q in range( len( client_hexmap[ 'hex' ] ) ):
    
        if client_hexmap[ 'flag' ] == None:
            root = client_hexmap[ 'root' ][ q ]
            fname = client_hexmap[ 'fname' ][ q ]
            src = path.join( client, root, fname)
            dst = path.join( cloud, root, fname)            

            try:
                copy2( src, dst )
                log_it( logger, f"{path.join( root, fname )}\n" )                
                
            except OSError as XX:
                if XX.errno == errno.ENOSPC:
                    log_it( logger, f"{strerror( XX.errno )}\n" )
                    exit()
                
            except Exception as X:
                log_it( logger, f"{X}\n" )
    return
    

def one_way_sync( logger ):
# triggered by main if hexmap diff
    
    global client, cloud, client_hexmap, cloud_hexmap, tree
    
    sync_start = datetime.now()
     
    log_it( logger, f"Starting sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n\n" )
    
    # get the source directory hash map
    client_hexmap = generate_hexmap( client, logger )
    
    # initial full dump to cloud storage
    if len( listdir( cloud ) ) == 0 and len( listdir( client ) ) != 0:
        log_it( logger, f"FULL SYNC\n" )
        full_dump_to_cloud( logger )
        log_it( logger, f"\nFINISHED FULL SYNC\n\n" )
        
    else:
        # get the destination directory hash map
        cloud_hexmap = generate_hexmap( cloud, logger )
        
        # both tree sets have only the common root extracted during hexmap generation
        log_it( logger, "\nUPDATING DESTINATION TREE\n`````````````````````````" )
        
        for client_dir in tree[ client ]:     
            cloud_dirpath = path.join( cloud, client_dir )
            
            set_trace()
            
            if not path.exists( cloud_dirpath ):
                try:
                    mkdir( cloud_dirpath )
                    log_it( logger, f"\n{cloud_dirpath} - OK\n" )
                    
                except OSError as XX:
                    if XX.errno == errno.ENOENT:
                        # build upper tree
                        mk_upper_dir( cloud_dirpath, logger )
                
        # cleanup on cloud storage
        log_it( logger, "\n\nFILE CLEANUP\n````````````````" )
        diff_hex( logger )
        
        # remove dirs after file cleanup
        log_it( logger, "\n\nREMOVING OBSOLETE DIRECTORIES\n``````````````````````````````" )
        if len( tree[ cloud ] ) != 0:
            rm_obsolete_dir( logger )
            
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
