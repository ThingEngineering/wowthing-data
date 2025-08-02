import csv
import os
import os.path
import re
import sys


CLASS_MASK = {
       1: 'warrior',
       2: 'paladin',
       4: 'hunter',
       8: 'rogue',
      16: 'priest',
      32: 'death-knight',
      64: 'shaman',
     128: 'mage',
     256: 'warlock',
     512: 'monk',
    1024: 'druid',
    2048: 'demon-hunter',
    4096: 'evoker',
}

ARMOR_MASKS = {
    'cloth': [
        16 + 128 + 256,
    ],
    'leather': [
        8 + 1024,
        8 + 1024 + 512,
        8 + 1024 + 512 + 2048,
    ],
    'mail': [
        4 + 64,
        4 + 64 + 4096,
    ],
    'plate': [
        1 + 2,
        1 + 2 + 32,
    ]
}
ARMOR_MASK = {}
for armor_type, masks in ARMOR_MASKS.items():
    for mask in masks:
        ARMOR_MASK[mask] = armor_type

SLOT_MAP = {
     1: 'Head',
     3: 'Shoulders',
     5: 'Chest',
     6: 'Waist',
     7: 'Legs',
     8: 'Feet',
     9: 'Wrists',
    10: 'Hands',
    16: 'Back',
    20: 'Chest',
}

SLOT_ORDER = [
    1,
    3,
    16,
    5,
    20,
    9,
    10,
    6,
    7,
    8,
]

DESCRIPTION_MAP = {
     1641: 'Raid Finder',
     2015: 'Heroic',
     3859: 'Elite',
    13145: 'Mythic',
    13193: 'Normal',
    13216: 'Timewarped',
    13291: '25 Normal',
    13292: '25 Heroic',
    13293: '10 Normal',
    13301: 'Gladiator',
    13302: 'Combatant',
    13303: 'Aspirant',
    13304: 'Honor',
    13306: 'PVP Rare',
    13307: 'PVP Epic',
    13305: 'Normal', # Sunwell
    13448: 'Warfront',
    13584: 'Ember Court',
    13590: 'Campaign',
    13591: 'Renown',
    13592: "Queen's Conservatory",
    13594: 'Abominable Stitching',
    13595: 'Unity',
    13596: 'Travel Network',
    13787: 'Winterborn',
    13813: 'Path of Ascension',
    13849: "Death's Advance",
    13850: 'Korthia',
    13859: 'Renown Quartermaster',
    13964: 'Bronze',
    13965: 'Red',
    13966: 'Black',
    13967: 'Blue',
    13968: 'Green',
    13979: 'Primal Storms',
    13980: 'War Mode',
    13987: 'World and Weekly Quests',
    13989: 'Quest Rewards',
    13990: 'World Drops',
    13991: 'Professions',
    13992: 'World Drop',
    13993: 'Crafted',
    13998: 'Dungeons',
    14009: 'The Forbidden Reach',
    14015: 'Purple',
    14016: 'World Quests and World Drops',
    14017: 'Suffusion Camps and PvP',
    14018: 'Treasures and Unique Creatures',
    14025: 'Time Rifts',
    14028: 'Time Rifts and Dawn of the Infinite',
    14029: 'Dawn of the Infinite',
    14034: 'Emerald Bounty',
    14041: 'Superbloom',
    14122: 'Yellow',
    14125: 'Beige',
    14145: 'Teal',
    14146: 'Burgundy',
    14174: 'Delves',
    14214: 'Rare Monsters',
    14349: 'Phase Diving',
    14350: 'Treasures and World Quests',
}
DESCRIPTION_ORDER = [
    13145, # Mythic
     2015, # Heroic
    13292, # 25 Heroic
    13305, # Sunwell
    13291, # 25 Normal
    13293, # 10 Normal
    13193, # Normal
     1641, # Raid Finder
    13216, # Timewarped
     3859, # Elite
    13301, # Gladiator
    13302, # Combatant
    13304, # Honor
    13303, # Aspirant
    13307, # PVP Epic
    13306, # PVP Rare
    13448, # Warfront

    # 9.0 covenant
    13590, # Campaign
    13591, # Renown
    # Kyrian
    13813, # Path of Ascension
    # Necrolord
    13594, # Abominable Stitching
    13595, # Unity
    # Night Fae
    13592, # Queen's Conservatory
    13787, # Winterborn
    # Venthyr
    13584, # Ember Court
    13596, # Travel Network

    # 9.1 covenant
    13849, # Death's Advance
    13850, # Korthia
    13859, # Renown Quartermaster

    # Dragonflight
    14009, # The Forbidden Reach
    13979, # Primal Storms
    13989, # Quest Rewards
    13987, # World and Weekly Quests
    13998, # Dungeons
    13980, # War Mode
    13991, # Professions
    13993, # Crafted
    14174, # Delves
    13992, # World Drop
    13990, # World Drops

    14017, # 'Suffusion Camps and PvP'
    14018, # 'Treasures and Unique Creatures'
    14016, # 'World Quests and World Drops'
    14029, # 'Dawn of the Infinite'
    14028, # 'Time Rifts and Dawn of the Infinite'

    15025, # 'Time Rifts'

    14125, # Beige
    13966, # Black
    13967, # Blue
    14146, # Burgundy
    13964, # Bronze
    13968, # Green
    14015, # Purple
    13965, # Red
    14145, # Teal
    14122, # Yellow

    0,
]


