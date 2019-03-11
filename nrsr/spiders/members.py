"""
Members
"""

from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
import scrapy
from scrapy_splash import SplashRequest

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
        for period in periods:
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()

            body = {
                '__EVENTTARGET': '_sectionLayoutContainer$ctl01$_currentTerm',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__VIEWSTATE': viewstate,
                '__EVENTVALIDATION': eventvalidation,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_currentTerm': str(period),
                '_sectionLayoutContainer$ctl01$ctlListType': 'abc',
                '_sectionLayoutContainer$ctl01$ctlShow': 'Zobraziť',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2019',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2019',
            }

            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_list,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body)
                },
                meta={'period_num': period}
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

        # GDPR
        # item.add_value('born', datetime.strptime(
        #     response.xpath(
        #         '//*{}/div[1]/div[1]/div[1]/div[5]/span/text()'.format(panel_content)
        #     ).extract_first().strip().replace('&nbsp;', ''),
        #     '%d. %m. %Y').replace(hour=12, minute=0, second=0, microsecond=0)
        # )

        # item.add_value('nationality', response.xpath(
        #     '//*{}/div[1]/div[1]/div[1]/div[6]/span/text()'.format(panel_content)
        # ).extract_first())

        # item.add_value('residence', response.xpath(
        #     '//*{}/div[1]/div[1]/div[1]/div[7]/span/text()'.format(panel_content)
        # ).extract_first())

        # item.add_value('county', response.xpath(
        #     '//*{}/div[1]/div[1]/div[1]/div[8]/span/text()'.format(panel_content)
        # ).extract_first())

        # item.add_value('email', response.xpath(
        #     '//*{}/div[1]/div[1]/div[1]/div[9]/span/a/@href'.format(panel_content)
        # ).extract_first())

        item.add_value('image_urls', response.xpath(
            '//*{}/div[1]/div[2]/div/img/@src'.format(panel_content)).extract())

        # memberships
        memberships = response.xpath(
            '//*{}/div[1]/div[1]/div[2]/ul/li/text()'.format(panel_content)).extract()
        item.add_value('memberships', memberships)
        yield item.load_item()
