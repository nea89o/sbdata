import dataclasses
import json
import os
import pathlib
import re
import typing

item_list = {}
repo_dir = pathlib.Path(os.environ.get('REPO_DIR', 'NotEnoughUpdates-REPO'))


@dataclasses.dataclass
class Item:
    displayname: str
    itemid: str
    internalname: str
    lore: list[str]


def unformat_name(name: str) -> str:
    return re.sub('§.', '', name)


def bare_name(name: str) -> str:
    name = unformat_name(name).replace("'", '').lower()
    if name.startswith('ultimate'):
        name = name[8:]
    return name.strip()


def load_item(item: pathlib.Path):
    with item.open('r', encoding='utf-8') as fp:
        data = json.load(fp)
        item_list[data['internalname']] = Item(data['displayname'], data['itemid'], data['internalname'], data['lore'])


def find_item_by_name(name: str) -> typing.Optional[Item]:
    name = bare_name(name)
    pot = [item for item in item_list.values()
           if item.internalname.casefold() == name
           or bare_name(item.displayname) == name
           or (item.itemid == 'minecraft:enchanted_book'
               and bare_name(item.lore[0]).endswith(name))]
    if pot:
        return pot[0]
    return None


def load_items():
    item_dir = repo_dir / 'items'
    for item in item_dir.iterdir():
        if item.name.endswith('.json'):
            load_item(item)


def load_repo_data():
    item_list.clear()
    load_items()


load_repo_data()
