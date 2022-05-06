import sys
import socket

import pdb

# print usage on invalid execution, exit code 1
if len(sys.argv) not in [2, 3]:
    print("Improper number of arguments: at least one is required and not more than two are allowed:\n- http server's address (required)\n- port number (defaults to 80 if not specified)\n")
    sys.exit(1)


# arg 1 = ip or hostname 
host = sys.argv[1]

#pdb.set_trace()
# arg 2 = default port 80, else hint
if len(sys.argv) == 2:
    port = 80
else:
    port = int(sys.argv[2])
    if port not in range(1,65536):
        print("Port number is invalid - exiting")
        sys.exit(2)

try:
	# set TCP connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as z:
        z.connect((host, port))
        z.sendall(b"HEAD / HTTP/1.1\r\nHost: localhost\r\n\Accept: text/html\r\n\r\n")
		# get the response
        reply = str(z.recv(1024), 'utf-8')

		# retrieve brief status
        ok_conn = str(reply.splitlines()[0])
        ok_conn = ok_conn.replace("'", '').replace('b', '')
        print(ok_conn)

except socket.timeout as t:
    print('TimeoutError after ' + str(sock.gettimeout()) + ' seconds')
    sys.exit(3)

except:
    print(sys.exc_info())
    sys.exit(4)
