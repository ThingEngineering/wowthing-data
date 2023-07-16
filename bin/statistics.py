import csv
import os
import os.path
import re
import sys


DIFFICULTIES = [
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

ENCOUNTER_NAME_OVERRIDES = {
    'Raszageth the Storm-Eater': 'Raszageth',
}


def main():
    dumps_path = os.path.join(os.path.abspath(os.path.expanduser(os.environ['WOWTHING_DUMP_PATH'])), 'enUS')

    achievements = {}
    with open(os.path.join(dumps_path, 'achievement.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            id = int(row['ID'])
            title = row['Title_lang']
            if ' kills ' in title:
                achievements[title.lower()] = id

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
    

    for [instance_id, instance_name] in instances:
        printed_instance = False
        encounters = sorted(instance_encounters.get(instance_id, []))
        for [order, encounter_id, encounter_name] in encounters:
            printed_encounter = False
            for [difficulty, difficulty_name] in DIFFICULTIES:
                if difficulty_name == '40 player':
                    stat_title = f'{encounter_name} kills ({instance_name})'
                else:
                    stat_title = f'{encounter_name} kills ({difficulty_name} {instance_name})'

                if stat_title.lower() in achievements:
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

                    print(f'  {difficulty}: {achievements[stat_title.lower()]} # {difficulty_name}')
                    
            #for difficulty in sorted(encounter_difficulties.get(encounter_id, [])):
            #    if difficulty not in difficulties:
            #        continue
            #    print(encounter_id, encounter_name, difficulty)
            #    #print(f'# {instance_id} {instance_name}')
            


if __name__ == '__main__':
    main()
