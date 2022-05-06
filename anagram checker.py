def sortString(txt):
    # remove whitespace
    txt = txt.upper().split()
    # make 1 string out of the new array
    txt = list(''.join(txt))
    # convert back to list for sorting
    txt.sort()
    # make a new string out of the sorted array for easier comparison
    txt = ''.join(txt)
    return txt

print('Welcome to anagram checker!\nYou will need to enter 2 phrases for this check\n')
phraze1 = sortString(input('Please enter the 1st phraze\n'))
phraze2 = sortString(input('Please enter the 2nd phraze\n'))


if phraze1 == phraze2:
    print('The phrazez are anagrams\n')
else:
    print('The phrazez are not anagrams\n')
