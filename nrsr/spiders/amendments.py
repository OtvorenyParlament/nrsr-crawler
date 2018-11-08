"""
Amendments Spider
"""

from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, parse_qs, urlencode
import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import AmendmentItem


class AmendmentsSpider(NRSRSpider):

    name = 'amendments'
    BASE_URL = 'https://www.nrsr.sk/web/'
    crawled_pages = {}
    crawled_amendments = {}

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=schodze/nrepdn',

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

        if self.daily:
            date_from = (datetime.utcnow() - timedelta(days=7)).strftime('%d. %m. %Y')
        else:
            date_from = ''

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
                '_sectionLayoutContainer$ctl01$ctlNazov': '',
                '_sectionLayoutContainer$ctl01$ctlCisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$ctlCPT': '',
                '_sectionLayoutContainer$ctl01$PoslanecMasterID': '-1',
                '_sectionLayoutContainer$ctl01$_meetingNrCombo': '0',
                '_sectionLayoutContainer$ctl01$DatumOd': date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$Type': 'optFullTextType',
                '_sectionLayoutContainer$ctl01$cmdSearch': 'Vyhľadať',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '11',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '11',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018'
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

        if self.daily:
            date_from = (datetime.utcnow() - timedelta(days=7)).strftime('%d. %m. %Y')
        else:
            date_from = ''

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
                '_sectionLayoutContainer$ctl01$DatumOd': date_from,
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
            itemlink = item.xpath('td[4]/a/@href').extract_first()
            press_num = item.xpath('td[3]/text()').extract_first()
            if press_num:
                press_num = int(press_num)
            url_parsed = urlparse(itemlink)
            url_qs = parse_qs(url_parsed.query)
            amendment_id = int(url_qs['id'][0])
            if amendment_id in self.crawled_amendments:
                continue
            self.crawled_amendments[amendment_id] = True
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, itemlink),
                self.parse_amendment,
                meta={'period_num': period, 'press_num': press_num}
            )

    def parse_amendment(self, response):
        url_parsed = urlparse(response.url)
        url_qs = parse_qs(url_parsed.query)
        amendment_id = int(url_qs['id'][0])

        press_num = response.meta['press_num']

        item = scrapy.loader.ItemLoader(item=AmendmentItem())
        item.add_value('type', 'amendment')
        item.add_value('external_id', amendment_id)
        item.add_value('period_num', response.meta['period_num'])
        item.add_value('press_num', press_num)
        item.add_value(
            'session_num',
            int(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[4]/span/text()'
                ).extract_first()))
        item.add_value(
            'title',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[1]/span/text()'
            ).extract_first())
        item.add_value(
            'submitter',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[3]/span/text()'
            ).extract_first())
        item.add_value(
            'other_submitters',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[8]/span/ul/li/span/text()'
            ).extract())
        date_string = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[6]/span/text()'
        ).extract_first()
        date_match = re.match(r'(\d+\. \d+\. \d+).*', date_string)
        item.add_value(
            'date',
            datetime.strptime(
                date_match.groups()[0], '%d. %m. %Y').replace(hour=12)
        )
        item.add_value(
            'signed_members',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[10]/span/ul/li/span/text()'
            ).extract())
        voting_link = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[10]/span/a/@href'
        ).extract_first()
        if voting_link:
            link_parsed = urlparse(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div[10]/span/a/@href'
                ).extract_first())
            link_qs = parse_qs(link_parsed.query)
            voting_external_id = int(link_qs['ID'][0])
        else:
            voting_external_id = None
        item.add_value('voting_external_id', voting_external_id)
        item.add_value('url', response.url)

        yield item.load_item()
