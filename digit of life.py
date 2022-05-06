dateofbirth = input('Enter the date of birth in DD MM YYYY format\n')
digitz = []
total = 0

for j in dateofbirth:
    if j.isnumeric():
        digitz.append(int(j))
    else:
        continue


def sumOfDOB():
    global digitz, total
    
    for z in digitz:
        total += int(z)

    # make new string array from the obtained total
    digitz = list(str(total))
    
    return digitz, total


while len(digitz) > 1:
    total = 0
    sumOfDOB()
else:
    print('Digit of life is', total)