def main():
    dumps_path = os.path.join(os.path.abspath(os.path.expanduser(os.environ['WOWTHING_DUMP_PATH'])), 'enUS')

    inds = {}
    with open(os.path.join(dumps_path, 'itemnamedescription.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            inds[int(row['ID'])] = row['Description_lang']

    groups = {}
    sets = {}
    with open(os.path.join(dumps_path, 'transmogset.csv')) as csv_file:
        # Name_lang,ID,ClassMask,TrackingQuestID,Flags,TransmogSetGroupID,
        # ItemNameDescriptionID,ParentTransmogSetID,Field_8_1_0_28294_008,
        # ExpansionID,PatchIntroduced,UiOrder,ConditionID
        for row in csv.DictReader(csv_file):
            set_id = int(row['ID'])
            new_set = dict(
                name=row['Name_lang'],
                class_mask=int(row['ClassMask']),
                description_id=int(row['ItemNameDescriptionID']),
                flags=int(row['Flags']),
            )
            sets[set_id] = new_set

            group_id = int(row['TransmogSetGroupID'])
            if group_id > 0:
                groups.setdefault(group_id, []).append(set_id)

    combine = False
    group_mode = False
    output_items = False
    set_mode = False
    item_ids = []
    set_ids = []

    # combined sets
    if sys.argv[1] == 'c':
        combine = True
        set_ids = sys.argv[2:]
    # specific itemIDs
    elif sys.argv[1] == 'i':
        item_ids = sys.argv[2:]
    # MogIt import string
    elif sys.argv[1] == 'm':
        # compare?items=29093:28340:27456:28398:27800:137029:27827:28268
        item_ids = sys.argv[2].split('=')[1].split(':')
    # set names
    elif sys.argv[1] == 'name':
        name_res = []
        for set_name in sys.argv[2:]:
            name_res.append(re.compile(set_name.replace('*', '.*?')))
        for name_re in name_res:
            set_ids.extend(k for k, v in sets.items() if name_re.match(v['name']))
    # sets, item+modifier output
    elif sys.argv[1] == '2':
        output_items = True
        set_ids = sys.argv[2:]
    # sets v2 by group id
    elif sys.argv[1] == 'g2':
        set_mode = True
        if len(sys.argv) == 4:
            set_ids = [set_id for set_id in groups[int(sys.argv[2])] if sets[set_id]['description_id'] == int(sys.argv[3])]
        else:
            set_ids = groups[int(sys.argv[2])]
    # sets v2 by set id
    elif sys.argv[1] == 'ts':
        set_mode = True
        set_ids = sys.argv[2:]
    # sets v1 by group id
    elif sys.argv[1] == 'g':
        group_mode = True
        set_ids = groups[int(sys.argv[2])]
    # sets v1 by set id
    else:
        set_ids = sys.argv[1:]

    item_ids = [int(item_id) for item_id in item_ids]
    set_ids = [int(set_id) for set_id in set_ids]

    set_items = {}
    with open(os.path.join(dumps_path, 'transmogsetitem.csv')) as csv_file:
        # ID,TransmogSetID,ItemModifiedAppearanceID,Flags
        for row in csv.DictReader(csv_file):
            if set_mode and (int(row['Flags']) & 0x1) == 0:
                continue
            set_items.setdefault(int(row['TransmogSetID']), []).append(int(row['ItemModifiedAppearanceID']))

    appearances = {}
    with open(os.path.join(dumps_path, 'itemmodifiedappearance.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            appearances[int(row['ID'])] = [
                int(row['ItemID']),
                int(row['ItemAppearanceID']),
                int(row['ItemAppearanceModifierID']),
            ]

    item_slot = {}
    with open(os.path.join(dumps_path, 'item.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            item_slot[int(row['ID'])] = int(row['InventoryType'])

    if group_mode:
        sort_me = [
            (
                CLASS_MASK.get(sets[set_id]['class_mask'], ''),
                ARMOR_MASK.get(sets[set_id]['class_mask'], ''),
                get_description_order(inds, sets[set_id]['description_id']),
                get_description(sets, set_id),
                set_id,
            ) for set_id in set_ids
        ]
        sort_me.sort()

        old_mask = None
        for (_, _, _, description, set_id) in sort_me:
            mask = sets[set_id]['class_mask']
            if mask in CLASS_MASK and mask != old_mask:
                print(f'    {CLASS_MASK[mask]}:')
                old_mask = mask
            else:
                for armor_type, masks in ARMOR_MASKS.items():
                    if mask in masks:
                        if mask != old_mask:
                            print(f'    {armor_type}:')
                            old_mask = mask
                        break

            print(f'      # {sets[set_id]["name"]} [{description}]')
            print(f'      - transmogSetId: {set_id}')
            print(f'        wowheadSetId:')
            print()

    elif set_mode:
        sort_me = [
            (
                CLASS_MASK.get(sets[set_id]['class_mask'], ''),
                ARMOR_MASK.get(sets[set_id]['class_mask'], ''),
                set_id,
            ) for set_id in set_ids
        ]
        sort_me.sort()

        for (_, _, set_id) in sort_me:
            set = sets[set_id]
            faction = None
            if (set['flags'] & 0x4) == 0x4:
                faction = 'Alliance'
            elif (set['flags'] & 0x8) == 0x8:
                faction = 'Horde'

            if faction:
                print(f'  - name: "transmog:{set_id}" # {set["name"]} [{faction}]')
            else:
                print(f'  - name: "transmog:{set_id}" # {set["name"]}')

            print(f'    tags:')

            mask = set['class_mask']
            if mask in CLASS_MASK:
                print(f'      - "class:{CLASS_MASK[mask]}"')
            elif mask in ARMOR_MASK:
                print(f'      - "armor:{ARMOR_MASK[mask]}"')

            print_items(set_items[set_id], appearances, item_slot, output_items=True, set_mode=True)

    elif item_ids:
        appearance_ids = []
        modifier_appearances = {}
        for item_id in item_ids:
            print(item_id)
            for k, v in appearances.items():
                if item_id == v[0]:
                    modifier_appearances.setdefault(v[2], []).append(k)

        for modifier_id, appearance_ids in reversed(sorted(modifier_appearances.items())):
            print(f'      # modifier={modifier_id}')
            print(f'      - name: "Modifier {modifier_id}"')
            print_items(appearance_ids, appearances, item_slot)

    else:
        old_mask = None

        if combine:
            set_ids.sort()
            print_set_ids = ",".join(str(s) for s in set_ids)
            print_set_name = ' / '.join(list(dict.fromkeys(sets[s]['name'] for s in set_ids)))

            print(f'      # {get_description(sets, set_ids[0])} set={print_set_ids}')
            print(f'      - name: "{print_set_name}"')

            appearance_ids = []
            for set_id in set_ids:
                appearance_ids.extend(set_items[set_id])

            print_items(appearance_ids, appearances, item_slot)

        else:
            sort_me = [
                (
                    CLASS_MASK.get(sets[set_id]['class_mask'], ''),
                    ARMOR_MASK.get(sets[set_id]['class_mask'], ''),
                    get_description_order(inds, sets[set_id]['description_id']),
                    get_description(sets, set_id),
                    set_id,
                ) for set_id in set_ids
            ]
            sort_me.sort()

            for (_, _, _, description, set_id) in sort_me:
                mask = sets[set_id]['class_mask']
                if mask in CLASS_MASK and mask != old_mask:
                    print(f'    {CLASS_MASK[mask]}:')
                    old_mask = mask
                else:
                    for armor_type, masks in ARMOR_MASKS.items():
                        if mask in masks:
                            if mask != old_mask:
                                print(f'    {armor_type}:')
                                old_mask = mask
                            break

                print(f'      # {description} set={set_id}')
                print(f'      - name: "{sets[set_id]["name"]}"')

                print_items(set_items[set_id], appearances, item_slot, output_items)


def get_description_order(inds, description_id):
    if description_id in DESCRIPTION_ORDER:
        return DESCRIPTION_ORDER.index(description_id)
    else:
        print('*** Not in DESCRIPTION_ORDER:', description_id, inds[description_id])
        return description_id

def get_description(sets, set_id):
    description_id = sets[set_id]['description_id']
    flags = sets[set_id]['flags']
    alliance = (flags & 4) > 0
    horde = (flags & 8) > 0

    description = DESCRIPTION_MAP.get(description_id, f'description={description_id}')
    if alliance and not horde:
        description = f'{description} (Alliance)'
    elif horde and not alliance:
        description = f'{description} (Horde)'

    return description

def print_items(appearance_ids, appearances, item_slot, output_items=False, set_mode=False):
    ugh = {}
    for appearance_id in appearance_ids:
        if appearance_id not in appearances:
            print('        # Missing appearance', appearance_id)
            continue

        item_id, item_appearance_id, modifier_id = appearances[appearance_id]
        slot = item_slot[item_id]
        # Why are there 2 chest slots?
        if slot == 20:
            slot = 5
        
        if output_items:
            ugh.setdefault(slot, []).append(item_id)
            if not set_mode:
                ugh[slot].append(modifier_id)
        else:
            ugh.setdefault(slot, []).append(item_appearance_id)


    #print(sets[set_id])
    #print(ugh)
    if set_mode:
        print(f'    items:')
        for thing in sorted(ugh.items(), key=lambda u: SLOT_ORDER.index(u[0])):
            strings = [str(s) for s in output_items and thing[1] or sorted(set(thing[1]))]

            print(f'      - {" ".join(strings)}', '#', SLOT_MAP[thing[0]])
    else:
        print(f'        wowheadSetId:')
        print(f'        items:')
        for thing in sorted(ugh.items()):#, key=lambda u: SLOT_ORDER.index(u[0])):
            s = thing[0] < 10 and '  ' or ' '
            strings = [str(s) for s in output_items and thing[1] or sorted(set(thing[1]))]

            print(f'          {thing[0]}:{s}{" ".join(strings)}', '#', SLOT_MAP[thing[0]])
    
    print()



if __name__ == '__main__':
    main()
