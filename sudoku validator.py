
# test case variables
valid = ['295743861','431865927','876192543','387459216',
          '612387495','549216738','763524189','928671354',
          '154938672']

invalid = ['195743862','431865927','876192543','387459216',
            '612387495','549216738','763524189','928671354',
            '254938671']


# outer matrix rows
row = []

for h in range(9):
    # uncomment next line for interactive build, else use test case variable 
    #row.append(list(input('build your own sudoku, enter a 9-digit sequence\n')))

    # use test case variables
    row.append(list(valid[h]))


# outer matrix columns
col = [ [0 for x in range(9) ] for x in range(9)]

for q in range(9):
    for x in range(9):
        col[q][x] = row[x][q]


# build dictionary of the 9 inner matrix
matrix = {}
for z in range(0, 9, 3):
    matrix['row'+ str(z+1)] = [ row[z][0], row[z][1], row[z][2],
                       row[z+1][0], row[z+1][1], row[z+1][2],
                    row[z+2][0], row[z+2][1], row[z+2][2]
    ]
    
    matrix['row'+ str(z+2)] = [ row[z][3], row[z][4], row[z][5],
                       row[z+1][3], row[z+1][4], row[z+1][5],
                    row[z+2][3], row[z+2][4], row[z+2][5]
    ]	

    matrix['row'+ str(z+3)] = [ row[z][6], row[z][7], row[z][8],
                       row[z+1][6], row[z+1][7], row[z+1][8],
                    row[z+2][6], row[z+2][7], row[z+2][8]
    ]


# draw Sudoku board
def draw_board(row):  
    for z in range(9):
        print("+-----+-----+-----+-----+-----+-----+-----+-----+-----+")
        for q in range(9):
            if q == 8:
                print("| ", int(row[z][q]), " |")
            else:
                print("| ", int(row[z][q]), " ", end="")      
    print("+-----+-----+-----+-----+-----+-----+-----+-----+-----+"),


def validate_inner_matrix(matrix):
    for value in matrix.values():
        for z in range(9):
            if value.count(str(z+1)) != 1:
                return False            
            else:
                return True           
            

def validate_outer_matrix(row, col):
    for z in range(9):
        if row[z].count(str(z+1)) == 1 and col[z].count(str(z+1)) == 1:
            continue
        else:
            return False
    return True


# validation
draw_board(row)

innerMatrix = validate_inner_matrix(matrix)
outerMatrix = validate_outer_matrix(row, col)

if innerMatrix == True and outerMatrix == True:
    print('Valid Sudoku board')
else:
    print('Not a valid Sudoku board')
