  # ### ### # # ### ### ### ### ### ### 
  #   #   # # # #   #     # # # # # # # 
  # ### ### ### ### ###   # ### ### # # 
  # #     #   #   # # #   # # #   # # # 
  # ### ###   # ### ###   # ### ### ###


digitz = {
        '0': ['###','# #','# #','# #','###'],
        '1': ['#','#','#','#','#'],
        '2': ['###','  #','###','#  ','###'],
        '3': ['###','  #','###','  #','###'],
        '4': ['# #','# #','###','  #','  #',],
        '5': ['###','#  ','###','  #','###'],
        '6': ['###','#  ','###','# #','###'],
        '7': ['###','  #','  #','  #','  #'],
        '8': ['###','# #','###','# #','###'],
        '9': ['###','# #','###','  #','###']
    }

intz = input("Enter some numbers for your LED display: ")


def led(intz):
    
    todo = [digitz[x] for x in intz]

    for z in range(5):
        for j in range(len(todo)):
            if j == len(todo)-1:
                print(todo[j][z])
            else:
                print(todo[j][z], end="  ")

led(intz)
