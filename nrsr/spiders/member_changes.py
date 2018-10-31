"""
Member Changes
"""

import re
from urllib.parse import urlencode, urlparse, parse_qs
import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import MemberChangeItem


class MemberChangesSpider(NRSRSpider):
    name = 'member_changes'
    BASE_URL = 'https://www.nrsr.sk/web/'
    crawled_pages = {}

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/default.aspx?sid=poslanci/zmeny',

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
            body = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__EVENTVALIDATION': eventvalidation,
                '__SCROLLPOSITONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '_sectionLayoutContainer$ctl01$_currentTerm': str(period),
                '_sectionLayoutContainer$ctl01$ctlListType': 'abc',
                '_searchText': '',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '8',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '8',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018'
            }
            yield SplashRequest(
                response.url,
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body)
                }
            )

    def parse_pages(self, response):
        if self.daily:
            pages = []
        else:
            pages = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__ResultGrid2"]/tbody/tr[1]/td/table/tbody/tr/td/a/@href'
            ).extract()
        pages = list(set(pages))
        period = int(response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__currentTerm"]/option[@selected="selected"]/@value'
        ).extract_first())
        current_page = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__ResultGrid2"]/tbody/tr[1]/td/table/tbody/tr/td/span/text()'
        ).extract()
        if current_page[0].isdigit():
            crawled_string = '{}_{}'.format(period, current_page[0])
        for page in pages:
            page_match = re.match(r'.*(Page.*[0-9]).*', page)
            if not page_match:
                continue
            eventargument = page_match.groups()[0]
            page_num = eventargument.split('$')[-1]
            crawled_string = '{}_{}'.format(period, page_num)
            if crawled_string in self.crawled_pages:
                print("{} already crawled".format(crawled_string))
                continue
            else:
                self.crawled_pages[crawled_string] = True
            viewstate = response.css(
                'input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css(
                'input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css(
                'input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css(
                'input#__SCROLLPOSITIONX::attr(value)').extract_first()
            scroll_y = response.css(
                'input#__SCROLLPOSITIONY::attr(value)').extract_first()
            post_action = response.xpath(
                '//*[@id="_f"]/@action').extract_first()
            eventtarget = '_sectionLayoutContainer$ctl01$_ResultGrid2'
            body = {
                '__EVENTTARGET': eventtarget,
                '__EVENTARGUMENT': eventargument,
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__EVENTVALIDATION': eventvalidation,
                '__SCROLLPOSITONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '_sectionLayoutContainer$ctl01$_currentTerm': str(period),
                '_searchText': '',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '8',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '8',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018'
            }

            yield SplashRequest(
                # response.url,
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    # 'url': response.meta['url'],
                    'body': urlencode(body),
                },
                # meta=meta,
                meta={'page': True})

        items = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__ResultGrid2"]/tbody/tr[@class="tab_zoznam_alt" or @class="tab_zoznam_nonalt"]'
        )
        for item in items:
            change = scrapy.loader.ItemLoader(item=MemberChangeItem())
            url_parsed = urlparse(item.xpath('td[2]/a/@href').extract_first())
            change.add_value('external_id',
                             parse_qs(url_parsed.query)['PoslanecID'][0])
            change.add_value('type', 'member_change')
            change.add_value('date',
                             item.xpath('td[1]/text()').extract_first())
            change.add_value('period_num', period)
            change.add_value('change_type',
                             item.xpath('td[3]/text()').extract_first())
            change.add_value('change_reason',
                             item.xpath('td[4]/text()').extract_first())
            yield change.load_item()
