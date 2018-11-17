"""
Parliament Press Spider
"""

from datetime import datetime, timedelta
import re
from urllib.parse import urlencode, urlparse, parse_qs
import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import PressItem


class PressSpider(NRSRSpider):
    name = 'presses'
    BASE_URL = 'https://www.nrsr.sk/web/'
    crawled_pages = {}

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=schodze%2fcpt&Text=&CisObdobia=7&FullText=False&TypTlaceID=-1'

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        if self.period:
            periods = [self.period]
        else:
            periods = response.xpath(
                '//*/select[@id="_sectionLayoutContainer_ctl01_ctlCisObdobia"]/option/@value').extract()
            periods = list(map(int, periods))

        for period in periods:
            if period == 1:
                continue
            # parse period
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
            body = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__EVENTVALIDATION': eventvalidation,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$ctlNazov': '',
                '_sectionLayoutContainer$ctl01$ctlCisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$ctlCPT': '',
                '_sectionLayoutContainer$ctl01$ctlTypTlace': '-1',
                '_sectionLayoutContainer$ctl01$DatumOd': self.date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$Type': 'optSearchType',
                '_sectionLayoutContainer$ctl01$cmdSearch': 'Vyhľadať',
                '_sectionLayoutContainer$ctl01$ctl00$txtDescriptorText': '',
                '_sectionLayoutContainer$ctl01$ctl00$cboLanguages': '3',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '9',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrcpt_all',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '9',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018'
            }

            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body),
                }
            )


    def parse_pages(self, response):
        pages = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01_dgResult2"]/tbody/tr[1]/td/table/tbody/tr/td/a/@href'
        ).extract()
        pages = list(set(pages))
        post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
        url_parsed = urlparse(post_action)
        url_qs = parse_qs(url_parsed.query)
        period = int(url_qs['CisObdobia'][0])
        current_page = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01_dgResult2"]/tbody/tr[1]/td/table/tbody/tr/td/span/text()'
        ).extract()

        if not current_page:
            current_page = '1'

        initial_string = '{}_{}'.format(period, current_page)
        if not initial_string in self.crawled_pages:
            self.crawled_pages[initial_string] = True

        cleaned_pages = []
        for page in pages:
            page_match = re.match(r'.*(Page.*[0-9]).*', page)
            if not page_match:
                continue
            page_num = page_match.groups()[0].split('$')[-1]
            crawled_string = '{}_{}'.format(period, page_num)
            if crawled_string in self.crawled_pages:
                print("{} already crawled".format(crawled_string))
                continue
            cleaned_pages.append(page_match.groups()[0])

        for page in cleaned_pages:
            eventargument = page
            page_num = eventargument.split('$')[-1]
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            eventtarget = '_sectionLayoutContainer$ctl01$dgResult2'
            body = {
                '__EVENTTARGET': eventtarget,
                '__EVENTARGUMENT': eventargument,
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__EVENTVALIDATION': eventvalidation,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$ctlNazov': '',
                '_sectionLayoutContainer$ctl01$ctlCisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$ctlCPT': '',
                '_sectionLayoutContainer$ctl01$ctlTypTlace': '-1',
                '_sectionLayoutContainer$ctl01$DatumOd': self.date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$Type': 'optSearchType',
                '_sectionLayoutContainer$ctl01$ctl00$txtDescriptorText': '',
                '_sectionLayoutContainer$ctl01$ctl00$cboLanguages': '3',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '9',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrcpt_all',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '9',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018'
            }
            if not crawled_string in self.crawled_pages:
                self.crawled_pages[crawled_string] = True
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body),
                },
                meta={'page': True}
            )

        items = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_dgResult2"]/tbody/tr[position()>1]')
        for item in items:
            press_url = item.xpath('td[1]/a/@href').extract_first()
            if press_url:
                url = '{}{}'.format(self.BASE_URL, press_url)
                yield scrapy.Request(
                    url,
                    callback=self.parse_press,
                    meta={'period_num': period}
                )

    def parse_press(self, response):
        press = PressItem()
        press['period_num'] = response.meta['period_num']
        press['type'] = 'press'
        try:
            press['title'] = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[4]/span/text()').extract_first().strip()
        except KeyError:
            press['title'] = None
        try:
            press['press_num'] = int(response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[1]/span/text()').extract_first().strip())
        except KeyError:
            press['press_num'] = None
        try:
            press['press_type'] = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[2]/span/text()').extract_first().strip()
        except KeyError:
            press['press_type'] = None
        try:
            press['date'] = datetime.strptime(response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[3]/span/text()').extract_first().strip(),
                '%d. %m. %Y'
            ).replace(hour=12, minute=0, second=0, microsecond=0)
        except KeyError:
            press['date'] = None
        press['attachments_names'] = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[5]/span/a/text()').extract()
        attachments = []
        for x in response.xpath('//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[5]/span/a'):
            attachments.append({
                'url': '{}{}'.format(self.BASE_URL, x.xpath('@href').extract_first()),
                'name': x.xpath('text()').extract_first().strip(),
            })
        press['attachments_names'] = attachments
        press['attachments_urls'] = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__cptPanel"]/div/div[5]/span/a/@href').extract()
        press['url'] = response.url
        yield press
