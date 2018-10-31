"""
Pull missing press represented in votings but not in press list
"""

from datetime import datetime
from urllib.parse import urlparse

import pymongo
import scrapy
from scrapy.utils.project import get_project_settings

from nrsr.items import PressItem


class MissingPressSpider(scrapy.Spider):
    name = 'missing_presses'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        settings = get_project_settings()
        client = pymongo.MongoClient('{}/{}'.format(
            settings.get('MONGO_URI'), settings.get('MONGO_DATABASE')))
        db = client['nrsr']
        collection = settings.get('MONGO_COL')

        wanted = db[collection].find({
            'type': 'voting'
        }, {
            'period_num': 1,
            'press_num': 1
        })
        having = db[collection].find({
            'type': 'press'
        }, {
            'period_num': 1,
            'num': 1
        })

        wanted_list = [(x['period_num'], x['press_num']) for x in wanted
                       if 'press_num' in x]
        having_list = [(x['period_num'], x['num']) for x in having]

        missing = set(wanted_list) - set(having_list)
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
        try:
            press['press_num'] = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[1]/span/text()'
            ).extract_first().strip()
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
