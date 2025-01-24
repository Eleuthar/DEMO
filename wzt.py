import pandas as pd
from xlsxwriter import Workbook
from openpyxl import load_workbook
from datetime import date
from os import listdir
from dataclasses import dataclass
import json

from pdb import set_trace


# customization
env = json.load(open('env.json'))
# first column dedicated for round count
COLUMN_OFFSET = env['column_offset'] + 66


def border(wb, left='thin', right='thin',top='thin', bottom='thin'):
    # "top": 2, "left": 1, "bottom": 2, "right": 1
    return wb.add_format({
        'left': left, 'right': right,
        'top': top, 'bottom': bottom
    })


@dataclass
class Member:
    nm: str
    bet_char: str
    done_char: str
    point_char: str
    bet: list
    done: list
    point: list
    winz: int
    failz: int
    total: int


# keep user prompt on same line to prevent terminal clutter
def rewind_prompt(mzg, condition=None):
    opt = ''
    # prompt option must be digit in a certain range
    print()
    while True:
        while not opt.isdigit():
            print("\033[A\033[A")
            opt = input(f'{mzg}:  \b')
        opt = int(opt)
        if condition is not None:
            if not eval(condition):
                opt = ''
                continue
            else:
                return opt
        return opt


def group_count():
    gamer_num = ''
    while not gamer_num.isdigit():
        gamer_num = input('Numar jucatori: ')
    return int(gamer_num)


def join_players(COLUMN_OFFSET, gamer_num):
    group = []
    uzr_char = COLUMN_OFFSET
    print()
    for q in range(gamer_num):
        # bet \ done \ point
        bet_char = chr(uzr_char)
        done_char = chr(uzr_char + 1)
        point_char = chr(uzr_char+ 2)
        who = input('Nume jucator: ')
        # nm,bet_char,done_char,point_char,winz,failz,total
        group.append(
            Member(
                nm=who,
                bet_char = bet_char,
                done_char = done_char,
                point_char = point_char,
                bet = [], done = [], point = [],
                winz=0, failz=0, total=0
            )
        )
        uzr_char += 3
    return group


# the amount of cards in one round depends on the number of players
def hand_num(gamer_num):
    return [1 for z in range(gamer_num)] + \
    [x for x in range(2,8)] + \
        [8 for z in range(gamer_num)] + \
            [x for x in range(7,1,-1)] + \
                [1 for z in range(gamer_num)]


# format dataframe
def dump_frame(fm, formatting, pending_colorize, group, roundz, gamer_num):
    
    fm.set_row(0, 30)
    fm.set_row(1, 25)
    fm.set_row(2, 22)
    # round number column
    round_col = chr(COLUMN_OFFSET-1)
    fm.set_column(f"{round_col}:{round_col}", 5)
    for j in range(len(roundz)):
        row = j+3
        fm.set_row(row, 25)
        fm.write(f'{round_col}{row}', f'#{j+1}', formatting['round'])
    for uzr in group:
        # name
        fm.merge_range(f"{uzr.bet_char}1:{uzr.point_char}1", uzr.nm, formatting['header'])
        # total
        fm.merge_range(f"{uzr.bet_char}2:{uzr.point_char}2", uzr.total, formatting['total'])
        # stats
        fm.write(f'{uzr.bet_char}3', 'Pariat', formatting['stat'])
        fm.write(f'{uzr.done_char}3', 'Facut', formatting['stat'])
        fm.write(f'{uzr.point_char}3', 'Puncte', formatting['stat'])
        # round iteration from row 4
        for j in range(len(roundz)):
            row = j+3
            fm.write(f'{uzr.bet_char}{row}', uzr.bet[j], formatting['round'])
            fm.write(f'{uzr.done_char}{row}', uzr.done[j], formatting['round'])
            point = f'{uzr.point_char}{row}'
            color = pending_colorize.get(point, '')
            fm.write(point, uzr.done[j], formatting[f'{color}round'])


