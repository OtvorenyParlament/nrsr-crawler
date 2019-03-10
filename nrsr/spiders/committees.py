"""
NR SR committee crawler
"""

from urllib.parse import urlparse, parse_qs
import scrapy

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import CommitteeItem


class CommitteeSpider(NRSRSpider):
    name = 'committees'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/default.aspx?sid=vybory/zoznam',

        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if self.period:
            periods = [self.period]
        else:
            periods = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl02__currentTerm"]/option/@value'
            ).extract()
            periods = list(map(int, periods))
        i = 0
        for period in periods:
            meta = {'period_num': period}
            if i == 0:
                links = response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/ul/li/a/@href').extract()
                for link in links:
                    yield scrapy.Request(
                        '%s%s' % (self.BASE_URL, link),
                        callback=self.parse_committee,
                        meta=meta
                    )

    def parse_committee(self, response):
        item = CommitteeItem()
        url_parsed = urlparse(response.url)
        item['type'] = 'committee'
        item['period_num'] = response.meta['period_num']
        item['external_id'] = int(parse_qs(url_parsed.query)['ID'][0])
        item['name'] = response.xpath('//h1/text()').extract_first().strip()
        item['description'] = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__basicInfoText"]/p/text()').extract()
        item['url'] = response.url

        members = response.xpath('//*[@class="member_name"]')
        committee_members = []
        for member in members:
            member_url = member.xpath('a/@href').extract_first()
            member_parsed = urlparse(member_url)
            member_role = member.xpath('span/text()').extract_first().strip()
            committee_members.append({
                'role': member_role,
                'external_id': int(parse_qs(member_parsed.query)['PoslanecID'][0])
            })
        item['members'] = committee_members
        yield item
