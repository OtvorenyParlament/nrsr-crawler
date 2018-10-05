"""
Clubs crawler
"""

from urllib.parse import urlparse, parse_qs
import scrapy

from nrsr.items import ClubItem, ClubMemberItem

class ClubSpider(scrapy.Spider):
    name = 'clubs'
    BASE_URL = 'https://www.nrsr.sk/web/'

    def start_requests(self):
        urls = ['https://www.nrsr.sk/web/default.aspx?SectionId=69']
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        periods = response.xpath(
            '//*/select[@id="_sectionLayoutContainer_ctl02__currentTerm"]/option/@value'
        ).extract()
        i = 0
        for period in periods:
            meta = {'period_num': period}
            if i == 0:
                links = response.xpath(
                    '//*[@id="_sectionLayoutContainer__panelContent"]/ul/li/a/@href'
                ).extract()
                for link in links:
                    yield scrapy.Request(
                        '%s%s' % (self.BASE_URL, link),
                        callback=self.parse_club,
                        meta=meta)
            i += 1
            viewstate = response.css(
                'input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css(
                'input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css(
                'input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            yield scrapy.FormRequest(
                response.request.url,
                formdata={
                    '__EVENTTARGET':
                    '_sectionLayoutContainer$ctl02$_currentTerm',
                    '_sectionLayoutContainer$ctl02$_currentTerm': str(period),
                    '__VIEWSTATE': viewstate,
                    '__EVENTVALIDATION': eventvalidation,
                    '__VIEWSTATEGENERATOR': viewstategenerator,
                },
                callback=self.parse_list,
                meta=meta)

    def parse_list(self, response):
        links = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/ul/li/a/@href').extract()
        for link in links:
            yield scrapy.Request(
                '%s%s' % (self.BASE_URL, link),
                callback=self.parse_club,
                meta=response.meta
            )

    def parse_club(self, response):
        club = scrapy.loader.ItemLoader(item=ClubItem())
        url_parsed = urlparse(response.url)
        club.add_value('type', 'club')
        club.add_value('period_num', response.meta['period_num'])
        club.add_value('external_id', parse_qs(url_parsed.query)['ID'])
        club.add_value('url', response.url)
        club.add_value('name',
                       response.xpath('//*/h1/text()').extract_first().strip())
        club.add_value(
            'email',
            response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__email"]/a/text()').
            extract_first())
        members = []
        found_members = response.xpath(
            '//table[@class="tab_zoznam"]/tr[position() > 1]')

        found_members = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/div[@class="member"]'
        )
        if len(list(found_members)) > 0:
            for member in found_members:
                club_member = ClubMemberItem()
                href = member.xpath(
                    'div[@class="member_name"]/a/@href').extract_first()
                parsed_qs = parse_qs(href)
                club_member['external_id'] = parsed_qs['PoslanecID'][0]
                club_member['membership'] = member.xpath(
                    'div[@class="member_name"]/span/text()').extract_first(
                    ).strip()
                members.append(club_member)
        else:
            found_members = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01__historicalViewGrid"]/tr[contains(@class, "tab_zoznam_nonalt") or contains(@class, "tab_zoznam_alt")]'
            )
            for member in found_members:
                club_member = ClubMemberItem()
                href = member.xpath('td[1]/a/@href').extract_first()
                parsed_qs = parse_qs(href)
                club_member['external_id'] = parsed_qs['PoslanecID'][0]
                club_member['membership'] = member.xpath(
                    'td[2]/text()').extract_first().strip()

        club.add_value('members', members)
        yield club.load_item()
