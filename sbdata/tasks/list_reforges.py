import json
import traceback

import mwparserfromhell.nodes

from sbdata.repo import find_item_by_name
from sbdata.task import register_task, Arguments
from sbdata.wiki import get_wiki_sources_by_title


@register_task("List Reforges")
def list_reforges(args: Arguments):
    all_reforge_ids = []
    for temp in (get_wiki_sources_by_title("Reforging")['Reforging']).filter_templates():
        if temp.name.strip() == 'Reforge_Table_Builder':
            t = ""
            reforgeids = []
            for param in temp.params:
                if param.name == "type":
                    t = str(param.value)
                elif param.showkey == False and str(param.value).strip():
                    reforgeids.append(str(param.value).strip())
            print(f"Type = {t}: {reforgeids}")
            all_reforge_ids += reforgeids

    for reforge in set(all_reforge_ids):
        print(parse_reforge(reforge))


rarity_list = [
    '',
    'COMMON',
    'UNCOMMON',
    'RARE',
    'EPIC',
    'LEGENDARY',
    'MYTHIC',
    'DIVINE'
]

stat_names = dict(
    SA_STR="STRENGTH",
    SA_CC="CRIT_CHANCE",
    SA_SCC="SEA_CREATURE_CHANCE",
    SA_CD="CRIT_DAMAGE",
    SA_INT="INTELLIGENCE",
    SA_AS="BONUS_ATTACK_SPEED",
    SA_HP="HEALTH",
    SA_DEF="DEFENSE",
    SA_SPD="SPEED",
    SA_MF="MAGIC_FIND",
    SA_FERO="FEROCITY",
    SA_DMG="DAMAGE",
    SA_MS="MINING_SPEED",
    SA_MI="MINING_FORTUNE",
    SA_FS="FISHING_SPEED",
)


def parse_reforge(reforge):
    prefix = None
    rarity = None
    applied = None
    stone = None
    cost = None
    stats = {}
    tn = "Template:Reforge/" + reforge
    for t in list(get_wiki_sources_by_title(tn).values())[0].filter_templates():
        if str(t.name).startswith("#switch: {{{type"):
            for param in t.params:
                pn = str(param.name).strip()
                if pn == 'prefix':
                    prefix = str(param.value).strip()
                elif pn == 'rarity':
                    rarity = str(param.value.filter_templates()[0].name)[0]
                elif pn == 'stone':
                    try:
                        stone = str(param.value.filter(forcetype=mwparserfromhell.nodes.Wikilink)[-1].title)
                    except:
                        pass
                elif pn == 'bonus':
                    pass
                elif pn == 'applied':
                    applied = [l.strip().upper().replace(' ', '_')[:-1] for l in str(param.value).split(',')]
                elif pn == 'stats':
                    i = 0
                    for s in param.value.filter_templates():
                        sn = s.name.strip()
                        if sn == '!':
                            i += 1
                            stats[rarity_list[i]] = {}
                        elif sn.startswith('SA'):
                            try:
                                stats[rarity_list[i]][stat_names[sn]] = str(s.params[0].value).strip()
                            except:
                                print(f"Could not parse {s}")
    return {
        'reforge_id': reforge,
        'prefix': prefix,
        'stats': stats,
        'stone': find_item_by_name(stone) if stone else None,
        'applicable': applied
    }
