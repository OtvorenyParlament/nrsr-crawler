from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, parse_qs, urlencode

import scrapy
from scrapy_splash import SplashRequest


from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import DebateAppearanceItem


class DebateAppearancesSpider(NRSRSpider):

    name = 'debate_appearances'
    BASE_URL = 'https://www.nrsr.sk/web/'
    crawled_pages = {}

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=schodze/rozprava/vyhladavanie',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [self.period]
        else:
            periods = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__termNrCombo"]/option/@value').extract()
            periods = list(map(int, periods))

        if self.daily:
            date_from = (datetime.utcnow() - timedelta(days=7)).strftime('%d. %m. %Y')
        else:
            date_from = ''

        for period in periods:
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
            meta = {'period_num': period}
            body = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_termNrCombo': str(period),
                '_sectionLayoutContainer$ctl01$_mpsCombo': '0',
                '_sectionLayoutContainer$ctl01$_cptTextBox': '',
                '_sectionLayoutContainer$ctl01$_meetingNrCombo': '0',
                '_sectionLayoutContainer$ctl01$_dateFromTextBox': date_from,
                '_sectionLayoutContainer$ctl01$_dateToTextBox': '',
                '_sectionLayoutContainer$ctl01$_speechTypeCombo': '',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',
            }

            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_mp_list,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body),
                },
                meta=meta
            )

    def parse_mp_list(self, response):
        mps = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__mpsCombo"]/option/@value').extract()
        mps = list(map(int, mps))
        period = response.meta['period_num']
        if self.daily:
            date_from = (datetime.utcnow() - timedelta(days=7)).strftime('%d. %m. %Y')
        else:
            date_from = ''
        for mp in mps:
            # skip nofilter
            if mp == 0:
                continue
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
            meta = {'period_num': period, 'member_id': mp}
            body = {
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_termNrCombo': str(period),
                '_sectionLayoutContainer$ctl01$_mpsCombo': str(mp),
                '_sectionLayoutContainer$ctl01$_cptTextBox': '',
                '_sectionLayoutContainer$ctl01$_meetingNrCombo': '0',
                '_sectionLayoutContainer$ctl01$_dateFromTextBox': date_from,
                '_sectionLayoutContainer$ctl01$_dateToTextBox': '',
                '_sectionLayoutContainer$ctl01$_speechTypeCombo': '',
                '_sectionLayoutContainer$ctl01$_searchButton': 'Vyhľadať',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',
            }

            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_appearances,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body),
                },
                meta=meta
            )

    def parse_appearances(self, response):
        period = response.meta['period_num']
        member_id = response.meta['member_id']
        pages = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__resultGrid"]/tbody/tr[1]/td/table/tbody/tr/td/a/@href'
        ).extract()
        pages = list(set(pages))
        current_page = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__resultGrid"]/tbody/tr[1]/td/table/tbody/tr/td/span/text()'
        ).extract_first()
        
        if not current_page:
            current_page = '1'

        initial_string = 'page_{}_{}_{}'.format(period, member_id, current_page)
        if not initial_string in self.crawled_pages:
            self.crawled_pages[initial_string] = True

        cleaned_pages = []
        for page in pages:
            page_match = re.match(r'.*(Page.*[0-9]).*', page)
            if not page_match:
                continue
            page_num = page_match.groups()[0].split('$')[-1]
            crawled_string = 'page_{}_{}_{}'.format(period, member_id, page_num)

            if crawled_string in self.crawled_pages:
                continue
            cleaned_pages.append(page_match.groups()[0])

        if self.daily:
            date_from = (datetime.utcnow() - timedelta(days=7)).strftime('%d. %m. %Y')
        else:
            date_from = ''

        for page in cleaned_pages:
            eventargument = page
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
            meta = {'period_num': period, 'member_id': member_id}
            body = {
                '__EVENTTARGET': '_sectionLayoutContainer$ctl01$_resultGrid',
                '__EVENTARGUMENT': eventargument,
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_termNrCombo': str(period),
                '_sectionLayoutContainer$ctl01$_mpsCombo': str(member_id),
                '_sectionLayoutContainer$ctl01$_cptTextBox': '',
                '_sectionLayoutContainer$ctl01$_meetingNrCombo': '0',
                '_sectionLayoutContainer$ctl01$_dateFromTextBox': date_from,
                '_sectionLayoutContainer$ctl01$_dateToTextBox': '',
                '_sectionLayoutContainer$ctl01$_speechTypeCombo': '',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrdvp',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',
            }

            if not crawled_string in self.crawled_pages:
                self.crawled_pages[crawled_string] = True
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_appearances,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body),
                },
                meta=meta
            )

        # parse items
        items = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__resultGrid"]/tbody/tr[contains(@class, "tab_zoznam_nalt")]')
        for item in items:
            when_string = item.xpath('td[1]/div/div[1]/span[1]/text()').extract_first().strip()
            when_match = re.match(r'^([0-9]{1,2}\. [0-9]{1,2}\. [0-9]{4}) (.*) \- (.*)$', when_string)
            when_start = datetime.strptime(
                '{} {}'.format(when_match.groups()[0], when_match.groups()[1]), '%d. %m. %Y %H:%M:%S')
            when_end = datetime.strptime(
                '{} {}'.format(when_match.groups()[0], when_match.groups()[2]), '%d. %m. %Y %H:%M:%S')
            where_string = item.xpath('td[1]/div/div[1]/span[2]/text()').extract_first().strip()
            ppress_num = item.xpath('td[1]/div/div[1]/span[3]/a/text()').extract()
            video_links = item.xpath('td[1]/div/div[1]/span[4]/a/@href').extract()
            video_parsed = urlparse(video_links[0])
            video_qs = parse_qs(video_parsed.query)
            appearance_id = int(video_qs['id'][0])

            try:
                session_num = int(where_string.split('.')[0])
            except:
                session_num = None
            try:
                appearance_type_string = item.xpath(
                    'td[1]/div/div[3]/span[4]/em/text()').extract_first().strip()
            except:
                appearance_type_string = None
            try:
                appearance_type_addition_string = item.xpath(
                    'td[1]/div/div[3]/span[4]/text()').extract_first().strip()
            except:
                appearance_type_addition_string = None
            appearance_text = item.xpath('td/div/div[5]/span/text()').extract()

            final_item = scrapy.loader.ItemLoader(item=DebateAppearanceItem())
            final_item.add_value('type', 'debate_appearance')
            final_item.add_value('external_id', appearance_id)
            final_item.add_value('period_num', period)
            final_item.add_value('member_id', member_id)
            final_item.add_value('start', when_start)
            final_item.add_value('end', when_end)
            final_item.add_value('session_num', session_num)
            final_item.add_value('press_num', list(map(int, ppress_num)))
            final_item.add_value('appearance_type', appearance_type_string)
            final_item.add_value('appearance_type_addition', appearance_type_addition_string)
            final_item.add_value('text', appearance_text)
            final_item.add_value('video_short_url', video_links[0])
            final_item.add_value('video_long_url', video_links[1])
            yield final_item.load_item()
