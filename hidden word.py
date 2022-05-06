word = input('Hide a word?\n').lower()
hidden = input('Where will you hide it?\n').lower()
index = []

for z in word:
    index.append(hidden.find(z))
    

if -1 in index:
    print('Word not found in ', hidden)
else:
    print('Word found in ', hidden)
        
        

