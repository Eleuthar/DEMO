"""
My very own ASCII LED display.

  #  #### #### #   # #### #### ##### ##### ##### #####
  #     #    # #   # #    #    #   # #   # #   # #   #
  #  #### #### ##### #### ####    #  ##### ##### #   #
  #  #       #     #    # #  #   #   #   #     # #   #
  #  #### ####     # #### ####   #   ##### ##### #####

Usage: python LED_display.py <any sequence of numbers or number groups separated by space>
"""

from os import system
from platform import platform
from sys import argv

current_os = platform()
digitz = {
    '0': ['#####', '#   #', '#   #', '#   #', '#####'],
    '1': ['#', '#', '#', '#', '#'],
    '2': ['####', '   #', '####', '#   ', '####'],
    '3': ['####', '   #', '####', '   #', '####'],
    '4': ['#   #', '#   #', '#####', '    #', '    #', ],
    '5': ['####', '#   ', '####', '   #', '####'],
    '6': ['####', '#   ', '####', '#  #', '####'],
    '7': ['#####', '#   #', '   # ', '  #  ', '  #  '],
    '8': ['#####', '#   #', '#####', '#   #', '#####'],
    '9': ['#####', '#   #', '#####', '    #', '#####'],
    ' ': [3 * ' ' for x in range(5)]
}


def led(digit_map, digit_arg):
    """
    Build each digit line by line, including the space
    """
    todo = ' '.join(digit_arg)

    # clear screen to display in the same area
    system('cls') if 'Windows' in current_os else system('clear')

    # each digit has a height of 5 '#'
    for z in range(5):
        for ndx, digit_key in enumerate(todo):
            if ndx == len(todo) - 1:
                print(digit_map[digit_key][z])
            else:
                print(digit_map[digit_key][z], end="  ")


led(digitz, argv[1:])
