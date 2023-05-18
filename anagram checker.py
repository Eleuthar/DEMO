def anagrammer(txt):
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
phraze1 = anagrammer(input('Please enter the 1st phrase\n'))
phraze2 = anagrammer(input('Please enter the 2nd phrase\n'))


if phraze1 == phraze2:
    print('The phrases are anagrams\n')
else:
    print('The phrases are not anagrams\n')
