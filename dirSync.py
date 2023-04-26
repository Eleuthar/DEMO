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
logger = None
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


def log_it( log_item ):
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


def generate_hexmap( target ):
    global tree    
    # hexmap flag initalized with None, later marked with "Z"
    # used only for client during diff_hex
    hexmap = {
        'root': [],
        'fname': [], 
        'hex': [],
        'flag' : []
    }    
    log_it( f'\n\n\n\nHEXMAP for base root "{target}"\n{ 120 * "-"}' )    
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
            log_it( f"\n{ path.join( root, fname ) }" )
            log_it( f"\n{hx}" )
            log_it( f"\n{ 120 * '-'}\n" )            
    return hexmap
    

def mk_upper_dir( root ):
    global cloud    
    
    current_dir = path.basename( root )
     
    # remove ending "\\" or "/"
    upper_dir = root[ : -len( current_dir ) ][: -1]
        
    # '' is base root, meaning the basename has no upper directory to mirror the client
    if upper_dir == '':
        upper_dir = current_dir
    
    upper_path = path.join( cloud, upper_dir )
    
    if not path.exists( upper_path ):
        try:
            mkdir( upper_path )
            log_it( f"\nCreated directory {upper_dir}\n" )
            mkdir( root )
            log_it( f"\nCreated directory {root}\n" )
            return
            
        except Exception as X:
            log_it( f"{X}" )
    else:                    
        return
        

def new_dir_cloud():

    global tree, cloud, client
    
    new_dir_counter = 0

    for client_dir in tree[ client ]:     
        cloud_dirpath = path.join( cloud, client_dir )            
        
        if not path.exists( cloud_dirpath ):      
            try:
                mkdir( cloud_dirpath )
                log_it( f"\n{cloud_dirpath} - OK" )
                new_dir_counter += 1
                
            except Exception as XX:
                if XX.errno == errno.ENOENT:
                    # build upper tree
                    mk_upper_dir( cloud_dirpath )
                    new_dir_counter += 1
    
    return new_dir_counter
    
   
def rm_obsolete_dir( ):
# applicable only for cloud directories against client
    global tree, client, cloud
    
    rm_counter = 0
    set_trace()
    
    for folder in tree[ cloud ]:        
        client_path = path.join( client, folder )
        
        if client_path != client and not path.exists( client_path ):
            try:                
                rmdir( path.join( cloud, folder ) )
                rm_counter += 1
                log_it( f"\nRemoved directory { root}\\\n" )
            
            except Exception as X:            
                # is already deleted, content is already deleted
                log_it( f"\n{ X }\n" )
        
    return rm_counter


def diff_hex( ):
# iterate each cloud file against client and mark handled for later dump
    global client, cloud, client_hexmap, cloud_hexmap
    
    diff_counter = 0
    
    # cloud-side cleanup
    for j in range( len( cloud_hexmap[ 'hex' ] ) ):
        
        dst_root = cloud_hexmap[ 'root' ][ j ]
        dst_fname = cloud_hexmap[ 'fname' ][ j ]
        dst_hex = cloud_hexmap[ 'hex' ][ j ]        
        common_root = path.join( dst_root, dst_fname )
        fpath_on_cloud = path.join( cloud, common_root )        
        expected_path_on_client = path.join( client, common_root )        
        
        set_trace()
        # hex match
        if dst_hex in client_hexmap[ 'hex' ]:            
                        
            # client has at least 2 duplicates
            if client_hexmap[ 'hex' ].count( dst_hex ) > 1:
            
                log_it( f"Handling mutiple duplicates for {common_root}\n" )
                
                # gather the index for each duplicate file of both endpoints
                #x = 0
                ndx_src = [ x for x in range(len( client_hexmap[ 'hex' ] ) ) if client_hexmap[ 'hex' ][ x ] == dst_hex ]                
                #x = 0
                ndx_dst = [ x for x in range(len( cloud_hexmap[ 'hex' ] ) ) if cloud_hexmap[ 'hex' ][ x ] == dst_hex ]
                
                max_len = max( len( ndx_dst ), len( ndx_src ) )
                
                # 1-1 renaming as a refresher, since they are all identical. Otherwise the logic would be way too complicated to parse something identical in content, except probably for name                                
                try:
                    x = 0
                    for x in range( max_len ):
                        
                        # check if the path to be renamed is on client
                        expected_path_on_client = path.join( client, cloud_hexmap[ 'root' ][ ndx_dst[x] ], cloud_hexmap[ 'fname' ][ ndx_dst[x] ] )                        
                        
                        dst_path = path.join( cloud, cloud_hexmap[ 'root' ][ ndx_dst[x] ], cloud_hexmap[ 'fname' ][ ndx_dst[x] ] )
                        
                        # use the common root from client
                        src_path = path.join( cloud, client_hexmap[ 'root' ][ ndx_src[x] ], client_hexmap[ 'fname' ][ ndx_src[x] ] )
                        
                        # rename if the current cloud path should not exist on client
                        if not path.exists( expected_path_on_client ):                        
                            rename( src_path, dst_path )
                        
                        cloud_hexmap[ 'flag' ][ ndx_src[x] ] = 'Z'
                        client_hexmap[ 'flag' ][ ndx_dst[x] ] = 'Z'
                        
                        ndx_src.remove( ndx_src[x] )
                        ndx_dst.remove( ndx_dst[x] )
                        x -= 1
                        
                # one of the lists is bigger by at least 1 and the other is now empty
                except IndexError as XX:
                    # if cloud is 0, then client is the bigger list; the rest of it's content will be dumped during selective_dump_to_cloud()
                    if len( ndx_dst ) == 0:
                        continue                    
                    # remove the remaining obsolete cloud duplicates
                    else:
                        for ndx in ndx_dst:
                            remove( path.join( cloud, cloud_hexmap[ 'root' ][ ndx ], cloud_hexmap[ 'fname' ][ ndx ] ) )
                        continue
                        
                except Exception as X:
                    log_it( f"\n{X}\n")
                    
                # all duplicates' names has been refreshed
                if (len( ndx_dst ) == 0 and len( ndx_src ) == 0) or len( ndx_dst ) == 0:
                    continue
                    
            
            # unique hex match
            elif client_hexmap[ 'hex' ].count( dst_hex ) == 1:
               
                index = client_hexmap[ 'hex' ].index( dst_hex )
                client_hexmap[ 'flag' ][ index ] = 'Z'
                
                # PASS <<<<< cloud path matching
                if path.exists( expected_path_on_client ):    
                    log_it( f"\nPASS {common_root}\n" )
                
                # RENAME <<<<< path not matching
                else:
                    new_path = path.join( cloud, client_hexmap[ 'root' ][ index ], client_hexmap[ 'fname' ][ index ] )
                    rename( new_path, fpath_on_cloud )
                    log_it( f"RENAMED {fpath_on_cloud} TO {new_path}\n" )
                
             
        # no hex match
        else:
            try:
                remove( fpath_on_cloud )
                diff_counter += 1
                log_it( f"\nDELETED {fpath_on_cloud}\n" )
                
            except Exception as X:
                log_it( f"{X}\n" )
                
            finally:
                continue 
                
    return diff_counter


