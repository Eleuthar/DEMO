from os import strerror

class StudentsDataException(Exception):
    pass

class BadLine(StudentsDataException):
    pass

class FileEmpty(StudentsDataException):
    pass
        

PROMPT = 'Where is Dr. Jekyll\'s note?\n'
concatalog = {}
mark = ''
fqdn = ''


def getFileInput():
    fileInput = input(PROMPT)
    global xzp, x
    xzp = open(fileInput, 'r')
    x = xzp.readline()
    # keep asking for a non-empty file 
    if x == '':
        xzp.close()
        raise FileEmpty()
    else:
        return xzp,x


def updatektlog(xzp, x):
    global fqdn, mark
    # iterate catalog
    while x != '':
        xz = x.split()
        # at least 2 names and a mark
        assert len(xz) >= 3

        # sanitize & validate mark is a number
        # if it can be converted to float
        mark = xz[-1]
        if mark.find(',') != -1:
            mark = float(mark.replace(',','.'))
        mark = float(mark)

        # validate each name until the mark point
        # concatenate name for dict key check or addition
        for j in range(len(xz)-1):
            assert xz[j].isalpha()
            fqdn = fqdn + xz[j] + ' '
        fqdn = fqdn.strip()

        if len(fqdn) <= 4:
            raise BadLine()

        if fqdn not in concatalog:
            concatalog[fqdn] = mark
        else:
            concatalog[fqdn] += mark

        # clear var for name and mark and go to next row
        fqdn,mark = '',''
        x = xzp.readline()

    xzp.close()    
    return concatalog


try:
    getFileInput()

except FileEmpty as fx:
    print('This file is empty!\n')
    while FileEmpty:
        getFileInput()

try:
    updatektlog(xzp, x)
    for q,z in concatalog.items():
        print(q, ' ', z)

except BadLine as bx:
    print('Invalid name\n')

except Exception as x:
    print(x.encode, strerror(x.errno))
