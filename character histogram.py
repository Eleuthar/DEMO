##the output histogram will be sorted based on the characters' frequency (the bigger counter should be presented first)
##the histogram should be sent to a file with the same name as the input one, but with the suffix '.hist' (it should be concatenated to the original name)
##Assuming that the input file contains just one line filled with:
##
##cBabAa
##samplefile.txt
##
##the expected output should look as follows:
##
##a -> 3
##b -> 2
##c -> 1



from os import strerror


# generate dict for each letter, initialized counter to 0

qz = {}
for z in range (65,91):
    qz[str(chr(z))] = 0


fname = input('Enter filename to count all letterz: ')


# convert to upper, match dict key & increment count
try:
    txt = open(fname, 'rt')
    q = txt.read(1)
    while q != '':
        if q.isalpha():
            q = q.upper()
            qz[q] += 1
            q = txt.read(1)
        else:
            q = txt.read(1)
            continue
    txt.close()
    
except Exception as x:
    print(x, strerror(x.errno))


# display final count
zx = sorted(qz.items(), key=lambda x:x[1], reverse=True)

for j in zx:
    print(j[0], " -> ", j[1])


