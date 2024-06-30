import csv
import os
import os.path
import sys


def main():
    dumps_path = os.path.join(os.path.abspath(os.path.expanduser(os.environ['WOWTHING_DUMP_PATH'])), 'enUS')
    
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

    # grep -r "transmogSetId" * | perl -pe 's/^.*?: (\d+).*?$/$1/' | sort -n > sets.txt
    seen_ids = set()
    for line in open('sets.txt').readlines():
        set_id = int(line.strip())
        seen_ids.add(set_id)
    
    set_ids = set(sets.keys())
    unused_ids = set_ids.difference(seen_ids)
    for set_id in sorted(unused_ids):
        print('% 4d # %s' % (set_id, sets[set_id]['name']))

if __name__ == '__main__':
    main()
