import csv
import json
import math
import os
import re
import requests
import requests_cache
import sys


HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
}

ARMOR_SUBCLASS = {
    1: 'cloth',
    2: 'leather',
    3: 'mail',
    4: 'plate',
}
WEAPON_SUBCLASS = {
    0: '1h ? axe',
    1: '2h ? axe',
    2: 'bow',
    3: 'gun',
    4: '1h ? mace',
    5: '2h ? mace',
    6: 'polearm',
    7: '1h ? sword',
    8: '2h ? sword',
    9: 'warglaive',
    10: 'staff',
    13: 'fist',
    15: '? dagger',
    18: 'crossbow',
    19: 'wand',
    20: 'fishing-pole',
}
INVENTORY_SLOT = {
    1: 'head',
    3: 'shoulders',
    4: 'shirt',
    5: 'chest',
    6: 'waist',
    7: 'legs',
    8: 'feet',
    9: 'wrists',
    10: 'hands',
    13: 'weapon',
    14: 'weapon',
    15: 'ranged',
    16: 'back',
    17: 'weapon',
    20: 'chest',
    21: 'weapon',
    22: 'weapon',
    23: 'off-hand',
    26: 'ranged',
}
CHRCLASS = {
    1: 'Death Knight',
    2: 'Demon Hunter',
    3: 'Druid',
    4: 'Evoker',
    5: 'Hunter',
    6: 'Mage',
    7: 'Monk',
    8: 'Paladin',
    9: 'Priest',
    10: 'Rogue',
    11: 'Shaman',
    12: 'Warlock',
    13: 'Warrior',
}
SORT_CHRCLASS = {
    32: 1,   # 6=death knight
    2048: 2, # 12=demon hunter
    1024: 3, # 11=druid
    4096: 4, # 13=evoker
    4: 5,    # 3=hunter
    128: 6,  # 8=mage
    512: 7,  # 10=monk
    2: 8,    # 2=paladin
    16: 9,   # 5=priest
    8: 10,   # 4=rogue
    64: 11,  # 7=shaman
    256: 12, # 9=warlock
    1: 13,   # 1=warrior

    # cloth
    (16 + 128 + 256): 20,
    # leather
    (8 + 1024): 21,
    (8 + 1024 + 512): 21,
    (8 + 1024 + 512 + 2048): 21,
    # mail
    (4 + 64): 22,
    (4 + 64 + 4096): 22,
    # plate
    (1 + 2): 23,
    (1 + 2 + 32): 23,
}
SORT_CLASS = {
    4: 1, # Armor
    0: 2, # Misc
    2: 3, # Weapon
}
SORT_SUBCLASS = {
    (4, 1): 20, # Cloth
    (4, 2): 21, # Leather
    (4, 3): 22, # Mail
    (4, 4): 23, # Plate
    (4, -6): 30, # Cloak
    (2, 0): 100, # 1h axe
    (2, 4): 101, # 1h mace
    (2, 7): 102, # 1h sword
    (2, 15): 103, # dagger
    (2, 13): 104, # fist
    (2, 9): 105, # warglaive
    (2, 1): 110, # 2h axe
    (2, 5): 111, # 2h mace
    (2, 8): 112, # 2h sword
    (2, 6): 113, # polearm
    (2, 10): 114, # staff
    (2, 2): 120, # bow
    (2, 18): 121, # crossbow
    (2, 3): 122, # gun
    (2, 19): 123, # wand
    (4, -5): 130, # off-hand
    (4, 6): 131, # shield
}
SORT_KEY = {
    1: 1, # head
    3: 2, # shoulders
    16: 3, # back
    5: 4, # chest
    9: 5, # wrists
    10: 6, # hands
    6: 7, # waist
    7: 8, # legs
    8: 9, # feets
}
SKIP_INVENTORY_SLOT = set([
    2, # neck
    11, # ring
    12, # trinket
])


