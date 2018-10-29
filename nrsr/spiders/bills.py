"""
Bills spider
"""

from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, parse_qs, urlencode

import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import BillItem, BillStepItem, BillStepChangeItem


class BillsSpider(NRSRSpider):
    name = 'bills'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=zakony/sslp',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [str(self.period)]
        else:
            periods = response.xpath('//*/select[@id="_sectionLayoutContainer_ctl01_ctlCisObdobia"]/option/@value').extract()

        if self.daily:
            date_from = (datetime.utcnow() - timedelta(days=7)).strftime('%d. %m. %Y')
        else:
            date_from = ''

        for period in periods:
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first() or '0'
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first() or '0'
            body = {
                '__EVENTTARGET': '_sectionLayoutContainer$ctl01$ctlCisObdobia',
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
                '_sectionLayoutContainer$ctl01$ctlCategory': '-1',
                '_sectionLayoutContainer$ctl01$ctlPredkladatel': '-1',
                '_sectionLayoutContainer$ctl01$ctlPredkladatelName': '',
                '_sectionLayoutContainer$ctl01$_mpsCombo': '-1',
                '_sectionLayoutContainer$ctl01$ctlView': '',
                '_sectionLayoutContainer$ctl01$_Ciastka': '',
                '_sectionLayoutContainer$ctl01$_Cislo': '',
                '_sectionLayoutContainer$ctl01$DatumOd': date_from,
                '_sectionLayoutContainer$ctl01$DatumDo': '',
                '_sectionLayoutContainer$ctl01$Type': 'optSearchType',
                '_sectionLayoutContainer$ctl01$cmdSearch': 'Vyhľadať',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrcpt',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',
            }

            yield SplashRequest(
                response.url,
                self.parse_list,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body)
                },
                meta={'period_num': period}
            )

    def parse_list(self, response):
        period = response.meta['period_num']

        # items
        items = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_dgResult"]/tbody/tr[contains(@class, "odd") or contains(@class, "even")]/td[1]/a/@href').extract()
        for item in items:
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, item),
                self.parse_item,
                meta={'period_num': period}
            )

    def parse_item(self, response):
        url_parsed = urlparse(response.url)
        url_qs = parse_qs(url_parsed.query)
        bill_id = url_qs['MasterID'][0]
        item = scrapy.loader.ItemLoader(item=BillItem())
        item.add_value('type', 'bill')
        item.add_value('external_id', bill_id)
        item.add_value('period_num', response.meta['period_num'])
        item.add_value('url', response.url)
        item.add_value('proposer', response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__NavrhovatelLabel"]/text()').extract_first())
        item.add_value('delivered', response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__DatumDoruceniaLabel"]/text()').extract_first())
        item.add_value('press_num', response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__CptLink"]/text()').extract_first())
        item.add_value('current_state', response.xpath('//*[@id="_sectionLayoutContainer_ctl01__ProcessStateLabel"]/text()').extract_first())
        item.add_value('current_result', response.xpath('//*[@id="_sectionLayoutContainer_ctl01__CurrentResultLabel"]/text()').extract_first())


        graph_detail = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__LegProcesDiagramLink"]/@href').extract_first()
        if graph_detail:
            yield scrapy.Request(url='{}{}'.format(self.BASE_URL, graph_detail), callback=self.parse_graph)
        yield item.load_item()

    def parse_graph(self, response):
        steps = response.xpath('//*[@id="_sectionLayoutContainer__panelContent"]/table/tr/td[1]/div/a/@href').extract()
        for step in steps:
            yield scrapy.Request(url='{}{}'.format(self.BASE_URL, step), callback=self.parse_step)


    def parse_step(self, response):
        url_parsed = urlparse(response.url)
        url_qs = parse_qs(url_parsed.query)
        bill_id = url_qs['MasterID'][0]
        external_id = url_qs['WorkitemID'][0]
        main_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__MainLabel"]/text()').extract_first()
        body_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__BodyPanel"]/h2/text()').extract_first()

        meeting_panel = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__meetingPanel"]/text()').extract()
        if meeting_panel:
            meeting_session_num = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__CisSchodzeLabel"]/text()').extract_first()
            meeting_resolution = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__UznesenieLabel"]/text()').extract_first()
        else:
            meeting_session_num = None
            meeting_resolution = None

        committees_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__VyboryLabel"]/text()').extract()
        slk_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__SlkLabel"]/text()').extract()
        coordinator_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__GestorskyVyborLabel"]/text()').extract_first()
        step_result = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__ResultLabel"]/text()').extract_first()
        

        coordinator_meeting_date = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__DatumPrerokovaniaLabel"]/text()').extract_first()
        if coordinator_meeting_date:
            coordinator_name = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__GVNameLabel"]/text()').extract_first()
        else:
            coordinator_name = None
    
        discussed_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__PrerokovanyLabel"]/text()').extract_first()
        sent_standpoint = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__ZaslaneStanoviskoLabel"]/text()').extract_first()

        sent_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__OdoslanyLabel"]/text()').extract_first()
        act_num_label = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__CiastkaLabel"]/text()').extract_first()

        changes = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__PdnList__PdnLabel"]').extract_first()
        change_rows = []
        if changes:
            rows = response.xpath('//*[@id="_sectionLayoutContainer_ctl01_ctl00__PdnList__pdnListPanel"]/table/tr')
            for row in rows:
                change = BillStepChangeItem()
                change['date'] = row.xpath('td[1]/text()').extract_first()
                change['author'] = row.xpath('td[2]/text()').extract_first()
                change['detail'] = row.xpath('td[3]/a/@href').extract_first()
                change['attachment_title'] = row.xpath('td[4]/a/text()').extract_first()
                change['attachment_url'] = row.xpath('td[5]/a/@href').extract_first()
                change_rows.append(change)
        item = scrapy.loader.ItemLoader(item=BillStepItem())
        item.add_value('type', 'bill_step')
        item.add_value('bill_id', bill_id)
        item.add_value('external_id', external_id)
        item.add_value('url', response.url)
        item.add_value('main_label', main_label)
        item.add_value('body_label', body_label)
        item.add_value('meeting_panel', meeting_panel)
        item.add_value('meeting_session_num', meeting_session_num)
        item.add_value('meeting_resolution', meeting_resolution)
        item.add_value('committees_label', committees_label)
        item.add_value('slk_label', slk_label)
        item.add_value('coordinator_label', coordinator_label)
        item.add_value('coordinator_meeting_date', coordinator_meeting_date)
        item.add_value('coordinator_name', coordinator_name)
        item.add_value('step_result', step_result)
        item.add_value('discussed_label', discussed_label)
        item.add_value('sent_standpoint', sent_standpoint)
        item.add_value('sent_label', sent_label)
        item.add_value('act_num_label', act_num_label)

        item.add_value('changes', change_rows)
        yield item.load_item()
