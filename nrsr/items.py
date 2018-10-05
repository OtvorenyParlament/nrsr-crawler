"""
NRSR Items
"""

import scrapy
from scrapy.loader.processors import Join, MapCompose, TakeFirst


def filter_whitespaces(value):
    return value.replace('\xa0', '').strip()


def filter_mailto(value):
    return value.replace('mailto:', '')    


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


class MemberItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    forename = scrapy.Field(output_processor=TakeFirst())
    surname = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    stood_for_party = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=TakeFirst()
    )
    born = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    nationality = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    residence = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    county = scrapy.Field(
        input_processor=MapCompose(filter_whitespaces),
        output_processor=Join()
    )
    email = scrapy.Field(
        input_processor=MapCompose(filter_mailto),
        output_processor=Join()
    )
    images = scrapy.Field()
    image_urls = scrapy.Field()
    period_num = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())

    memberships = scrapy.Field()


class MemberChangeItem(scrapy.Item):
    type = scrapy.Field(output_processor=TakeFirst())
    period_num = scrapy.Field(output_processor=TakeFirst())
    date = scrapy.Field(output_processor=TakeFirst())
    external_id = scrapy.Field(output_processor=TakeFirst())
    change_type = scrapy.Field(output_processor=TakeFirst())
    change_reason = scrapy.Field(output_processor=TakeFirst())


class ParliamentPressItem(scrapy.Item):
    type = scrapy.Field()
    title = scrapy.Field()
    num = scrapy.Field()
    group_num = scrapy.Field()
    period_num = scrapy.Field()
    press_type = scrapy.Field()
    date = scrapy.Field()
    attachments_names = scrapy.Field()
    attachments_urls = scrapy.Field()
    attachments = scrapy.Field()
    raw = scrapy.Field()
    url = scrapy.Field(output_processor=TakeFirst())