def get_tabz():
    tabz = []
    for q in listdir():
        if 'xlsx' in q:
            tabz.append(q)
    return tabz


def prompt_bet(who, ndx, final_bidder, bid, hand):
    turn = f'{who} -->'
    allowed = None
    # no constraint for final bidder if bid > hand
    if ndx == final_bidder and bid <= hand:
        diff = hand - bid
        allowed = [q for q in range(0, hand+1)]
        allowed.remove(diff)
    else:
        allowed = [q for q in range(0, hand+1)]
    mzg = f"{turn} {allowed}"
    condition = f'opt in {allowed}'
    bet = int(rewind_prompt(mzg, condition=condition))
    return bet


# pick workbook or make new1
def prompt_menu(menu_opt):
    mzg = '\nAlegeti optiune'
    for z in menu_opt:
        print(z)
    condition = f"opt in range(1, {len(menu_opt)+1})"
    menu = rewind_prompt(mzg, condition=condition)
    return menu
    

def get_wb_frame(tabz):
    # xlsxwriter object
    fname = None
    pen = None
    wb = None
    frame = None
    ROUND = 1
    # make new workbook if none found
    if len(tabz) > 0:
        ROUND = len(tabz)
    fname = f'ROUND {ROUND}.xlsx'
    wb = Workbook(fname)
    frame = wb.add_worksheet(f'ROUND {ROUND}')
    return wb, frame, ROUND


def old_get_wb_frame(tabz):
    # xlsxwriter object
    fname = None
    pen = None
    wb = None
    frame = None
    ROUND = 1
    # make new workbook if none found
    if len(tabz) == 0:
        dt = date.today().strftime('%d-%m-%Y')
        fname = f'ROUND {ROUND}.xlsx'
        wb = Workbook(fname)
        frame = wb.add_worksheet('ROUND 1')
    else:
        mzg = ''
        # enrich prompt menu for singular or plural
        if len(tabz) > 1:
            mzg = 'mai multe tabele'
        else:
            mzg = 'un tabel'
        # score workbooks menu
        print(f'\nAm gasit {mzg}\n')
        for z in tabz:
            print(z)

        menu_opt = ['\n\n1.Alegeti tabel', '2.Creati tabel nou', '3. EXIT']
        menu = prompt_menu(menu_opt)
        if menu == 3:
            exit()
        # pick existing scoring file
        if menu == 1:
            print('\n\nAlegeti tabel\n')
            menu_opt = [f'{x+1}. {tabz[x]}' for x in range(len(tabz))]
            menu = prompt_menu(menu_opt)
            fname = tabz[menu-1]
            with pd.ExcelFile(fname, engine="openpyxl") as reader:
                ROUND = len(wb.sheetnames)+1
            pen = Workbook(fname)
            wb = pen.book
            frame = wb.add_worksheet(f'Round {ROUND}')
        # make new scoring file
        else:
            while True:
                try:
                    fname = input('Introduceti nume fisier: ')
                    fname = f"{'_'.join(fname.split())}.xlsx"
                    pen = pd.ExcelWriter(fname, engine="xlsxwriter")
                    wb = Workbook()
                    frame = wb.add_worksheet('ROUND 1')
                    break
                except:
                    print(f'Nume fisier invalid: >> {fname} <<')
    return wb, frame, ROUND


# mark Cell for color formatting during dataframe dump
def colorize(pending_colorize, color, point_char, row, gamer_num):
    for j in range(gamer_num, row-gamer_num, -1):
        pending_colorize[f'{point_char}j'] = color
    return pending_colorize


