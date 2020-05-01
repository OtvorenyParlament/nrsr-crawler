"""
Interpellations Spider
"""

from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, parse_qs, urlencode
import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import InterpellationItem


class InterpellationsSpider(NRSRSpider):

    name = 'interpellations'
    BASE_URL = 'https://www.nrsr.sk/web/'
    crawled_pages = {}
    crawled_interpellations = {}

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=schodze/interpelacie_result',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [self.period]
        else:
            periods = response.xpath(
                '//*/select[@id="_sectionLayoutContainer_ctl01_ctlCisObdobia"]/option/@value'
            ).extract()
            periods = list(map(int, periods))

        for period in periods:
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css(
                'input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
            body = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$ctlText': '',
                '_sectionLayoutContainer$ctl01$ctlCisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$ctlAdresat': '',
                '_sectionLayoutContainer$ctl01$_mpsCombo': '-1',
                '_sectionLayoutContainer$ctl01$ctlZadavatelKlub': '',
                '_sectionLayoutContainer$ctl01$_meetingNrIntCombo': '0',
                '_sectionLayoutContainer$ctl01$_meetingNrOdpCombo': '0',
                '_sectionLayoutContainer$ctl01$ctlCPT': '',
                '_sectionLayoutContainer$ctl01$DatumOd': self.date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$_stateCombo': '',
                '_sectionLayoutContainer$ctl01$Type': 'optSearchType',
                '_sectionLayoutContainer$ctl01$cmdSearch': 'Vyhľadať',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',
            }

            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body)
                },
                meta={'period_num': period}
            )

    def parse_pages(self, response):
        pages = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01_dgResult"]/tbody/tr[1]/td/table/tbody/tr/td/a/@href'
        ).extract()
        pages = list(set(pages))
        period = response.meta['period_num']
        current_page = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01_dgResult"]/tbody/tr[1]/td/table/tbody/tr/td/span/text()'
        ).extract_first()

        if not current_page:
            current_page = '1'

        initial_string = '{}_{}'.format(period, current_page)
        if initial_string not in self.crawled_pages:
            self.crawled_pages[initial_string] = True

        cleaned_pages = []
        for page in pages:
            page_match = re.match(r'.*(Page.*[0-9]).*', page)
            if not page_match:
                continue
            page_num = page_match.groups()[0].split('$')[-1]
            crawled_string = '{}_{}'.format(period, page_num)

            if crawled_string in self.crawled_pages:
                continue
            cleaned_pages.append(page_match.groups()[0])

        for page in cleaned_pages:
            eventargument = page
            page_num = page.split('$')[-1]
            crawled_string = '{}_{}'.format(period, page_num)

            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
            body = {
                '__EVENTTARGET': '_sectionLayoutContainer$ctl01$dgResult',
                '__EVENTARGUMENT': eventargument,
                '__LASTFOCUS': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$ctlText': '',
                '_sectionLayoutContainer$ctl01$ctlCisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$ctlAdresat': '',
                '_sectionLayoutContainer$ctl01$_mpsCombo': '-1',
                '_sectionLayoutContainer$ctl01$ctlZadavatelKlub': '',
                '_sectionLayoutContainer$ctl01$_meetingNrIntCombo': '0',
                '_sectionLayoutContainer$ctl01$_meetingNrOdpCombo': '0',
                '_sectionLayoutContainer$ctl01$ctlCPT': '',
                '_sectionLayoutContainer$ctl01$DatumOd': self.date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$_stateCombo': '',
                '_sectionLayoutContainer$ctl01$Type': 'optSearchType',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',
            }

            if crawled_string not in self.crawled_pages:
                self.crawled_pages[crawled_string] = True
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    # 'url': response.meta['url'],
                    'body': urlencode(body),
                },
                meta={'period_num': period}
            )

        # items
        items = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01_dgResult"]/tbody/tr[contains(@class, "tab_zoznam_nonalt") or contains(@class, "tab_zoznam_alt")]'
        )
        for item in items:
            itemlink = item.xpath('td[1]/a/@href').extract_first()
            url_parsed = urlparse(itemlink)
            url_qs = parse_qs(url_parsed.query)
            interpellation_id = int(url_qs['ID'][0])
            if interpellation_id in self.crawled_interpellations:
                continue
            self.crawled_interpellations[interpellation_id] = True
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, itemlink),
                self.parse_interpellation,
                meta={'period_num': period}
            )

    def parse_interpellation(self, response):
        url_parsed = urlparse(response.url)
        url_qs = parse_qs(url_parsed.query)
        interpellation_id = int(url_qs['ID'][0])

        item = scrapy.loader.ItemLoader(item=InterpellationItem())
        item.add_value('type', 'interpellation')
        item.add_value('period_num', response.meta['period_num'])
        item.add_value(
            'status',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[1]/span/text()'
            ).extract_first())
        item.add_value('external_id', interpellation_id)
        item.add_value(
            'asked_by',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[2]/span/text()'
            ).extract_first())
        item.add_value(
            'description',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[1]/span/text()'
            ).extract_first())
        item.add_value(
            'recipients',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[3]/span/text()'
            ).extract_first())
        try:
            date_obj = datetime.strptime(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[4]/span/text()'
                ).extract_first(),
                '%d. %m. %Y'
            ).replace(hour=12)
        except ValueError:
            date_obj = datetime.strptime(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[4]/span/text()'
                ).extract_first(),
                '%d.%m.%Y'
            ).replace(hour=12)
        item.add_value(
            'date',
            date_obj
        )
        try:
            interpellation_session_num = int(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[5]/span/text()'
                ).extract_first())
        except (TypeError, ValueError):
            interpellation_session_num = None
        item.add_value('interpellation_session_num', interpellation_session_num)
        item.add_value(
            'responded_by',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[3]/div[1]/span/text()'
            ).extract_first())
        try:
            response_session_num = int(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[3]/div[2]/span/text()'
                ).extract_first())
        except (TypeError, ValueError):
            response_session_num = None
        item.add_value('response_session_num', response_session_num)
        try:
            press_num = int(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[3]/div[3]/span/text()'
                ).extract_first())
        except TypeError:
            press_num = None
        item.add_value('press_num', press_num)
        interpellation = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/a[1]')
        interpellation_response = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/a[2]')
        attachments = []
        if interpellation:
            attachments.append({
                'url': '{}{}'.format(self.BASE_URL, interpellation.xpath('@href').extract_first()),
                'name': interpellation.xpath('text()').extract_first().strip()
            })
        if interpellation_response:
            attachments.append({
                'url':
                '{}{}'.format(
                    self.BASE_URL,
                    interpellation_response.xpath('@href').extract_first()),
                'name':
                interpellation_response.xpath('text()').extract_first().strip()
            })

        item.add_value('attachments_names', attachments)
        item.add_value('attachments_urls', response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/a/@href').extract())
        item.add_value('url', response.url)

        yield item.load_item()
