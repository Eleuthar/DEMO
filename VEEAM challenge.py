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
	$ python dir_sync.py "C:\\Users\\MrRobot\\Documents\\Homework\\" "C:\\Users\\MrRobot\\Downloads\\VEEAM_CLOUD\\Homework\\" 5 M "C:\\Program Files\\VEEAM\\logs\\"
	
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
client = path.realpath(argv[1])
cloud = path.realpath(argv[2])
# interval translated into seconds
interval = ( int( argv[3] ) * timeframe[ argv[4].upper( ) ] )
log_path = path.realpath(argv[5])
client_hexmap = { }
cloud_hexmap = { }

	
def setup_log_path( log_path ):
# implemented log path validation since user interpretation can be ambiguous: either provide a directory to be created or use an existing one.
	
	print( f'Validating log directory: "{ log_path }"\n' )	
	# set a unique delimiter regardless of platform (Linux\Windows)
	
	# folder check
	if not path.exists( log_path ):    
		
		sep = '\\' if '\\' in log_path else '/'            
		split_path = log_path.split( sep )
		dir_name = split_path.pop()
		upper_dirname = split_path[-1]
		upper_dir = '/'.join( split_path )
        
		print( f'Directory "{ dir_name }" does not exist. Will create it if upper directory "{ upper_dirname }" is valid.\n' )
		# upper folder check
        
		if not path.exists( upper_dir ):				
			print( f"Upper directory of { dir_name } does not exist either.\nPlease use an existing directory to store the logs." )
			exit()		
		else:
			print( f"Creating { dir_name } under { upper_dir }\n" )
			mkdir( log_path )
			return True	  
	else:
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
            hexmap[ 'root' ].append( root )
            heexmap[ 'fname' ].append( None )
			hexmap[ 'hex' ].append( None )
            
		for fname in directory[2]:
			hexmap[ 'root' ].append( root )
			hexmap[ 'fname' ].append( fname )
			hx = generate_file_hex( root, fname )
			hexmap[ 'hex' ].append( hx )			
			logger.write( root )
			logger.write( fname )
			logger.write( hx )
			logger.write("\n\n{60*'-'}\n\n")			
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
				rename( new_path, old_path )
				log_it( logger, f"Renamed {old_path} to {new_path}\n")
			except Exception as X:
				log_it( logger, f"{X}\n" )
			return

	
def rm_obsolete_dir( root, logger ):	  
	try:
        set_trace()
		rmdir( root )
		log_it( logger, f"Deleted directory { root }\n" )		
	except Exception as X:
		log_it( logger, f"Error: { X }\n" )	
	return
		

def diff_hex( logger ):
	# start from the client deepest root	
	# if root not in cloud ['root'], review content recursively to remove\move\keep\update, then add to set for final cleanup
	
	global client, cloud, client_hexmap, cloud_hexmap		
	dir_to_rm = set()
    
	# compare cloud against client
	for hx_tgt in reversed( cloud_hexmap['hex'] ):
	
		index = cloud_hexmap['hex'].index( hx_tgt )
        
		dst_root = cloud_hexmap[ 'root' ][ index ]
		dst_fn = cloud_hexmap[ 'fname' ][ index ] 
		dst_hex = cloud_hexmap[ 'hex' ][ index ]
        
		fpath_on_cloud = path.join( dst_root, dst_fn )
        
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
				continue
			# different filename || root || path > RENAME
			else:				
				rename_it( logger, dst_hex, fpath_on_cloud )			
		# no hex match
		else:
			# same path > REPLACED
			if path.exists( expected_path_on_client ):
				log_it( logger, f"UPDATING { fpath_on_cloud }\n" )
				try:					
					remove( fpath_on_cloud )
					copy2( expected_path_on_client, fpath_on_cloud )
					log_it( logger, f"UPDATED { fpath_on_cloud }\n" )
					continue
				except Exception as X:
					log_it( logger,  f"Error: { X }\n" )			
			# same filename but diff root > RENAME
			elif not path.exists( expected_path_on_client ) and dst_fn in client_hexmap['fname']:
				rename_it( logger, dst_root, fpath_on_cloud )				
			# no path match > DELETE
			else:
				try:
					remove( fpath_on_cloud )
				except Exception as X:
					log_it( logger, f"DELETED {fpath_on_cloud}\n")
		if dst_root not in client_hexmap[ 'root' ]:
			dir_to_rm.add( dst_root )
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
