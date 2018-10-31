"""
Members
"""

from datetime import datetime
from urllib.parse import urlparse, parse_qs
import scrapy

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import MemberItem

class MembersSpider(NRSRSpider):
    name = 'members'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/?SectionId=60',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [self.period]
        else:
            periods = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__currentTerm"]/option/@value'
            ).extract()
            periods = list(map(int, periods))
        i = 0
        for period in periods:
            if i == 0:
                links = response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div/div/ul/li/a/@href').extract()
                for link in links:
                    yield scrapy.Request('%s%s' % (self.BASE_URL, link), callback=self.parse_member)
            i += 1
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            yield scrapy.FormRequest(
                response.request.url,
                formdata={
                    '__EVENTTARGET': '_sectionLayoutContainer$ctl01$_currentTerm',
                    '_sectionLayoutContainer$ctl01$_currentTerm': str(period),
                    '_sectionLayoutContainer$ctl01$ctlListType': 'abc',
                    '__VIEWSTATE': viewstate,
                    '__EVENTVALIDATION': eventvalidation,
                    '__VIEWSTATEGENERATOR': viewstategenerator,
                },
                callback=self.parse_list
            )

    def parse_list(self, response):
        links = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/div/div/ul/li/a/@href').extract()
        for link in links:
            yield scrapy.Request('%s%s' % (self.BASE_URL, link), callback=self.parse_member)


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
        item.add_value('stood_for_party', response.xpath(
            '//*{}/div[1]/div[1]/div[1]/div[4]/span/text()'.format(panel_content)
        ).extract_first())

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
