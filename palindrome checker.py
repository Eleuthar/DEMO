while True:
    txt = input('enter phrase to check if palindrome\n')
    
    while len(txt) == 0 or txt.isspace():
        txt = input('enter phrase to check if palindrome\n')

    phraze = ''
    
    for z in txt.upper():
        if z.isspace():
            continue
        else:
            phraze += z

    half1 = phraze[:(len(phraze)//2)]
    
    if len(phraze) % 2 == 0:
        half2 = list(phraze[(len(phraze)//2):])
    else:
        half2 = list(phraze[(len(phraze)//2 + 1):])

    half2.reverse()
    half2 = str(''.join(half2))

    if half1 != half2:
        print('Not a palindrome')
    else:
        print('It is palindrome!')
