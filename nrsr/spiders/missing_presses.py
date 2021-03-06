"""
Pull missing press represented in votings but not in press list
"""

from datetime import datetime
from urllib.parse import urlparse

import pymongo
import scrapy

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import PressItem


class MissingPressSpider(NRSRSpider):
    name = 'missing_presses'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        client = pymongo.MongoClient('{}/{}'.format(
            self.mongo_uri, self.mongo_database))
        db = client['nrsr']
        collection = self.mongo_col

        wanted = db[collection].find({
            'type': {'$in': ['voting', 'debate_appearance']},
            'period_num': int(self.period)
        }, {
            'period_num': 1,
            'press_num': 1
        })
        wanted2 = db[collection].aggregate([
            {'$match': {'type': 'committeeschedule', 'period_num': int(self.period)}},
            {'$unwind': '$points'},
            {'$project': {'press_num': '$points.press_num', 'period_num': '$period_num'}}
        ])
        wanted2_list = [(x['period_num'], x['press_num']) for x in wanted2 if 'press_num' in x and x['press_num']]
        
        having = db[collection].find({
            'type': 'press',
            'period_num': int(self.period)
        }, {
            'period_num': 1,
            'press_num': 1
        })

        wanted_list = [(x['period_num'], x['press_num'][0] if isinstance(x['press_num'], list) else x['press_num']) for x in wanted
                       if 'press_num' in x]
        having_list = [(x['period_num'], x['press_num']) for x in having]
        missing = set(wanted_list + wanted2_list) - set(having_list)
        url_template = 'https://www.nrsr.sk/web/Default.aspx?sid=zakony/cpt&CisObdobia={period_num}&ID={external_id}'

        for item in missing:
            period_num = int(item[0])
            yield scrapy.Request(
                url=url_template.format(
                    external_id=item[1], period_num=period_num),
                meta={'period_num': period_num},
                callback=self.parse_press)

    def parse_press(self, response):
        press = PressItem()
        press['period_num'] = response.meta['period_num']
        press['type'] = 'press'
        try:
            press['title'] = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[4]/span/text()'
            ).extract_first().strip()
        except KeyError:
            press['title'] = None
        except AttributeError:
            raise scrapy.exceptions.DropItem
        try:
            press['press_num'] = int(response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[1]/span/text()'
            ).extract_first().strip())
        except KeyError:
            press['press_num'] = None
        try:
            press['press_type'] = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[2]/span/text()'
            ).extract_first().strip()
        except KeyError:
            press['press_type'] = None
        try:
            press['date'] = datetime.strptime(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[3]/span/text()'
                ).extract_first().strip(),
                '%d. %m. %Y').replace(hour=12, minute=0, second=0, microsecond=0)
        except ValueError:
            press['date'] = datetime.strptime(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[3]/span/text()'
                ).extract_first().strip(),
                '%d.%m.%Y').replace(hour=12, minute=0, second=0, microsecond=0)
        except KeyError:
            press['date'] = None
        press['attachments_names'] = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[5]/span/a/text()'
        ).extract()
        attachments = []
        for x in response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[5]/span/a'
        ):
            attachments.append({
                'url':
                '{}{}'.format(self.BASE_URL,
                              x.xpath('@href').extract_first()),
                'name':
                x.xpath('text()').extract_first().strip(),
            })
        press['attachments_names'] = attachments
        press['attachments_urls'] = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[5]/span/a/@href'
        ).extract()
        press['url'] = response.url
        yield press