def full_dump_to_cloud( ):
    global client, cloud
    
    for item in listdir(client):
        try:
            src = path.join( client, item )
            dst = path.join( cloud, item )
            
            if path.isdir( src ):                
                copytree( src, dst )
            else:
                copy2( src, dst )
                
            log_it( f"Copied { item }\n" )
            
        except OSError as XX:
                if XX.errno == errno.ENOSPC:
                    log_it( f"{strerror( XX.errno )}\n" )
                    exit()
            
        except Exception as X:
            log_it(  f"Error: { X }\n" )
            
    return


def selective_dump_to_cloud( ):
# directories have been already created
# potential conflict handled in the previous stage
# dumping remaining unflagged files
    set_trace()
    global client_hexmap, cloud
       
    for q in range( len( client_hexmap[ 'hex' ] ) ):
    
        if client_hexmap[ 'flag' ] == None:
       
            root = client_hexmap[ 'root' ][ q ]
            fname = client_hexmap[ 'fname' ][ q ]
            src = path.join( client, root, fname)
            dst = path.join( cloud, root, fname)
            
            if not path.exists( dst ) and path.exists( src ):
                try:
                    copy2( src, dst )
                    log_it( f"{dst}\n" )                
                    
                except OSError as XX:
                    if XX.errno == errno.ENOSPC:
                        log_it( f"{strerror( XX.errno )}\n" )
                        exit()
                    
                except Exception as X:
                    log_it( f"{X}\n" )
    return
    

def one_way_sync( ):
# triggered by main if hexmap diff
    
    global client, cloud, client_hexmap, cloud_hexmap, tree
    
    sync_start = datetime.now()
     
    log_it( f"Starting sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
    
    # get the source directory hash map
    client_hexmap = generate_hexmap( client )
    
    # initial full dump to cloud storage
    if len( listdir( cloud ) ) == 0 and len( listdir( client ) ) != 0:
        log_it( f"\nFULL SYNC\n" )
        full_dump_to_cloud( )
        log_it( f"\nFINISHED FULL SYNC\n\n" )
        
    else:
        # get the destination directory hash map
        cloud_hexmap = generate_hexmap( cloud )
        
        # both tree sets have only the common root extracted during hexmap generation
        log_it( "\n\n\n\nUPDATING DESTINATION TREE\n`````````````````````````" )
        
        new_dir_counter = new_dir_cloud()
        
        if new_dir_counter == 0:
            log_it( "No action taken\n" )
        
                
        # cleanup on cloud storage
        log_it( "\n\n\nFILE CLEANUP\n````````````\n" )
        
        cleanup_counter = diff_hex()
        
        if cleanup_counter == 0:        
            log_it( "No action taken\n" )
        
        
        # remove dirs after file cleanup
        log_it( "\n\n\nREMOVING OBSOLETE DIRECTORIES\n``````````````````````````````\n" )
        
        rm_dir_counter = rm_obsolete_dir()
    
        if rm_dir_counter == 0:
            log_it( "No action taken\n" )
            
            
        # dump left-overs from client
        log_it( "\n\nADDING NEW CONTENT\n```````````````````\n" )
        
        dump_counter = selective_dump_to_cloud( )
        
        if dump_counter == 0:
                log_it( "No action taken\n" )
    
    sync_finish = datetime.now()
    
    log_it( f"\n\n\nFinished sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
    
    return ( sync_finish - sync_start ).seconds

    
def main( log_path_set=False ):    
    
    global client, cloud, client_hexmap, interval, log_path, logger
    
    # log file timeframe
    ymd_now = datetime.now().strftime( '%Y-%m-%d' )    
    
    # setup log file
    if not log_path_set:
        log_path_set = setup_log_path( log_path )
    
    logger = new_log_file( log_path, ymd_now )
       
    # sync folders
    sync_duration = one_way_sync( )    
    
    # determine last sync duration to cut from the interval sleep time until next sync 
    sync_delta = interval - sync_duration
    
    log_it( f"\nLast sync took { sync_duration } seconds.\n\n\n{80 * '~'}\n\n\n\n\n\n" )
    
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
