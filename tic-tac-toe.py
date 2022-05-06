from random import randrange
from copy import deepcopy


# board game template
newBoard = [
    ['1','2','3'],
    ['4','5','6'],
    ['7','8','9']
    ]


# player token
sign = {
    'Computer': "X",
    'You': "O"
    }


# the occupied squares will be added on each player & bot move 
markedSquare = []


# win combination template
# the first key to have all values replaced with either 'X' or 'O' will end the game
newCombo = {
    'row1': [ '1','2','3' ],
    'row2': [ '4','5','6' ],
    'row3': [ '7','8','9' ],
    'col1': [ '1','4','7' ],
    'col2': [ '2','5','8' ],
    'col3': [ '3','6','9' ],
    'diag1': [ '1','5','9' ],
    'diag2': [ '3','5','7' ]
}


# make a copy of the win board & win combo
board = [q[:] for q in newBoard]
combo = deepcopy(newCombo)



# ~~~~~~~~~~~~~~~~~~ METHODS ~~~~~~~~~~~~~~~~~~ #

def display_board():    
    for z in range(3):
        print("+-------+-------+-------+")
        print("|       |       |       |")
        for q in range(3):
            if q == 2:
                print("|  ", board[z][q], "  |")
            else:
                print("|  ", board[z][q], "  ", end="")
        print("|       |       |       |")        
    print("+-------+-------+-------+")
    

# ask the user their move & validate input
# update the board & win combo copies
def enter_move():

    try:
        # restart main function if user choice is not numeric
        o = input("Enter your move!\n")
        if not o.isnumeric():
            raise ValueError
        
        # restart main function if user choice is not in range
        elif int(o) not in range(1,10):                
            print("That is not in the range of 1-9, try again!\n")
            enter_move()
        
        # restart main function if user choice square is already taken 
        elif o in markedSquare:
            print("Spot taken! Pick another!\n")
            enter_move()

        else:
            # replace corresponding square value with user mark            
            # if the value is not found in the 1st row, it will be found in either 2nd or 3rd
            for q in range(3):
                if o in board[q]:
                    markedSquare.append(board[q][board[q].index(o)])
                    board[q][board[q].index(o)] = "O"

                elif o not in board[q]:
                    continue       
                            
    except ValueError:
        print('This is not a number, try again!\n')
        enter_move()

    # update win combination table, useful to determine the winner
    for q,v in combo.items():
        if o in v:        
            v[v.index(o)] = "O"
        

## The function browses the board and builds a list of all the free squares;
## the list consists of tuples, while each tuple is a pair of row and column numbers.
def freeSquares():
    freeQ = []
    for z in range(3):
        for q in range(3):
            if board[q][z] != "X" and board[q][z] != "O":
                tup = (q,z)
                freeQ.append(tup)
            else:
                continue
    return len(freeQ)


## analyze the board status in order to check if
## the player using 'O's or 'X's has won the game
def victory_for():
    for key, value in sign.items():
        for j in combo.values():
            if j.count(value) != 3:           
                continue
            elif j.count(value) == 3:
                print(key, " win!\n")
                return True
            else:
                return None
            

## draw the computer's move and update the board
def draw_random_bot_move():
    x = str(randrange(1,10))

    if x in markedSquare: 
        draw_random_bot_move()

    for q in range(3):            

        if x not in board[q]:
            continue

        elif x in board[q]:
            markedSquare.append(board[q][board[q].index(x)])
            board[q][board[q].index(x)] = "X"

    ## update combo
    for q,v in combo.items():
        if x in v:
            v[v.index(x)] = "X"
           

# restart game menu
def rrGame():    
    game = input("Play a new game?\nY or N: ")
    if game.upper() == "Y":        
        return True
    elif game.upper() == "N":
        return False
    else:
        print("Looks like you made a typo :)\n")
        rrGame()

        
# restore the initial values of the global var for a new game
def reinit():
    global board, combo, markedSquare

    board = [q[:] for q in newBoard]
    combo = deepcopy(newCombo)
    markedSquare.clear()    


# start a new game or end program
def gameOver():
    if rrGame():
        reinit()
        return
    else:
        raise SystemExit

    

# ~~~~~~~~~~~~~~~  GAME FLOW ~~~~~~~~~~~~~~~ #

while True:
    # players take turns until there are 2 free squares left
    # get the victor status after each turn
    while freeSquares() > 1:

        # bot move
        draw_random_bot_move()        
        display_board()     
        if victory_for():
               gameOver()        

        # player move
        enter_move()
        display_board()
        if victory_for():
            gameOver()

        # the last move belongs to the bot
        # if he doesn't win, it is a tie
        if freeSquares() == 1:
            draw_random_bot_move()        
            display_board()
            if victory_for():
                gameOver()
            else:
                print("IT'S A TIE!!!\n")        
                gameOver()
