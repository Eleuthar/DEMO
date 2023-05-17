import xml.etree.ElementTree as xtree


tree = None

try:
	tree = xtree.parse('nyse.xml')
	root = tree.getroot()
	tagz = root.getchildren()

	# column header
	header = list(tagz[0].keys())
	header.insert(0, 'Company')

	# get size of the longest text
	txt = []
	max_size = 0
	reg_size = 10

	for q in tagz:
		txt.append(q.text)
		if len(q.text) > max_size:
			max_size = len(q.text) + 6

	# header separator
	sepLen = 0
	for h in header:
		sepLen += len(h) + 5

	sepLen += max_size - len(header[0])
	separator = '-' * sepLen

	# print header, separator, text & attributes
	for q in header:
		if q != 'Company':
			if header.index(q) == 4:
				print(q.upper().ljust(reg_size, " "))
			else:
				print(q.upper().ljust(reg_size, " "), end='')
		else:
			print(q.upper().ljust(max_size, " "), end="")

	print(separator)

	# pdb.set_trace()
	for q in tagz:
		for xtree in range(len(header)):
			if xtree == 0:
				print(q.text.ljust(max_size, ' '), end='')
			else:
				print(q.attrib[header[xtree]].ljust(10, " "), end='')
		print('\n')

except FileNotFoundError as fe:
	print(repr(fe))

except xtree.ParseError as pe:
	print(repr(pe))
