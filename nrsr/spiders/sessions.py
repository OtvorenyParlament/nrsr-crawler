"""
Parliament Sessions spider
"""

from urllib.parse import urlparse, parse_qs
import scrapy

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import SessionItem


class SessionsSpider(NRSRSpider):
    name = 'sessions'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=schodze/zoznam',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [str(self.period)]
        else:
            periods = response.xpath(
                '//*/select[@id="_sectionLayoutContainer_ctl01__currentTerm"]/option/@value'
            ).extract()
        i = 0
        for period in periods:
            meta = {'period_num': period}
            if i == 0:
                links = response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/ul/li/a/@href').extract()
                for link in links:
                    yield scrapy.Request(
                        '%s%s' % (self.BASE_URL, link),
                        callback=self.parse_session,
                        meta=meta
                    )
            i += 1
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            yield scrapy.FormRequest(
                response.request.url,
                formdata={
                    '__EVENTTARGET': '_sectionLayoutContainer$ctl01$_currentTerm',
                    '_sectionLayoutContainer$ctl01$_currentTerm': str(period),
                    '__VIEWSTATE': viewstate,
                    '__EVENTVALIDATION': eventvalidation,
                    '__VIEWSTATEGENERATOR': viewstategenerator,
                },
                callback=self.parse_list,
                meta=meta
            )

    def parse_list(self, response):
        links = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/ul/li/a/@href').extract()
        for link in links:
            yield scrapy.Request(
                '%s%s' % (self.BASE_URL, link),
                callback=self.parse_session,
                meta=response.meta
            )

    def parse_session(self, response):
        item = SessionItem()
        url_parsed = urlparse(response.url)
        item['type'] = 'session'
        item['period_num'] = response.meta['period_num']
        item['external_id'] = parse_qs(url_parsed.query)['ID'][0]
        item['name'] = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__Caption"]/text()').extract_first()
        item['attachments_urls'] = response.xpath(
            '//*[@id="_sectionLayoutContainer_ctl01__programDocumentPanel"]/a/@href').extract()
        item['url'] = response.url
        attachments = []
        for x in response.xpath('//*[@id="_sectionLayoutContainer_ctl01__programDocumentPanel"]/a'):
            attachments.append({
                'url': '{}{}'.format(self.BASE_URL, x.xpath('@href').extract_first()),
                'name': x.xpath('text()').extract_first().strip(),
            })
        item['attachment_names'] = attachments

        press = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/table/tbody/tr[contains(@class, "tab_zoznam_nonalt") or contains(@class, "tab_zoznam_alt")]'
        )
        program_points = []
        for row in press:
            p_url = '%s%s' % (self.BASE_URL,
                              row.xpath('td[3]/a/@href').extract_first())
            try:
                p_state = row.xpath('td[1]/img/@alt').extract_first().strip()
            except:
                p_state = None
            try:
                p_progpoint = row.xpath('td[2]/text()').extract()[0].replace(
                    '\xfd', '').strip().replace('.', '')
            except:
                p_progpoint = None
            try:
                p_parlpress = row.xpath('td[3]/a/text()').extract()[0].replace(
                    '\xfd', '').strip()
            except:
                p_parlpress = None
            try:
                p_text1 = ' '.join(row.xpath('td[4]/strong/text()').extract()).strip()
            except:
                p_text1 = None
            try:
                p_text2 = ' '.join(row.xpath('td[4]/i/text()').extract()).strip()
            except:
                p_text2 = None
            try:
                p_text3 = ' '.join([x.strip() for x in row.xpath('td[4]/text()').extract()]).strip()
            except:
                p_text3 = None
            program_points.append({
                'state': p_state,
                'progpoint': p_progpoint,
                'parlpress': p_parlpress,
                'parlpress_url': p_url,
                'text': [p_text1, p_text2, p_text3]
            })
        item['program_points'] = program_points
        yield item
