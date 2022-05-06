def mysplit(strng):
    qz = []
    q = ""
    for z in range(len(strng)):
        if ord(strng[z]) > 32:
            q += strng[z]
        else:
            if len(q) == 0:
                continue
            else:
                qz.append(q)
                q = ""
    return qz
        

## tester 
print(mysplit("To be or not to be, that is the question"))
print(mysplit("To be or not to be,that is the question"))
print(mysplit("   "))
print(mysplit(" abc "))
print(mysplit(""))
