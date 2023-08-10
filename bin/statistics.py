import csv
import os
import os.path
import re
import sys


ENCOUNTER_NAME_OVERRIDES = {
    'Raszageth the Storm-Eater': 'Raszageth',
}

DUNGEON_DIFFICULTIES = [
    [1, 'Normal'],
    [2, 'Heroic'],
    [23, 'Mythic'],
]
DUNGEON_DIFFICULTY_MAP = {k: v for k, v in DUNGEON_DIFFICULTIES}

RAID_DIFFICULTIES = [
    [3, '10-player Normal'],
    [4, '25-player Normal'],
    [5, '10-player Heroic'],
    [6, '25-player Heroic'],
    [7, 'LFR'],

    [9, '40 player'],

    [14, 'Normal'],
    [15, 'Heroic'],
    [16, 'Mythic'],
    [17, 'Raid Finder'],
]
RAID_DIFFICULTY_MAP = {k: v for k, v in RAID_DIFFICULTIES}


def main():
    dumps_path = os.path.join(os.path.abspath(os.path.expanduser(os.environ['WOWTHING_DUMP_PATH'])), 'enUS')

    achievements = {}
    with open(os.path.join(dumps_path, 'achievement.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            flags = int(row['Flags'])
            id = int(row['ID'])
            instance_id = int(row['Instance_ID'])
            title = row['Title_lang']
            if (flags & 1) == 1:
                achievements[title.lower()] = [id, instance_id]

    difficulties = {}
    with open(os.path.join(dumps_path, 'difficulty.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            id = int(row['ID'])
            instance_type = int(row['InstanceType'])
            name = row['Name_lang']
            if instance_type in [2]: # raid
                difficulties[id] = name

    instances = []
    with open(os.path.join(dumps_path, 'journalinstance.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            id = int(row['ID'])
            name = row['Name_lang']
            instances.append([id, name])
    
    instance_encounters = {}
    with open(os.path.join(dumps_path, 'journalencounter.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            id = int(row['ID'])
            instance_id = int(row['JournalInstanceID'])
            order_index = int(row['OrderIndex'])
            name = row['Name_lang']
            instance_encounters.setdefault(instance_id, []).append([
                order_index,
                id,
                ENCOUNTER_NAME_OVERRIDES.get(name, name),
            ])
    
    encounter_difficulties = {}
    with open(os.path.join(dumps_path, 'journalencounterxdifficulty.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            difficulty = int(row['DifficultyID'])
            encounter_id = int(row['JournalEncounterID'])
            encounter_difficulties.setdefault(encounter_id, []).append(difficulty)
    
    maps = {}
    with open(os.path.join(dumps_path, 'map.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            id = int(row['ID'])
            instance_type = int(row['InstanceType'])
            maps[id] = instance_type

    for [instance_id, instance_name] in instances:
        printed_instance = False
        encounters = sorted(instance_encounters.get(instance_id, []))
        for [order, encounter_id, encounter_name] in encounters:
            printed_encounter = False
            for [difficulty, difficulty_name] in DUNGEON_DIFFICULTIES + RAID_DIFFICULTIES:
                stat_title = None
                if difficulty_name == '40 player':
                    stat_title = f'{encounter_name} kills ({instance_name})'
                else:
                    stat_title = f'{encounter_name} kills ({difficulty_name} {instance_name})'

                achievement_data = achievements.get(stat_title.lower()) or \
                    achievements.get(stat_title.replace(' kills ', ' ').lower())

                if achievement_data is None and ', ' in encounter_name:
                    stat_title = stat_title.replace(encounter_name, encounter_name.split(', ')[0])
                    achievement_data = achievements.get(stat_title.lower()) or \
                        achievements.get(stat_title.replace(' kills ', ' ').lower())

                if achievement_data is None:
                    continue

                achievement_id, map_id = achievement_data

                if map_id > 0 and map_id in maps:
                    map_type = maps[map_id]
                    if map_type == 1 and difficulty not in DUNGEON_DIFFICULTY_MAP:
                        # print(f'# not a dungeon?? achievement={achievement_id} map={map_id} instance={instance_name} difficulty={difficulty} type={map_type}')
                        continue
                    elif map_type == 2 and difficulty not in RAID_DIFFICULTY_MAP:
                        # print(f'# not a raid?? achievement={achievement_id} map={map_id} instance={instance_name} difficulty={difficulty} type={map_type}')
                        continue

                if not printed_instance:
                    printed_instance = True
                    print()
                    print('#' * 50)
                    print(f'# {instance_id} {instance_name}')
                    print('#' * 50)
                
                if not printed_encounter:
                    printed_encounter = True
                    print()
                    print(f'{encounter_id}: # {encounter_name}')

                print(f'  {difficulty}: {achievement_id} # {difficulty_name}')
                    
            #for difficulty in sorted(encounter_difficulties.get(encounter_id, [])):
            #    if difficulty not in difficulties:
            #        continue
            #    print(encounter_id, encounter_name, difficulty)
            #    #print(f'# {instance_id} {instance_name}')
            


if __name__ == '__main__':
    main()
