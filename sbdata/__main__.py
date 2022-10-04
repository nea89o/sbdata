import dataclasses
import json
import sys
from typing import Any

import questionary
import rich
import rich.table
from sbdata.repo import Item
from sbdata.task import Arguments, tasks


class ObjectEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        if isinstance(o, Item):
            return o.internalname
        if dataclasses.is_dataclass(o):
            return o.__dict__
        return super().default(o)


def render_thing(i):
    if isinstance(i, Item):
        return i.internalname
    return str(i)


def main():
    args = Arguments(sys.argv)
    task = args.get_value(
        'Task', tasks.get(args.task),
        questionary.select('Which task do you want to execute?', choices=[
            questionary.Choice(task.label, task) for task in tasks.values()
        ]))
    print("Selected task: " + task.label)
    data = task.run(args)
    if args.has_flag('json'):
        print(json.dumps(data, cls=ObjectEncoder))
    if args.has_flag('explore'):
        if not (isinstance(data, list) and len(data) > 0 and dataclasses.is_dataclass(data[0])):
            print('Cannot explore this')
            return
        console = rich.get_console()
        keys = list(data[0].__dict__.keys())
        query = ''
        while True:
            table = rich.table.Table(show_footer=True)
            for k in keys:
                table.add_column(header=k, footer=k)
            for item in data:
                if any(query in render_thing(val).casefold() for val in item.__dict__.values()):
                    table.add_row(*[render_thing(getattr(item, k)) for k in keys])
            console.print(table)
            query = console.input("Search: ").casefold()


if __name__ == '__main__':
    main()
