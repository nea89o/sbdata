import json

import mwparserfromhell.nodes

from sbdata.repo import find_item_by_name, item_list, Item, save_modified_file
from sbdata.task import register_task, Arguments
from sbdata.wiki import get_wiki_sources_by_title

# Format:
# <stat>_<postfix>(optional rest of postfix) -> before upgrade rarity index
rarity_postfixes = {
    'c': 0,
    'u': 1,
    'r': 2,
    'e': 3,
    'l': 4
}


@register_task("Find Kat Recipes")
def find_kat_recipes(args: Arguments):
    itemids = set()
    for item in item_list.values():
        if "Lvl" in item.displayname and ';' in item.internalname:
            itemids.add(item.internalname.split(';')[0])
    print(f"Analyzing: {itemids}")
    for itemid in itemids:
        analyze_pet(itemid)


def analyze_pet(itemid: str):
    x = next(iter(get_wiki_sources_by_title('_'.join(x.capitalize() for x in itemid.split('_')) + '_Pet', wiki_host='hypixel-skyblock.fandom.com').values()))
    for t in x.filter_templates():
        if t.name.strip() == 'Kat Cost table':
            t: mwparserfromhell.nodes.Template
            for rarity_postfix, rarity_before_idx in rarity_postfixes.items():
                costp = find_param(t, 'cost', rarity_postfix)
                matsp = find_param(t, 'mats', rarity_postfix)
                timep = find_param(t, 'time', rarity_postfix)
                if None in [costp, timep]:
                    print(f"Missing data for {rarity_postfix} in {itemid}")
                    continue
                cost = parse_coins(costp.value.strip_code())
                time = parse_time(timep.value.strip_code())
                mats = parse_mats(matsp.value.strip_code()) if matsp else []
                # print(f"Upgrading from {rarity_before_idx} to {rarity_before_idx + 1} using {mats} and {cost} coins in {time} seconds")
                from sbdata.repo import get_item_file
                itemfile = get_item_file(itemid + ';' + str(rarity_before_idx + 1))
                itemjson = json.loads(itemfile.read_text())
                itemjson['recipes'] = [dict(
                    type='katgrade',
                    coins=cost,
                    time=time,
                    input=f'{itemid};{rarity_before_idx}',
                    output=f'{itemid};{rarity_before_idx + 1}',
                    items=[f'{x[0].internalname}:{str(x[1])}' for x in mats]
                )] + [r for r in itemjson.get('recipes', []) if r.get('type') != 'katgrade']
                save_modified_file(itemfile, itemjson)
            break


postfix_numbers = dict(
    k=1000,
    m=1000000,
)


def parse_coins(a: str):
    a = a.lower().replace('coins', '').replace('coin', '').replace(',', '').strip()
    try:
        return int(a)
    except ValueError:
        pass
    for pn, pi in postfix_numbers.items():
        if a.endswith(pn):
            return int(a[:-len(pn)]) * pi
    raise ""


def parse_mats(a: str) -> [(Item, int)]:
    r = []
    for b in a.split('*'):
        b = b.strip()
        if not b or b.lower() == 'none' or b.lower() == 'n/a':
            continue
        x = b.split(",")
        if len(x) != 2:
            raise ""
        i = find_item_by_name(x[0])
        if not i:
            raise ""
        r += [(i, int(x[1]))]
    return r


times = {
    'second': 1,
    'seconds': 1,
    'minute': 60,
    'minutes': 60,
    'hour': 60 * 60,
    'hours': 60 * 60,
    'day': 60 * 60 * 24,
    'days': 60 * 60 * 24,
}


def parse_time(a: str) -> int:
    # returns seconds
    n = -1
    t = 0
    for p in a.split():
        p = p.strip().lower()
        if not p:
            continue
        if p.isdigit():
            if n > 0:
                raise "Double number"
            n = int(p)
            continue
        if p not in times:
            raise "Unknown time"
        t = n * times[p]
        n = -1
    if t == 0:
        raise ""
    return t


def find_param(t: mwparserfromhell.nodes.Template, name: str, rp: str) -> mwparserfromhell.nodes.template.Parameter:
    s = name + '_' + rp
    for p in t.params:
        if p.name.strip().startswith(s):
            return p
