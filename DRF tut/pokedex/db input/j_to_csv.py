import json
import csv

# poke_csv = open('pokemon.csv', 'w', newline='')
# pokemon_writer = csv.writer(poke_csv)
# 'id', 'name', type', height', weight', xp', hp', attack',defense',special-attack',special-defense',speed'

move_csv = open('move.csv', 'w', newline='')
move_writer = csv.writer(move_csv)

with open('db.json') as j_file:
    x = 1
    for mon in json.load(j_file):
        # row = []
        # mon_id = mon['id']
        # row.append(mon['name'])
        # row.append(mon['types'][0]['name'])
        # row.append(mon['height'])
        # row.append(mon['weight'])
        # row.append(mon['xp'])
        #
        # for stat in mon['stats']:
        #     row.append(stat['base_stat'])
        #
        # pokemon_writer.writerow(row)
        for move in mon['abilities']:
            move_writer.writerow([x, move['name'], mon['id']])
            x += 1

move_csv.close()
# poke_csv.close()
