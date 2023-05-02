from getopt import getopt
from hashlib import md5
from sys import argv
from os import walk, listdir, path, mkdir, remove, rmdir, rename, strerror
import errno
from shutil import copytree, copy2
from datetime import datetime
from time import sleep



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



class DirSync:

    def __init__( self, client, cloud, interval, log_path ):
        self.client = client
        self.cloud = cloud
        self.interval = interval
        self.log_path = log_path
        self.client_hexmap = { }
        self.cloud_hexmap = { }
        self.tree = { }
        self.tree[ client ] = set()
        self.tree[ cloud ] = set()
        self.logger = None


    def setup_log_path( self ):
    # implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
        
        print( f'Validating log directory: "{ self.log_path }"\n' )
       
        # folder check
        if not path.exists( self.log_path ):        
            dir_name = path.basename( self.log_path )
            parent = self.log_path[ : -len( dir_name ) ][: -1]
            
            print( f'Directory "{dir_name}" does not exist. Will create it if parent directory "{parent}\\" is valid.\n' )
            
            # upper folder check        
            if not path.exists( parent ):                
                print( f"Parent directory {parent} does not exist either.\nPlease use an existing directory to store the logs." )
                exit()        
            else:
                print( f"Creating {dir_name} under {parent}\n" )
                mkdir( self.log_path )
                return True   
        else:        
            print( f"Saving logs in {self.log_path}\n" )
            return True


    def new_log_file( self ):
        # File name format: dirSync_2023-04-18.txt        
        ymd_now = datetime.now().strftime( '%Y-%m-%d' )
        log_name = f"dirSync_{ ymd_now }.txt"
        full_log_path = path.join( self.log_path, log_name )
        log_file = open( full_log_path, 'a', encoding = 'UTF-8' )
        return log_file


    def log_it( self, log_item ):
        print( log_item )
        self.logger.write( log_item )
        return


    def reset_global( self ):        
        self.client_hexmap = { }
        self.cloud_hexmap = { }    
        self.tree[ client ] = set()
        self.tree[ cloud ] = set()
        return
        

    def generate_file_hex( self, target, root, filename, blocksize=8192 ):
        hh = md5()
        with open( path.join( target, root, filename ) , "rb" ) as f:
            while buff := f.read( blocksize ):
                hh.update( buff )
        return hh.hexdigest()


    def generate_hexmap( self, target ):        
        # hexmap flag initalized with None, later marked with "Z"
        # used only for client during diff_hex
        hexmap = {
            'root': [],
            'fname': [], 
            'hex': [],
            'flag' : []
        }    
        
        self.log_it( f'\n\n\n\nHEXMAP for base root "{target}"\n{ 120 * "-"}' )    
        
        for directory in walk( target ):    
            # ( 0=dirname, 1=[folder basenames], 2=[files] )
            # client = C:\Downloads\Pirated_MP3\<common root>
            # cloud = C:\Backup\Pirated_Music\<common root>	

            root = directory[0][ len( target ) : ]
            # remove beginning "\\" or "/" else join will fail
            root = root.removeprefix('\\') if '\\' in root else root.removeprefix('/')        
        
            # get a full list of all folders empty or not
            self.tree[ target ].add( root )
            
            for fname in directory[2]:
                hexmap[ 'root' ].append( root )
                hexmap[ 'fname' ].append( fname )
                hx = self.generate_file_hex( target, root, fname )
                hexmap[ 'hex' ].append( hx )
                hexmap[ 'flag' ].append(None)            
                self.log_it( f"\n{ path.join( root, fname ) }" )
                self.log_it( f"\n{hx}" )
                self.log_it( f"\n{ 120 * '-'}" )            

        return hexmap
        

    def mk_upper_dir( self, root ):
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
                self.log_it( f"\nCreated directory {upper_dir}\n" )
                mkdir( root )
                self.log_it( f"\nCreated directory {root}\n" )
                return
                
            except Exception as X:
                self.log_it( f"{X}" )
        else:                    
            return
            

    def new_dir_cloud( self ):

        new_dir_counter = 0

        for client_dir in self.tree[ client ]:
            cloud_dirpath = path.join( self.cloud, client_dir ) 
            
            if not path.exists( cloud_dirpath ):      
                try:
                    mkdir( cloud_dirpath )
                    self.log_it( f"\n{cloud_dirpath} - OK\n" )
                    new_dir_counter += 1
                    
                except Exception as XX:
                    if XX.errno == errno.ENOENT:
                        # build upper tree
                        mk_upper_dir( cloud_dirpath )
                        new_dir_counter += 1
        
        return new_dir_counter
        
       
    def rm_lower( self, dirpath ):
        if path.exists( dirpath ) and len( listdir( dirpath ) ) != 0:
            
            for dirname in listdir( dirpath ):
                try:
                    child_dir = path.join( dirpath, dirname )
                    rmdir( child_dir )
                    self.log_it( f"\nRemoved directory {child_dir}\\\n" ) 
                
                except OSError:
                    # dir not empty
                    rm_lower( child_dir )
                    self.log_it( f"\nRemoved directory {child_dir}\\\n" )  
            
            # remove parent after clearing its children
            rmdir( dirpath )
            self.log_it( f"\nRemoved directory {dirpath}\\\n" ) 
                

    def rm_obsolete_dir( self ):
    # applicable only for cloud directories against client
                
        rm_counter = 0
        
        for folder in self.tree[ cloud ]:        
            cloud_path_on_client = path.join( self.client, folder )
            
            if cloud_path_on_client != self.client and not path.exists( cloud_path_on_client ):
                try:
                    rm_target = path.join( self.cloud, folder )
                    rmdir( rm_target )
                    rm_counter += 1
                    self.log_it( f"\nRemoved directory {rm_target}\\\n" )
                
                except OSError:
                    # dir not empty
                    rm_lower( rm_target )
                    rm_counter += 1
                    self.log_it( f"\nRemoved directory {rm_target}\\\n" )                
                    
                except Exception as X:            
                    # is already deleted
                    self.log_it( f"\n{ X }\n" )
            
        return rm_counter


    def diff_hex( self ):
    # iterate each cloud file against client and mark handled for later dump
        
        diff_counter = 0
        
        # cloud-side cleanup
        for j in range( len( self.cloud_hexmap[ 'hex' ] ) ):
            
            dst_root = self.cloud_hexmap[ 'root' ][ j ]
            dst_fname = self.cloud_hexmap[ 'fname' ][ j ]
            dst_hex = self.cloud_hexmap[ 'hex' ][ j ]        
            common_root = path.join( dst_root, dst_fname )
            fpath_on_cloud = path.join( self.cloud, common_root )        
            expected_path_on_client = path.join( self.client, common_root )   
            
            # skip flagged items handled during duplication handling scenario 
            if self.cloud_hexmap[ 'flag' ][ j ] != None:
                continue            
            
            # hex match
            # both the client & cloud targets must have not been flagged previously
            if dst_hex in self.client_hexmap[ 'hex' ]:
                            
                # client and\or cloud has at least 2 duplicates
                
                # get the matching client's file index by "client_hexmap[ 'hex' ].index( dst_hex )"
                if ( self.client_hexmap[ 'hex' ].count( dst_hex ) > 1 or self.cloud_hexmap[ 'hex' ].count( dst_hex ) > 1 ):
                
                    self.log_it( f"Handling duplicates for '{common_root}'\n" )
                    
                    # gather the index for each duplicate file of both endpoints
                    ndx_src = [ x for x in range(len( self.client_hexmap[ 'hex' ] ) ) if self.client_hexmap[ 'hex' ][ x ] == dst_hex ]
                    x = 0                
                    
                    ndx_dst = [ x for x in range(len( self.cloud_hexmap[ 'hex' ] ) ) if self.cloud_hexmap[ 'hex' ][ x ] == dst_hex ]
                    x = 0
                    
                    max_len = max( len( ndx_dst ), len( ndx_src ) )
                    
                    # 1-1 name refresher                              
                    try:                   
                        for x in range( max_len ):                    
                            # refresh "x" on each iteration to access the first index of ndx_dst & ndx_src after removing on line 354 
                            x = 0                        
                            
                            # can be invalid on client
                            dst_path_on_client = path.join( self.client, self.cloud_hexmap[ 'root' ][ ndx_dst[x] ], self.cloud_hexmap[ 'fname' ][ ndx_dst[x] ] )                        
                         
                            # current cloud path pending validation
                            dst_path = path.join( self.cloud, self.cloud_hexmap[ 'root' ][ ndx_dst[x] ], self.cloud_hexmap[ 'fname' ][ ndx_dst[x] ] )
                            
                            # client full path to be mirrored if not yet
                            src_path_on_cloud = path.join( self.cloud, self.client_hexmap[ 'root' ][ ndx_src[x] ], self.client_hexmap[ 'fname' ][ ndx_src[x] ] )                                  
                           
                            # for debugging
                            #print(f"\n{dst_path} <<<<<<<<<<<<<< \n{dst_path_on_client} vs \n{src_path_on_cloud}\n")                       
                            
                            # REMOVE <<<<<<<< dst_path is an obsolete duplicate that exists on a different path than "src_path_on_cloud"
                            if not path.exists( dst_path_on_client ) and path.exists( src_path_on_cloud ) and src_path_on_cloud != dst_path:
                                remove( dst_path )
                                diff_counter += 1
                                self.log_it( f"\nDELETED extra duplicate {dst_path}\n" )                            
                                
                            # RENAME <<<<<<<< if the current cloud path does not exist on client
                            elif not path.exists( dst_path_on_client ) and not path.exists( src_path_on_cloud ):
                                rename( dst_path, src_path_on_cloud )
                                diff_counter += 1
                                self.log_it( f"\nRENAMED duplicate {dst_path} TO {src_path_on_cloud}\n" )
                           
                            self.cloud_hexmap[ 'flag' ][ ndx_dst[x] ] = 'Z'
                            self.client_hexmap[ 'flag' ][ ndx_src[x] ] = 'Z'
                            
                            del ndx_src[0], ndx_dst[0]
                                                    
                    # one of the lists is bigger by at least 1 and the other is now empty
                    except IndexError as XX:

                        # the client has the bigger duplicate list of files; the remaining will be dumped now
                        if len( ndx_dst ) == 0:                        
                            for ndx in ndx_src:                            
                                try:
                                    new_path = path.join( self.client_hexmap[ 'root' ][ ndx ], self.client_hexmap[ 'fname' ][ ndx ] )
                                    from_path = path.join( self.client, new_path )
                                    to_path = path.join( self.cloud, new_path )
                                    
                                    if not path.exists( to_path ):
                                        copy2( from_path, to_path )
                                        self.log_it( f"Copied {to_path}\n" )
                                        self.client_hexmap[ 'flag' ][ ndx ] = 'Z'
                                        
                                except Exception as XXX:
                                    self.log_it( f"\n{XXX}\n" )                                   
                            
                        # remove the remaining obsolete cloud duplicates
                        else:
                            for ndx in ndx_dst:
                                try:
                                    remove( path.join( self.cloud, self.cloud_hexmap[ 'root' ][ ndx ], self.cloud_hexmap[ 'fname' ][ ndx ] ) )
                                    self.cloud_hexmap[ 'flag' ][ ndx ] = 'Z'
                                    self.log_it( f"\nDELETED extra duplicate {dst_path}\n" )
                                    
                                except FileNotFoundError:
                                    # the file was previously removed
                                    pass                        
                            
                    except Exception as X:
                        self.log_it( f"\n{X}\n")
                    
                    finally:
                        continue
                        
                
                # unique hex match
                else:               
                    index = self.client_hexmap[ 'hex' ].index( dst_hex )
                    self.client_hexmap[ 'flag' ][ index ] = 'Z'
                    
                    # PASS <<<<< cloud path matching
                    if path.exists( expected_path_on_client ):    
                        self.log_it( f"\nPASS {common_root}\n" )
                    
                    # RENAME <<<<< path not matching
                    else:
                        new_path = path.join( self.cloud, self.client_hexmap[ 'root' ][ index ], self.client_hexmap[ 'fname' ][ index ] )
                        rename( fpath_on_cloud, new_path )
                        diff_counter += 1
                        self.log_it( f"\nRENAMED {fpath_on_cloud} TO {new_path}" )
                    
                 
            # no hex match
            else:
                try:
                    remove( fpath_on_cloud )
                    diff_counter += 1
                    self.log_it( f"\nDELETED {fpath_on_cloud}\n" )
                    
                #except OSError as XX:
                #    if XX.errno == 2:
                #        pass
                    
                except Exception as X:
                    self.log_it( f"{X}\n" )
                    
                finally:
                    continue 
                    
        return diff_counter


    def full_dump_to_cloud( self ):

        for item in listdir( self.client ):
            try:
                src = path.join( self.client, item )
                dst = path.join( self.cloud, item )
                
                if path.isdir( src ):                
                    copytree( src, dst )
                else:
                    copy2( src, dst )
                    
                self.log_it( f"Copied { item }\n" )
                
            except OSError as XX:
                    if XX.errno == errno.ENOSPC:
                        self.log_it( f"{strerror( XX.errno )}\n" )
                        exit()
                
            except Exception as X:
                self.log_it(  f"Error: { X }\n" )
                
        return


    def selective_dump_to_cloud( self ):
    # potential conflict handled in the previous stage as directories have been already created
    # dumping remaining unflagged files
        
        dump_counter = 0
                   
        for q in range( len( self.client_hexmap[ 'hex' ] ) ):
        
            if self.client_hexmap[ 'flag' ][ q ] == None:
           
                root = self.client_hexmap[ 'root' ][ q ]
                fname = self.client_hexmap[ 'fname' ][ q ]
                src = path.join( self.client, root, fname)
                dst = path.join( self.cloud, root, fname)
                
                if not path.exists( dst ) and path.exists( src ):
                    try:
                        copy2( src, dst )
                        self.log_it( f"{dst}\n" ) 
                        dump_counter += 1
                        
                    except OSError as XX:
                        if XX.errno == errno.ENOSPC:
                            self.log_it( f"{strerror( XX.errno )}\n" )
                            exit()
                        
                    except Exception as X:
                        self.log_it( f"{X}\n" )
        
        return dump_counter
        

    def one_way_sync( self ):
    # triggered by main if hexmap diff
        
        sync_start = datetime.now()
         
        self.log_it( f"Starting sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
        
        # get the source directory hash map
        self.client_hexmap = self.generate_hexmap( client )
        
        # initial full dump to cloud storage
        if len( listdir( self.cloud ) ) == 0 and len( listdir( self.client ) ) != 0:
            self.log_it( f"\n\n\nPERFORMING FULL SYNC\n\n" )
            self.full_dump_to_cloud()
        else:
            # get the destination directory hash map
            self.cloud_hexmap = self.generate_hexmap( self.cloud )
            
            # both tree sets have only the common root extracted during hexmap generation
            self.log_it( "\n\n\nUPDATING DESTINATION TREE\n`````````````````````````\n" )
            
            new_dir_counter = self.new_dir_cloud()
            
            if new_dir_counter == 0:
                self.log_it( "\nNo action taken\n" )
            
                    
            # cleanup on cloud storage
            self.log_it( "\n\n\n\nFILE CLEANUP\n````````````\n" )
            
            cleanup_counter = diff_hex()
            
            if cleanup_counter == 0:        
                self.log_it( "\nNo action taken\n" )
            
            
            # remove dirs after file cleanup
            self.log_it( "\n\n\nREMOVING OBSOLETE DIRECTORIES\n``````````````````````````````\n" )
            
            rm_dir_counter = rm_obsolete_dir()
        
            if rm_dir_counter == 0:
                self.log_it( "\nNo action taken\n" )
                
                
            # dump left-overs from client
            self.log_it( "\n\n\nADDING NEW CONTENT\n```````````````````\n" )
            
            dump_counter = self.selective_dump_to_cloud()
            
            if dump_counter == 0:
                self.log_it( "\nNo action taken\n" )
        
        sync_finish = datetime.now()
        
        self.log_it( f"\n\n\nFinished sync at { datetime.now().strftime( '%y-%m-%d %H:%M' ) }\n" )
        
        return ( sync_finish - sync_start ).seconds

        
def main_runner( dirSync, log_path_set=False ):
    
    # setup log file
    if not log_path_set:
        log_path_set = dirSync.setup_log_path()
    
    dirSync.logger = dirSync.new_log_file()
    
    # sync folders
    sync_duration = dirSync.one_way_sync()    
    
    # determine last sync duration to cut from the interval sleep time until next sync 
    sync_delta = dirSync.interval - sync_duration
    
    dirSync.log_it( f"\nLast sync took { sync_duration } seconds.\n\n\n{80 * '~'}\n\n\n\n\n\n" )
    
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

    # opts = [long form], args = [short form]
    opts, args = getopt( argv[1:], "s:d:i:l:",  [ "source_path=" , "destination_path=", "interval=", "log=" ] )

    # build arguments for DirSync constructor
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
        
    
    dir_sync = DirSync( client, cloud, interval, log_path )
    # On lack of disk space the program will exit
    main_runner( dir_sync )
