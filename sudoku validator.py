class SudokuValidator:
    """
    Validate a Sudoku board
    Create new object using a list of 9-digit long strings
    """   
    def __init__(self, matrix_input: list[str]):
        self.matrix = {}
        # outer matrix rows
        self.row = matrix_input
        # initialize outer matrix columns
        self.column = [["0" for _ in range(9)] for _ in range(9)]
        # assign outer matrix column values
        for q in range(9):
            for x in range(9):
                self.column[q][x] = self.row[x][q]
       
    def build_matrix_dict(self) -> dict:
        """
        Build dictionary of the 9 inner matrix based on user input
        :return: dict
        """
        for z in range(0, 9, 3):
            self.matrix["self.row" + str(z + 1)] = [
                self.row[z][0],
                self.row[z][1],
                self.row[z][2],
                self.row[z + 1][0],
                self.row[z + 1][1],
                self.row[z + 1][2],
                self.row[z + 2][0],
                self.row[z + 2][1],
                self.row[z + 2][2],
            ]
            self.matrix["self.row" + str(z + 2)] = [
                self.row[z][3],
                self.row[z][4],
                self.row[z][5],
                self.row[z + 1][3],
                self.row[z + 1][4],
                self.row[z + 1][5],
                self.row[z + 2][3],
                self.row[z + 2][4],
                self.row[z + 2][5],
            ]    
            self.matrix["self.row" + str(z + 3)] = [
                self.row[z][6],
                self.row[z][7],
                self.row[z][8],
                self.row[z + 1][6],
                self.row[z + 1][7],
                self.row[z + 1][8],
                self.row[z + 2][6],
                self.row[z + 2][7],
                self.row[z + 2][8],
            ]
    
    def draw_board(self):
        for z in range(9):
            print("+-----+-----+-----+-----+-----+-----+-----+-----+-----+")
            for q in range(9):
                if q == 8:
                    print("| ", int(self.row[z][q]), " |")
                else:
                    print("| ", int(self.row[z][q]), " ", end="")
        print("+-----+-----+-----+-----+-----+-----+-----+-----+-----+"),

    def validate_inner_matrix(self) -> bool:
        for value in self.matrix.values():
            for z in range(9):
                if value.count(str(z + 1)) != 1:
                    return False
                else:
                    return True
    
    def validate_outer_matrix(self) -> bool:
        for z in range(9):
            if (
                self.row[z].count(str(z + 1)) == 1
                and self.column[z].count(str(z + 1)) == 1
            ):
                continue
            else:
                return False
        return True

    def validation(self) -> bool:
        """
        Actual validation takes place
        :return: bool
        """
        self.draw_board()
        inner_matrix = self.validate_inner_matrix()
        outer_matrix = self.validate_outer_matrix()

        if inner_matrix and outer_matrix:
            print("Valid Sudoku board\n\n")
            return True
        else:
            print("Not a valid Sudoku board\n\n")
            return False


# test case variables
valid = [
    "295743861",
    "431865927",
    "876192543",
    "387459216",
    "612387495",
    "549216738",
    "763524189",
    "928671354",
    "154938672",
]

invalid = [
    "195743862",
    "431865927",
    "876192543",
    "387459216",
    "612387495",
    "549216738",
    "763524189",
    "928671354",
    "254938671",
]

board1 = SudokuValidator(valid)
board1.validation()
board2 = SudokuValidator(invalid)
board2.validation()
