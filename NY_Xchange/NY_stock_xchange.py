import xml.etree.ElementTree as x
import pdb

try:
	tree = x.parse('nyse.xml')
except FileNotFoundError as fe:
	print(repr(fe))
except x.ParseError as pe:
	print(repr(pe))
	
root = tree.getroot()
tagz = root.getchildren()

# column header
header = tagz[0].keys()
header.insert(0,'Company')


# get size of the longest text
txt = []
maxSize = 0
regSize = 10

for q in tagz:
	txt.append(q.text)
	if len(q.text) > maxSize:
		maxSize = len(q.text) + 6


# header separator
sepLen = 0
for h in header:
	sepLen += len(h)+5  

sepLen += maxSize - len(header[0])
separator = '-' * sepLen


# print header, separator, text & attributes
for q in header:
	if q != 'Company':
		if header.index(q) == 4:
			print(q.upper().ljust(regSize, " "))
		else:
			print(q.upper().ljust(regSize, " "), end='')
	else:
		print(q.upper().ljust(maxSize, " "), end="")

print(separator)

#pdb.set_trace()
for q in tagz:
	for x in range(len(header)):
		if x == 0:
			print(q.text.ljust(maxSize,' '), end='')
		else:
			print(q.attrib[header[x]].ljust(10, " ") ,end='')
	print('\n')



