##.\tree\python
##.\tree\cpp\other_courses\python
##.\tree\cpp\other_courses\c\python
##.\tree\c\other_courses\python
##.\tree\c\other_courses\cpp\python


import os as z

dirPath = input('where to find?\n')
z.chdir(dirPath)
target = input('what to find?\n')

# capitalize both target & dir
tg = target.capitalize()

# store found target 
rez = []

# store adjacent untraversed directory 
todo = []


# function start from root
def iterate(director):
    global todo, rez
    
    # if directory empty, traversal is complete and items may be added in todo[]
    tmp = z.listdir()
    if len(tmp) == 0:
        # iterate from todo if is not empty
        if len(todo) > 0:     
            nextDir = todo.pop()
            z.chdir(nextDir)
            iterate(nextDir)
        else:
            print('Iteration completed across all subdirectories!\n')
            return

    else:
        # find target in current pth and add to rezult[]
        for j in tmp:
            if j.capitalize() == tg:
                rez.append(z.getcwd() +'/'+j)

        # if there is at least 1 directory, continue iteration with popped dir which is next dir
        # if there are more than 1 dirz, save in todo the untouched
        nextDir = tmp.pop()
        if len(tmp) >= 1:
            for j in tmp:
                todo.append(z.getcwd()+'/'+j)
        z.chdir(nextDir)
                
        iterate(nextDir)


iterate(dirPath)
print(tg,'has been found in:\n')
for q in rez:
    print(q)
