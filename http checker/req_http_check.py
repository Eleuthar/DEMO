# arg 1 = ip or FQDN
# arg 2 = default port 80, else hint
# validate with HEAD, not GET

## exception:
# invalid usage if no arg, exit code 1
# port must be integer in range of 1..65535, exit code 2
# timeout exit code 3
# connectionError exit code 4
# connection ok => print first line of server response


import sys
import requests as q


if len(sys.argv) not in [2, 3]:
	print("Improper number of arguments: at least one is required and not more than two are allowed:\n- http server's address (required)\n- port number (defaults to 80 if not specified)\n")
	sys.exit(1)

host = sys.argv[1]

if len(sys.argv) == 2:
	port = 80
else:
	port = int(sys.argv[2])
	if port not in range(1,65536):
		print("Port number is invalid - exiting")
		sys.exit(2)

try:
	req = q.head('http://localhost:3000/cars', verify=False, timeout=3)

except q.exceptions.Timeout as t:
	print('TimeoutError after 3 seconds')
	sys.exit(3)

except q.exceptions.ConnectionError as conn_ex:
	print(repr(conn_ex()))
	sys.exit(4)
