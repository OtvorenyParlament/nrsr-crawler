"""
NRSR Items
"""

import scrapy
from scrapy.loader.processors import TakeFirst


class ClubItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    name = scrapy.Field(output_processor=TakeFirst())
    email = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    members = scrapy.Field()
    url = scrapy.Field()


class ClubMemberItem(scrapy.Item):
    external_id = scrapy.Field()
    membership = scrapy.Field()
