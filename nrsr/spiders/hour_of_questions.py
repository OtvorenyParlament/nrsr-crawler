"""
Hour of questions spider
"""

from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, parse_qs, urlencode
import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import HourOfQuestionsItem

class HourOfQuestionsSpider(NRSRSpider):

    name = 'hour_of_questions'
    BASE_URL = 'https://www.nrsr.sk/web/'

    crawled_pages = {}
    crawled_questions = {}

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=schodze/ho_result',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [self.period]
        else:
            periods = response.xpath(
                '//*/select[@id="_sectionLayoutContainer_ctl01__CisObdobia"]/option/@value'
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
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_Otazka': '',
                '_sectionLayoutContainer$ctl01$_CisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$_mpsCombo': '-1',
                '_sectionLayoutContainer$ctl01$_Adresat': '',
                '_sectionLayoutContainer$ctl01$_View': 'All',
                '_sectionLayoutContainer$ctl01$DatumOd': self.date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$Type': '_FullTextType',
                '_sectionLayoutContainer$ctl01$_SearchButton': 'Vyhľadať',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrho',
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
        pages = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__ResultGrid"]/tbody/tr[1]/td/table/tbody/tr/td/a/@href').extract()
        pages = list(set(pages))
        period = response.meta['period_num']
        current_page = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__ResultGrid"]/tbody/tr[1]/td/table/tbody/tr/td/span/text()'
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
                '__EVENTTARGET': '_sectionLayoutContainer$ctl01$_ResultGrid',
                '__EVENTARGUMENT': eventargument,
                '__LASTFOCUS': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_Otazka': '',
                '_sectionLayoutContainer$ctl01$_CisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$_mpsCombo': '-1',
                '_sectionLayoutContainer$ctl01$_Adresat': '',
                '_sectionLayoutContainer$ctl01$_View': 'All',
                '_sectionLayoutContainer$ctl01$DatumOd': self.date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$Type': '_FullTextType',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrho',
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
        items = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__ResultGrid"]/tbody/tr[contains(@class, "tab_zoznam_nonalt") or contains(@class, "tab_zoznam_alt")]')
        for item in items:
            itemlink = item.xpath('td[1]/a/@href').extract_first()
            url_parsed = urlparse(itemlink)
            url_qs = parse_qs(url_parsed.query)
            question_id = int(url_qs['MasterID'][0])
            if question_id in self.crawled_questions:
                continue
            self.crawled_questions[question_id] = True
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, itemlink),
                self.parse_question,
                meta={'period_num': period}
            )

    def parse_question(self, response):
        url_parsed = urlparse(response.url)
        url_qs = parse_qs(url_parsed.query)
        question_id = int(url_qs['MasterID'][0])
        item = scrapy.loader.ItemLoader(item=HourOfQuestionsItem())
        item.add_value('type', 'hour_of_questions')
        item.add_value('external_id', question_id)
        item.add_value(
            'status',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/text()'
            ).extract_first().strip().split(':')[1])
        item.add_value('period_num', response.meta['period_num'])
        item.add_value(
            'question_by',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[2]/span/text()'
            ).extract_first())
        try:
            question_date = datetime.strptime(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[1]/span/text()'
                ).extract_first().replace('\xa0', ''), '%d. %m. %Y').replace(hour=12)
        except Exception as exc:
            question_date = None
        item.add_value('question_date', question_date)
        try:
            answer_date = datetime.strptime(
                response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[5]/span/text()'
                ).extract_first().replace('\xa0', ''), '%d. %m. %Y').replace(hour=12)
        except:
            answer_date = None
        item.add_value('answer_date', answer_date)
        item.add_value(
            'recipient',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[4]/span/text()'
            ).extract_first())
        item.add_value(
            'question',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[3]/span/text()'
            ).extract_first())
        item.add_value(
            'answer_by',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[6]/span/text()'
            ).extract_first())
        item.add_value(
            'answer',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[7]/span/text()'
            ).extract_first())
        item.add_value(
            'additional_question',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[8]/span/text()'
            ).extract_first())
        item.add_value(
            'additional_answer',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[2]/div[9]/span/text()'
            ).extract_first())
        item.add_value('url', response.url)
        yield item.load_item()
