"""
Pipelines
"""

from copy import deepcopy

import pymongo


class NrsrPipeline:

    def __init__(self, mongo_uri, mongo_db, mongo_col, mongo_col_archive):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_col = mongo_col
        self.mongo_col_archive = mongo_col_archive

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE'),
            mongo_col=crawler.settings.get('MONGO_COL'),
            mongo_col_archive=crawler.settings.get('MONGO_COL_ARCHIVE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):

        col = self.db[self.mongo_col]
        item_type = item['type']
        if item_type == 'member':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id'],
                'period_num': item['period_num']
            }
        elif item_type == 'member_change':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id'],
                'period_num': item['period_num'],
                'change_type': item['change_type'],
                'date': item['date']
            }
        elif item_type == 'press':
            match_dict = {
                'type': item_type,
                'press_num': item['press_num'],
                'period_num': item['period_num']
            }

        elif item_type == 'session':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id'],
                'period_num': item['period_num'],
            }
        elif item_type == 'club':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id'],
                'period_num': item['period_num']
            }
        elif item_type == 'voting':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id'],
                'period_num': item['period_num'],
            }
            if 'press_num' in item:
                match_dict['press_num'] = item['press_num']
        elif item_type == 'daily_club':
            match_dict = {
                'type': item_type,
                'period_num': item['period_num'],
                'date': item['date']
            }
        elif item_type == 'bill':
            match_dict = {
                'type': item_type,
                'period_num': item['period_num'],
                'external_id': item['external_id']
            }
        elif item_type == 'bill_step':
            match_dict = {
                'type': item_type,
                'bill_id': item['bill_id'],
                'external_id': item['external_id']
            }
        elif item_type == 'debate_appearance':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id'],
            }
        elif item_type == 'interpelation':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id']
            }
        else:
            raise Exception("unknown type {}".format(item['type']))

        doc = col.find_one(match_dict)
        insert = True
        if doc:
            doc2 = deepcopy(doc)
            del doc2['_id']
            if doc2 != dict(item):
                self.db[self.mongo_col_archive].insert_one(doc)
                col.delete_one({'_id': doc['_id']})
            else:
                insert = False
        if insert:
            col.insert_one(dict(item))
        return item
