"""
Pipelines
"""

from copy import deepcopy

import pymongo


class NrsrPipeline(object):

    collection_name = 'crawled_data'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):

        col = self.db[self.collection_name]
        item_type = item['type']
        if item_type == 'club':
            match_dict = {
                'type': item_type,
                'external_id': item['external_id'],
                'period_num': item['period_num']
            }
        else:
            raise Exception("unknown type {}".format(item['type']))

        doc = col.find_one(match_dict)
        insert = True
        if doc:
            doc2 = deepcopy(doc)
            del doc2['_id']
            if doc2 != dict(item):
                self.db['crawled_archive'].insert_one(doc)
                col.delete_one({'_id': doc['_id']})
            else:
                insert = False
        if insert:
            col.insert_one(dict(item))
        return item
