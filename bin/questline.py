import csv
import json
import os
import sys


def main():
    dumps_path = os.path.join(os.path.abspath(os.path.expanduser(os.environ['WOWTHING_DUMP_PATH'])), 'enUS')

    achievement_to_criteria_tree = {}
    with open(os.path.join(dumps_path, 'achievement.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            achievement_to_criteria_tree[int(row['ID'])] = int(row['Criteria_tree'])
    
    criterias = {}
    with open(os.path.join(dumps_path, 'criteria.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            if int(row['Type']) == 27:
                criterias[int(row['ID'])] = int(row['Asset'])

    criteria_tree_parents = {}
    with open(os.path.join(dumps_path, 'criteriatree.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            parent_id = int(row['Parent'])
            if parent_id:
                criteria_tree_parents.setdefault(parent_id, []).append([
                    int(row['OrderIndex']), int(row['CriteriaID']), row['Description_lang']
                ])
    
    questline_x_quests = {}
    with open(os.path.join(dumps_path, 'questlinexquest.csv')) as csv_file:
        for row in csv.DictReader(csv_file):
            questline_x_quests[int(row['QuestID'])] = int(row['QuestLineID'])

    achievement_id = int(sys.argv[1])
    criteria_tree_id = achievement_to_criteria_tree[achievement_id]
    if criteria_tree_id is None:
        print('bad achievement?', achievement_id)
        return
    
    criteria_tree = criteria_tree_parents[criteria_tree_id]
    if criteria_tree is None:
        print('bad criteriatree?', criteria_tree_id)
        return
    
    criteria_tree.sort()
    for order, criteria_id, description in criteria_tree:
        quest_id = criterias.get(criteria_id)
        if quest_id and questline_x_quests[quest_id]:
            print(f'      - id: {questline_x_quests[quest_id]} # {description}')
        else:
            print(f'      # - id: ?? # {description}')

if __name__ == '__main__':
    main()
