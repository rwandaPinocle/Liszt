from tinydb import TinyDB, Query
from dataElements import Card, Board, _List

'''
Date: ISO formatted date strings

Card Schema
{
    _id: id
    name: str,
    content: str,
    dueDate: Date,
    dateAdded: Date,
    userData: {str: float, int, or str}
    parentId: id
}

List Schema
{
    _id: id,
    name: str,
    dateAdded: Date,
    parentId: id
}

Board Schema
{
    _id: id,
    name: str,
    dateAdded: Date,
    desc: str,
}
'''


def dictify(item):
    if type(item) in [int, str, float]:
        result = item
    elif type(item) == list:
        result = [dictify(subitem) for subitem in item]
    else:
        result = {}
        for key, value in item.__dict__:
            result[key] = dictify(value)
    return result


class Adapter:
    def __init__(self, path):
        self.db = TinyDB(path)
        self.boards = self.db.table('boards')
        self.lists = self.db.table('lists')
        self.cards = self.db.table('cards')
        return

    def create(self, item):
        tableMap = {Card: self.cards, _List: self.lists, Board: self.board}
        table = tableMap[type(item)]
        table.insert(dictify(item))
        return

    def getChildren(self, item=None):
        tableMap = {Board: self.lists, _List: self.cards}
        table = tableMap[type(item)]

        typeMap = {Board: _List, _List: Card}
        childType = typeMap[type(item)]

        children = table.search(Query().parentId == item._id)
        return [childType(**data) for data in children]

    def move(self, item, dest):
        parentClsMap = {Card: _List, _List: Board}
        parentCls = parentClsMap[type(item)]
        if parentCls != type(dest):
            raise TypeError(f'Dest is incorrect type {type(dest)}')
        item.parentId = dest._id

        self.update(item)
        return

    def update(self, item):
        tableMap = {Card: self.cards, _List: self.lists, Board: self.board}
        table = tableMap[type(item)]

        Child = Query()
        table.update(dictify(item), Child._id == item._id)
        return

    def delete(self, item):
        tableMap = {Card: self.cards, _List: self.lists, Board: self.board}
        table = tableMap[type(item)]
        table.delete(doc_ids=[item._id])
        return

    # TODO: Fill out clean function
    def clean(self):
        ''' Go through and delete all orphan items '''
        pass
