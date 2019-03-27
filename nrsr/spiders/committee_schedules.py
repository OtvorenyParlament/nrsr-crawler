"""
NR SR committee schedule crawler
"""

from urllib.parse import urlparse, parse_qs, urlencode
import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import CommitteeScheduleItem


class CommitteeSchedulesSpider(NRSRSpider):
    name = 'committee_schedules'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=vybory/schodze',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [self.period]
        else:
            periods = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01_ctlCisObdobia"]/option/@value'
            ).extract()
            periods = list(map(int, periods))

        for period in periods:
            meta = {'period_num': period}
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()

            body = {
                '__EVENTTARGET': '',
                '__VIEWSTATE': viewstate,
                '__EVENTVALIDATION': eventvalidation,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_View': 'NRVyb.Timetable',
                '_sectionLayoutContainer$ctl01$ctlCisObdobia': str(period),
                '_sectionLayoutContainer$ctl01$DatumOd': self.date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$_SearchButton': 'Vyhľadať',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2019',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrvyb',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2019',
            }

            yield scrapy.FormRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                callback=self.parse_committee_schedules,
                formdata=body,
                meta={'period_num': period}
            )
            # yield SplashRequest(
            #     '{}{}'.format(self.BASE_URL, post_action),
            #     self.parse_committee_schedules,
            #     args={
            #         'http_method': 'POST',
            #         'body': urlencode(body),
            #         'wait': 10,
            #     },
            #     meta={'period_num': period}
            # )

    def parse_committee_schedules(self, response):
        page_content = response.xpath('//div[@id="_sectionLayoutContainer_ctl01__MainPanel"]')
        committees = page_content.xpath('//div[@class="vyborylist_item"]')
        for committee in committees:
            committee_name = committee.xpath('h3/span/text()').extract_first()
            sessions = committee.xpath('div/div[@class="vyborylist_left"]')

            for session in sessions:
                committee_item = CommitteeScheduleItem()
                committee_item['type'] = 'committeeschedule'
                committee_item['committee_name'] = committee_name
                committee_item['period_num'] = response.meta['period_num']

                session_date = session.xpath('span[contains(@class, "grid_2")]/text()').extract_first()
                session_time = session.xpath('strong[contains(@class, "grid_2")]/text()').extract_first()
                session_place = session.xpath('div[contains(@class, "grid_8")]/text()').extract()

                committee_item['date'] = session_date
                committee_item['time'] = session_time
                committee_item['place'] = session_place

                items = session.xpath('following::ul[1]/li')
                points = []
                for item in items:
                    try:
                        press_num = int(item.xpath('a/text()').extract_first())
                    except:
                        press_num = None
                    text = item.xpath('text()').extract()
                    points.append({
                        'press_num': int(press_num) if press_num else None,
                        'text': text
                    })
                committee_item['points'] = points
                yield committee_item

