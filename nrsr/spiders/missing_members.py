"""
Pull Members which are not reachable directly but are linked in changes
"""

from datetime import datetime
from urllib.parse import urlparse, parse_qs
import scrapy
import pymongo

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import MemberItem


class MissingMembersSpider(NRSRSpider):
    # TODO: parse_member is redundant to members.parse_member
    name = 'missing_members'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        client = pymongo.MongoClient('{}/{}'.format(self.mongo_uri, self.mongo_database))
        db = client['nrsr']
        collection = self.mongo_col
        results1 = db[collection].find({
            'type': 'member_change'
        }, {
            'period_num': 1,
            'external_id': 1
        }).sort([('period_num', 1), ('external_id', 1)])
        results2 = db[collection].find({
            'type': 'member'
        }, {
            'period_num': 1,
            'external_id': 1
        }).sort([('period_num', 1), ('external_id', 1)])

        data1 = [(x['period_num'], x['external_id']) for x in results1]
        data2 = [(x['period_num'], x['external_id']) for x in results2]

        missing = set(data1) - set(data2)
        url_template = 'https://www.nrsr.sk/web/Default.aspx?sid=poslanci/poslanec&PoslanecID={member_id}&CisObdobia={period_num}'
        for item in missing:
            yield scrapy.Request(
                url=url_template.format(member_id=item[1], period_num=int(item[0])),
                callback=self.parse_member)


    def parse_member(self, response):
        item = scrapy.loader.ItemLoader(item=MemberItem())
        url_parsed = urlparse(response.url)

        panel_content = '[@id="_sectionLayoutContainer__panelContent"]'

        item.add_value('type', 'member')
        item.add_value('external_id', int(parse_qs(url_parsed.query)['PoslanecID'][0]))
        try:
            item.add_value('period_num', int(parse_qs(url_parsed.query)['CisObdobia'][0]))
        except:
            pass
        item.add_value('url', response.url)
        item.add_value('forename', response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[1]/span/text()'.format(panel_content)
        ).extract_first())

        item.add_value('surname', response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[3]/span/text()'.format(panel_content)
        ).extract_first())
        title = response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[2]/span/text()'.format(panel_content)
        ).extract_first()
        if not title:
            title = None
        item.add_value('title', title)
        stood_for_party = response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[4]/span/text()'.format(panel_content)
        ).extract_first()
        if not stood_for_party:
            stood_for_party = 'V čase zberu dát neuvedené'
        item.add_value('stood_for_party', stood_for_party)

        item.add_value('born', datetime.strptime(
            response.xpath(
                '//*{}/div[1]/div[1]/div[1]/div[5]/span/text()'.format(panel_content)
            ).extract_first().strip().replace('&nbsp;', ''),
            '%d. %m. %Y').replace(hour=12, minute=0, second=0, microsecond=0)
        )

        item.add_value('nationality', response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[6]/span/text()'.format(panel_content)
        ).extract_first())

        item.add_value('residence', response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[7]/span/text()'.format(panel_content)
        ).extract_first())

        item.add_value('county', response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[8]/span/text()'.format(panel_content)
        ).extract_first())

        item.add_value('email', response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[9]/span/a/@href'.format(panel_content)
        ).extract_first())

        item.add_value('image_urls', response.xpath(
            '//*{}/div[1]/div[2]/div/img/@src'.format(panel_content)).extract())

        # memberships
        memberships = response.xpath(
            '//*{}/div[1]/div[1]/div[2]/ul/li/text()'.format(panel_content)).extract()
        item.add_value('memberships', memberships)
        yield item.load_item()