if __name__ == '__main__':
    # number of players
    gamer_num = group_count()
    #  player join
    # group = join_players(COLUMN_OFFSET, gamer_num)

    group = [Member(nm='ela', bet_char='C', done_char='D', point_char='E', bet=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], done=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], point=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], winz=0, failz=0, total=0), Member(nm='geo', bet_char='F', done_char='G', point_char='H', bet=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], done=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], point=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], winz=0, failz=0, total=0), Member(nm='flo', bet_char='I', done_char='J', point_char='K', bet=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], done=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], point=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], winz=0, failz=0, total=0), Member(nm='cip', bet_char='L', done_char='M', point_char='N', bet=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], done=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], point=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1], winz=0, failz=0, total=0)]

    # number of deck dealing per round
    roundz = hand_num(gamer_num)
    # find existing score workbook in game directory
    tabz = get_tabz()
    # read existing or write new workbook
    wb, frame, ROUND = get_wb_frame(tabz)
    formatting = {}
    for bg in ['header','total','stat','round','green_round','red_round']:
        formatting[bg] = wb.add_format(env['formatting'][bg])
    _next = -1

    pending_colorize = {} # <<<<<<<<<<< # <<<<<<<<<<<<<<< REMOVE AFTER TZT
    dump_frame(frame, formatting, pending_colorize, group, roundz, gamer_num) # <<<<<<<<<<<<<<< REMOVE AFTER TZT
    wb.close() # <<<<<<<<<<< # <<<<<<<<<<<<<<< REMOVE AFTER TZT

    # GO
    while True:
        break # <<<<<<<<<<<<<<< REMOVE AFTER TZT
    
        pending_colorize = {}
        print(f'\nSpor la joaca!\n')
        for j in range(len(roundz)):
            row = j+3
            hand = roundz[j]
            print(f"\n\n#{j+1} Runda de {hand}\n{'='*len('runda de xxxx')}")
            # bidding
            print(f'\nPariaza\n{"`"*len("nPariaza")}')
            bid = 0
            _next += 1
            if _next == gamer_num:
                _next = 0
            order = [x for x in range(_next, gamer_num)] + [x for x in range(0, _next)]
            final_bidder = order[-1]
            for ndx in order:
                who = group[ndx]
                bet = prompt_bet(who.nm, ndx, final_bidder, bid, hand)
                who.bet.append(bet)
                bid += bet
            # done
            print(f'\nMaini facute\n{"`"*len("Maini facute")}')
            for ndx in order:
                bidder = group[ndx]
                condition = f"opt <= {hand}"
                done = rewind_prompt(bidder.nm, condition)
                bidder.done.append(done)
                # winner
                bet = bidder.bet[j]
                if done == bet:
                    bidder.point.append(5+bet)
                    bidder.total += bidder.point[j]
                    # positive bonus & reset streak
                    if hand != 1:
                        bidder.winz += 1
                        if bidder.winz == gamer_num:
                            bidder.total += (5*gamer_num)
                            bidder.winz = 0
                            pending_colorize = colorize(
                                pending_colorize, 'green_', bidder.point_char, row, gamer_num)
                # loser
                else:
                    # make negative to positive to allow subtraction from total
                    point = int(str(done - bet).strip('-'))
                    bidder.point.append(point)
                    bidder.total -= point
                    if hand != 1:
                        bidder.failz += 1
                        # negative bonus & reset streak
                        if bidder.failz == gamer_num:
                            bidder.total -= (5*gamer_num)
                            bidder.failz = 0
                            colorize(pending_colorize, 'red_', bidder.point_char, row, gamer_num)
        dump_frame(frame, formatting, pending_colorize, group, roundz, gamer_num)
        next = ''
        wb.close()
        while not next.isalpha():
            next = input("\n\nJoc nou? Y \ N: ")
            next = next.upper()
            if next.upper() not in ['Y', 'N']:
                continue
            elif next == 'N':
                exit()
            else:
                _next = -1
                ROUND += 1
                wb = Workbook(f'ROUND {ROUND}.xlsx')
                frame = wb.add_worksheet(f'ROUND {ROUND}')
                for uzr in group:
                    for prop in ['total','winz','failz']:
                        setattr(uzr, prop, 0)
                    for prop in ['bet','done','point']:
                        setattr(uzr, prop, [])
                break
            
