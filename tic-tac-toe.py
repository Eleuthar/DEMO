from random import choice
from copy import deepcopy
from os import system
from platform import platform


class TicTacToe:
"""
Play a game of TicTacToe with a competitive bot going for win moves or preventing your win.
"""
    # board game template
    new_board = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]

    # win combination template
    # the first key to have all values replaced with either 'X' or 'O' will end the game
    new_combo_map = {
        "row_top": ["1", "2", "3"],
        "row_mid": ["4", "5", "6"],
        "row_bot": ["7", "8", "9"],
        "col_left": ["1", "4", "7"],
        "col_mid": ["2", "5", "8"],
        "col_right": ["3", "6", "9"],
        "diag_1": ["1", "5", "9"],
        "diag_2": ["3", "5", "7"],
    }
    # player tokens
    tokens = {"Computer": "X", "You": "O"}

    def __init__(self):
        self.op_sys = platform()
        self.board: list[list[str]] = deepcopy(TicTacToe.new_board)
        self.combo_map: dict[str, list[str]] = deepcopy(TicTacToe.new_combo_map)
        self.free_squares: list[str] = [str(x) for x in range(1, 10)]
        self.player_winning_combo: list[str] = []
        self.comp_winning_combo: list[str] = []

    def __del__(self):
        """
        Instance deconstructor
        Triggered after every game, the message is visible on exiting the game
        """
        print("\n\nGOOD BYE! It's been a pleasure.\n\n")

    def display_board(self):
        """
        Clear the screen and draw the game board in place with updated move
        """

        if 'Windows' in self.op_sys:
            system('cls')
        else:
            system('clear')

        for z in range(3):
            print(f"+{7*'-'}+{7*'-'}+{7*'-'}")
            print(f"|{7*' '}|{7*' '}|{7*' '}|")
            for q in range(3):
                if q == 2:
                    print("|  ", self.board[z][q], "  |")
                else:
                    print("|  ", self.board[z][q], "  ", end="")
            print(f"|{7*' '}|{7*' '}|{7*' '}|")
        print(f"+{7*'-'}+{7*'-'}+{7*'-'}")

    def user_move(self):
    """
    Ask the player their move & validate input
    Update the board & combo map
    """
        try:
            # keep asking if user choice is not valid
            o = input("Enter your move!\n")
            if not o.isnumeric():
                raise ValueError

            # keep asking if user choice is not valid
            elif 9 < int(o) < 1:
                print("That is not in the range of 1-9, try again!\n")
                self.user_move()

            # restart main function if user choice square is already taken
            elif o not in self.free_squares:
                print("Spot taken! Pick another!\n")
                self.user_move()
            else:
                return o, "O"

        except ValueError:
            print("This is not a number, try again!\n")
            self.user_move()

    def bot_move(self):
    """
    Draw the computer's move and update the board
    """
        # go for the win!
        if len(self.comp_winning_combo) != 0:
            key = self.comp_winning_combo[0]
            for x in self.combo_map[key]:
                if x.isdigit():
                    return x, "X"

        # prevent win
        elif len(self.player_winning_combo) != 0:
            key = self.player_winning_combo[0]
            for x in self.combo_map[key]:
                if x.isdigit():
                    return x, "X"

        else:
            # get the current best choices
            temp_options = []
            for combo_key, combo in self.combo_map.items():
                if "X" in combo and "O" not in combo:
                    for x in combo:
                        if x.isdigit():
                            temp_options.append(x)

            if len(temp_options) != 0:
                return choice(temp_options), "X"
            else:
                return choice(self.free_squares), "X"

    def update_tables(self, board_number, token):
        """
        Update win combination table
        Replace the game board numbered square with token - "X" or "O"
        Remove tagged number from free_squares
        """
        # remove the square number last tagged
        self.free_squares.remove(board_number)

        # game board
        for row in range(3):
            if board_number in self.board[row]:
                index = self.board[row].index(board_number)
                self.board[row][index] = token
                break

        # combo table
        for combo_key, combo in self.combo_map.items():
            if board_number in combo:
                index = combo.index(board_number)
                combo[index] = token
                self.combo_map[combo_key] = combo

        # refresh list of current winning moves
        self.player_winning_combo: list[str] = []
        self.comp_winning_combo: list[str] = []

        for combo_key, combo in self.combo_map.items():
            if combo.count("O") == 2:
                if 'X' not in self.combo_map[combo_key]:
                    self.player_winning_combo.append(combo_key)
            elif combo.count("X") == 2:
                if 'O' not in self.combo_map[combo_key]:
                    self.comp_winning_combo.append(combo_key)

    def victory(self):
    """
    Analyze the board status and check if someone has won the game
    """
        for win_move in self.combo_map.values():
            for tag_owner, token in TicTacToe.tokens.items():
                if win_move.count(token) == 3:
                    print(tag_owner, " win!\n")
                    return True
        else:
            return False

    @staticmethod
    def restart():
    """
    Ask the player for restart
    """
        new_game = input("Play a new game?\nY or N: ")
        if new_game.upper() == "Y":
            return True
        elif new_game.upper() == "N":
            return False
        else:
            print("Looks like you made a typo :)\n")
            TicTacToe.restart()

            
# ~~~~~~~~~~~~~~~  PLAY GAME ~~~~~~~~~~~~~~~ #

if __name__ == "__main__":

    while True:

        game = TicTacToe()
        game.display_board()
        # players take turns until there are 2 free squares left
        # get the victor status after each turn
        while len(game.free_squares) >= 0:

            board_no, tokn = game.user_move()
            game.update_tables(board_no, tokn)
            game.display_board()

            if game.victory():
                break

            if len(game.free_squares) == 0:
                print("IT'S A TIE!!!\n")
                break

            board_no, tokn = game.bot_move()
            game.update_tables(board_no, tokn)
            game.display_board()

            if game.victory():
                break

        if not TicTacToe.restart():
            raise SystemExit
        else:
            del game
