"""
Find and return the cheapest (lowest) shown price (Please avoid using the minimum function)
Find and return the room type, number of guest with the cheapest price 
Print the total price (Net price + taxes) for all rooms along with the room type
Please add your output to a file
"""
import argparse
import json


def parse_price(room, shown_price, net_price) -> float|None:
    # the script assumes a ',' thousand separator & '.' decimal separator
    # otherwise, it would use a sanitization function to ensure\enforce expected formatting
    try:
        shown_price = float(shown_price)
        net_price = float(net_price)
        return shown_price, net_price
    except:
        # SANITIZE should happen here, for now just print invalid float
        # Suggestion: mypyc can enforce data type
        print(f'Wrong format for {room}: {shown_price}')
        return None, None

   
def find_min(
        shown_price: dict[str, str],
        net_price: dict[str, str],
        TAXES: float
    ):
    room_total = {}
    min_price = None
    min_room = None
    for room in shown_price.keys():
        s_price = shown_price[room]
        n_price = net_price[room]
        # parse_price is just a demonstration on handling invalid data inserted accidentally
        # for the sake of the task it would require only 2 lines for each conversion
        parsed_shown_price, parsed_net_price = parse_price(room, s_price, n_price)
        # set the lowest price found
        if parsed_shown_price is not None:
            # map the room to total
            room_total[room] = parsed_net_price + TAXES
            if min_price is not None:
                if parsed_shown_price < min_price:
                    min_price = parsed_shown_price
                    min_room = room
            else:
                min_price = parsed_shown_price
                min_room = room
    return room_total, min_room, min_price


# execute only if script is used as interpreter argument, not via import
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help=" JSON input file")
    parser.add_argument('output', help="Plain text output file")
    args = parser.parse_args()
    input_filename = args.input
    export_filename = args.output

    # 'Python-task.json'
    with open(input_filename) as jfile:
    
        # extract relevant items from json file
        jinput = json.load(jfile)
        shown_price = jinput['assignment_results'][0]['shown_price']
        net_price = jinput['assignment_results'][0]['net_price']
        number_of_guests = jinput['assignment_results'][0]['number_of_guests']
        tax = json.loads(jinput['assignment_results'][0]['ext_data']['taxes'])
        TAXES = float(tax['TAX']) + float(tax['City tax'])

        # result for console & file dumping
        room_total, min_room, min_price = find_min(shown_price, net_price, TAXES)
    
        # export to file
        with open(export_filename, 'w') as exported:
            num_guest_output = f'Number of guests: {number_of_guests}'
            min_room_output = f'Cheapest room "{min_room}" for {min_price}'
            for line in [num_guest_output, min_room_output]:
                print(line)
                exported.write(f'{line}\n')
            for room, total in room_total.items():
                output = f'Total price for {room}: {total:.2f}'
                print(output)
                exported.write(f'{output}\n')