STANDING = {
    4: 'friendly',
    5: 'honored',
    6: 'revered',
    7: 'exalted',
}

MAPPER_RE = re.compile(r'var g_mapperData = (.*?)\;$', re.MULTILINE)
NPC_RE = re.compile(r'^\$\.extend\(g_npcs\[\d+], (.*?)\)\;$', re.MULTILINE)
SELLS_RE = re.compile(r'^new Listview\(.*?id: \'(drops|sells)\'.*?data:\s*(.*?)\}\)\;$', re.MULTILINE)


def main():
    cache_path = os.path.join(os.path.dirname(__file__), '..', 'temp', 'requests_cache')
    requests_cache.install_cache(cache_path, expire_after=4 * 3600)

    dumps_path = os.path.join(os.path.abspath(os.path.expanduser(os.environ['WOWTHING_DUMP_PATH'])), 'enUS')

    ima_to_item = {}
    with open(os.path.join(dumps_path, 'itemmodifiedappearance.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            ima_to_item[int(row['ID'])] = int(row['ItemID'])

    rows = []
    with open(os.path.join(dumps_path, 'transmogsetitem.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            rows.append(row)
    
    set_size = {}
    for row in rows:
        set_id = int(row['TransmogSetID'])
        set_size[set_id] = set_size.get(set_id, 0) + 1

    item_to_set = {}
    for row in rows:
        ima_id = int(row['ItemModifiedAppearanceID'])
        if ima_id not in ima_to_item:
            continue

        item_id = ima_to_item[ima_id]
        set_id = int(row['TransmogSetID'])

        if item_id not in item_to_set or set_size[item_to_set[item_id]] < set_size[set_id]:
            item_to_set[item_id] = set_id


    url = sys.argv[1]
    if url.isdigit():
        url = f'https://www.wowhead.com/npc={url}'

    r = requests.get(url, headers=HEADERS)
    expand = len(sys.argv) >= 3 and sys.argv[2] == 'e'
    no_gold = len(sys.argv) >= 3 and sys.argv[2] == 'nogold'

    m = MAPPER_RE.search(r.text)
    mapper = None
    if m:
        mapper = json.loads(m.group(1))

    m = NPC_RE.search(r.text)
    if not m:
        print('npc_re fail')
        sys.exit(1)

    npc = json.loads(m.group(1))

    m = SELLS_RE.search(r.text)
    if not m:
        print('sells_re fail')
        sys.exit(1)

    contents_type = m.group(1)

    item_json = re.sub(r'(standing|react|stack|avail|cost):', r'"\1":', m.group(2))
    item_json = re.sub(r',\]', ',0]', item_json)
    item_json = re.sub(r'\[,', '[0,', item_json)
    items = json.loads(item_json)


    faction = ''
    react = npc.get('react')
    if react is None:
        react = [0, 9]
    else:
        if len(react) == 1:
            react.push(0)
        if react[0] is None:
            react[0] = 0
        if react[1] is None:
            react[1] = 0

    if react[0] == 1 and (len(react) == 1 or react[1] <= 0):
        faction = ' alliance'
    elif react[0] <= 0 and react[1] == 1:
        faction = ' horde'

    if not expand:
        print(f'things:')
        print(f'  - id: {npc["id"]}')

        if contents_type == 'drops':
            print(f'    type: "npc"')
        else:
            print(f'    type: "vendor"')

        print(f'    name: "{npc["name"]}"')
        if 'tag' in npc:
            print(f'    note: "{npc["tag"]}"')

        if contents_type == 'drops':
            print(f'    reset: "daily"')
            print(f'    trackingQuestId: ')

        print()
        print('    locations:')

        if mapper is not None:
            for map_set in mapper.values():
                if isinstance(map_set, dict):
                    map_set = map_set.values()

                for map in map_set:
                    map_name = map.get('uiMapName', 'unknown').lower().replace(' ', '_').replace('-', '_').replace("'", '')
                    print(f'      here: # {map_name}')
                    
                    for coord in map['coords']:
                        print(f'        - {coord[0]} {coord[1]}{faction}')

        print()

        print('    contents:')

    sorted_items = sorted(items, key=lambda item: [
        -item.get("standing", 0),
        SORT_CHRCLASS.get(item.get("reqclass", 0), 999),
        SORT_SUBCLASS.get(
            (item["classs"], item.get("subclass", 0)),
            SORT_CLASS.get(item["classs"], item["classs"] + 500 + item.get("subclass", 0)),
        ),
        item_to_set.get(item["id"], 99999),
        SORT_KEY.get(item.get("slot", 0), item.get("slot", 0) + 100),
        item["name"],
    ])

    last_cls = None
    last_set = 0
    for item in sorted_items:
        item_class = item.get('classs', 0)
        item_subclass = item.get('subclass', 0)
        item_slot = item.get('slot', 0)
        type_parts = []

        sort_key = SORT_CHRCLASS.get(item.get('reqclass', 0), 0)
        char_class = CHRCLASS.get(sort_key, sort_key)
        set_id = item_to_set.get(item['id'], 0)

        if item_slot in SKIP_INVENTORY_SLOT:
            if not expand and contents_type != 'drops':
                print(f'      # Skipped id={item["id"]} name={item["name"]} slot={item_slot}')
            continue

        costs = item.get('cost', [[0, [], []]])[0]
        if no_gold and costs[0] > 0 and len(costs[1]) == 0 and len(costs[2]) == 0:
            continue

        if contents_type == 'drops':
            count = item.get('count', 0)
            out_of = item.get('outof', 0)
            if count and out_of and count / out_of < 0.005:
                # print(f'      # Skipped id={item["id"]} name={item["name"]} slot={item_slot}')
                continue


        if expand:
            if char_class != 0:
                note = char_class
                if item.get('heroic', 0) == 1:
                    note += ' Heroic'
                print(f'  - {item["id"]} # {item["name"]} [{note}]')
        else:
            print('')

            if char_class != last_cls or set_id != last_set:
                if set_id:
                    print(f'      # {char_class} set={set_id}')
                else:
                    print(f'      # {char_class}')
                print()
                last_cls = char_class
                last_set = set_id

            if item_class == 2:
                type_parts.append(WEAPON_SUBCLASS.get(item_subclass, f'subclass={item_subclass}'))
            
            elif item_class == 4:
                if item_subclass == -8:
                    type_parts.append('shirt')
                elif item_subclass == -7:
                    type_parts.append('tabard')
                elif item_subclass == -6:
                    type_parts.append('cloak')
                elif item_subclass == -5:
                    type_parts.append('off-hand')
                elif item_subclass == 6:
                    type_parts.append('shield')
                else:
                    type_parts.append(ARMOR_SUBCLASS.get(item_subclass, f'subclass={item_subclass}'))
                    type_parts.append(INVENTORY_SLOT.get(item_slot, f'item_slot={item_slot}'))
            
            type_str = ''
            if len(type_parts) > 0:
                type_str = f' [{" ".join(type_parts)}]'

            print(f'      - id: {item["id"]} # {item["name"]}{type_str}')

            if contents_type != 'drops':
                print( '        costs:')

                # print(costs)
                if costs[0] > 0:
                    print(f'          0: {max(1, math.floor(costs[0] / 10000))} # Gold')

                if len(costs) >= 2:
                    # print(costs)
                    for cost in costs[1]:
                        print(f'          {cost[0]}: {cost[1]}')

                if len(costs) == 3:
                    for cost in costs[2]:
                        print(f'          1{cost[0]:06}: {cost[1]}')
                
                if item.get('standing', 0) > 0:
                    print(f'        requirements:')
                    print(f'          - "reputation: 0 {STANDING.get(item["standing"], item["standing"])}"')

            # print('>', item)


if __name__ == '__main__':
    main()
