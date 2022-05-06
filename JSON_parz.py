
import json

class Vehicle:

	def __init__(self):
		self.reg = input('Registration number: ')
		self.prod = input('Production year: ')
		self.pzng = 'True' if input('Passenger: [y/n] ') == 'y' else 'False'
		self.m = input('Vehicle mass: ')

	def encode_V(q):
		if isinstance(q, Vehicle):
			return q.__dict__
		else:
			raise TypeError(q.__class__.__name + ' is not JSON serializable\n')


	def decode_V(q):
		return Vehicle(q['reg'],q['prod'],q['pzng'],q['m'])



print('What can I do for you?\n')
print('1 - produce a JSON string describing a vehicle\n')
print('2 - decode a JSON string into vehicle data\n')
opt = input()


print('Choice = ' + opt + '\n')
nuV = Vehicle()
jzon = json.dumps(nuV.__dict__)


while True:
	if opt == '1':
		print(jzon)
		break
	elif opt == '2':
		print(json.loads(jzon))
		break
	else:
		print('You must pick either 1 or 2\n') 
