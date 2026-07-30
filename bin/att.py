import os
import os.path
import re
import sys


STATE_IDLE = 0
STATE_RARES = 1
STATE_NPC = 2
STATE_GROUPS = 3
STATE_SYM_ITEMID = 4

RE_NPC = re.compile(r'^n\((\d+).*?--\s*(.+)$')
RE_COORD = re.compile(r'^\["coord"\] = \{ ([\d\.]+), ([\d\.]+).*?\},$')
RE_QUEST_ID = re.compile(r'^\["questID"\] = (\d+),$')
RE_ITEM = re.compile(r'^i\((\d+)\),.*?--\s*(.+)$')
RE_SYM_ITEM = re.compile(r'(\d+).*?--\s*(.+)$')

def main():
    if len(sys.argv) < 2:
        print('No filename provided')
        return

    filename = sys.argv[1]
    if not os.path.isfile(filename):
        print('File does not exist')
        return
    
    lines = [l.strip() for l in open(filename).readlines()]
    npcs = []
    npc_data = {}
    state = STATE_IDLE

    for line in lines:
        if state == STATE_IDLE:
            if line.startswith('n(RARES,'):
                state = STATE_RARES

        elif state == STATE_RARES:
            m = RE_NPC.match(line)
            if m:
                npc_data['id'] = int(m.group(1))
                npc_data['name'] = m.group(2)
                state = STATE_NPC

        elif state == STATE_NPC:
            m = RE_COORD.match(line)
            if m:
                npc_data['coords'] = f'{m.group(1)} {m.group(2)}'
                continue
            
            m = RE_QUEST_ID.match(line)
            if m:
                npc_data['questId'] = int(m.group(1))
                continue
            
            if line.startswith('["groups"] = '):
                state = STATE_GROUPS
            elif line == '["sym"] = {{"select","itemID",':
                state = STATE_SYM_ITEMID
            elif line == '}),':
                npcs.append(npc_data)
                npc_data = {}
                state = STATE_RARES

        elif state == STATE_GROUPS:
            m = RE_ITEM.match(line)
            if m:
                npc_data.setdefault('items', []).append([
                    int(m.group(1)),
                    m.group(2)
                ])
                continue
            
            if line == '},':
                state = STATE_NPC
            else:
                print(f'STATE_GROUPS #{line}#')

        elif state == STATE_SYM_ITEMID:
            m = RE_SYM_ITEM.match(line)
            if m:
                npc_data.setdefault('items', []).append([
                    int(m.group(1)),
                    m.group(2)
                ])
                continue
            
            if line == '}},':
                state = STATE_NPC
            else:
                print(f'STATE_SYM_ITEMID #{line}#')

        else:
            print(line)
    
    if len(npc_data) > 0:
        npcs.append(npc_data)
    
    print('things:')

    for npc in npcs:
        print(f'  - id: {npc['id']}')
        print(f'    type: "npc"')
        print(f'    name: "{npc['name']}"')

        if 'questId' in npc:
            print(f'    reset: "daily"')
            print(f'    trackingQuestId: {npc['questId']}')

        if 'coords' in npc:
            print()
            print(f'    locations:')
            print(f'      here:')
            print(f'        - {npc['coords']}')

        if 'items' in npc:
            print()
            print(f'    contents:')

            for item in npc['items']:
                print(f'      - id: {item[0]} # {item[1]} []')
        
        print()


if __name__ == '__main__':
    main()
