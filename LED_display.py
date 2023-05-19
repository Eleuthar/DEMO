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


current_os = platform()
digitz = {
        '0': ['#####','#   #','#   #','#   #','#####'],
        '1': ['#','#','#','#','#'],
        '2': ['####','   #','####','#   ','####'],
        '3': ['####','   #','####','   #','####'],
        '4': ['#   #','#   #','#####','    #','    #',],
        '5': ['####','#   ','####','   #','####'],
        '6': ['####','#   ','####','#  #','####'],
        '7': ['#####','#   #','   # ','  #  ','  #  '],
        '8': ['#####','#   #','#####','#   #','#####'],
        '9': ['#####','#   #','#####','    #','#####'],
        ' ': [3 * ' ' for x in range(5)]
    }


def led(digit_argz):
"""
Build each digit line by line, including the space
"""
    todo = ' '.join(digit_argz)    
    
    # each digit has a height of 5 '#'
    for z in range(5):
        for j in range(len(todo)):
            if j == len(todo)-1:
                print(digitz[j][z])
            else:
                print(digitz[j][z], end="  ")
            

system('cls') if 'Windows' in current_os else system('clear')
led(argv[1:])
