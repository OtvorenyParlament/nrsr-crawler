"""
Votings and votes spider
"""

from datetime import datetime, timedelta
import re
from urllib.parse import urlencode, urlparse, parse_qs
import scrapy
from scrapy_splash import SplashRequest

from nrsr.nrsr_spider import NRSRSpider
from nrsr.items import VotingItem, VotingVoteItem, DailyClubItem


class VotingSpider(NRSRSpider):
    name = 'votings'
    BASE_URL = 'https://www.nrsr.sk/web/'
    crawled_pages = {}

    def start_requests(self):
        urls = [
            'https://www.nrsr.sk/web/Default.aspx?sid=schodze/hlasovanie/vyhladavanie_vysledok',

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
            date_from = (datetime.utcnow() - timedelta(days=1)).strftime('%d. %m. %Y')
        else:
            date_from = ''
        for period in periods:
            meta = {'period_num': period}
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
                '_sectionLayoutContainer$ctl01$_textTextBox:': '',
                '_sectionLayoutContainer$ctl01$_termNrCombo': str(period),
                '_sectionLayoutContainer$ctl01$_cptTextBox': '',
                '_sectionLayoutContainer$ctl01$_meetingNrCombo': '0',
                '_sectionLayoutContainer$ctl01$_dateFromTextBox': date_from,
                '_sectionLayoutContainer$ctl01$_dateToTextBox': '',
                '_sectionLayoutContainer$ctl01$Type': '_searchTypeFullTextOption',
                '_sectionLayoutContainer$ctl01$_searchButton': 'Vyhľadať',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '10',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrhpo',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '10',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',
            }

            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body),
                },
                meta=meta
            )

    def parse_pages(self, response):
        if self.daily:
            date_from = (datetime.utcnow() - timedelta(days=1)).strftime('%d. %m. %Y')
        else:
            date_from = ''
        pages = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__resultGrid2"]/tbody/tr[1]/td/table/tbody/tr/td/a/@href').extract()
        pages = list(set(pages))
        current_page = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__resultGrid2"]/tbody/tr[1]/td/table/tbody/tr/td/span/text()').extract()
        period = response.meta['period_num']
        if current_page and current_page[0].isdigit():
            self.crawled_pages['{}_{}'.format(period, current_page[0])] = True
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
            date_from = (datetime.utcnow() - timedelta(days=1)).strftime('%d. %m. %Y')
        else:
            date_from = ''

        for page in cleaned_pages:
            eventargument = page
            page_num = eventargument.split('$')[-1]
            viewstate = response.css('input#__VIEWSTATE::attr(value)').extract_first()
            eventvalidation = response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
            viewstategenerator = response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first()
            scroll_x = response.css('input#__SCROLLPOSITIONX::attr(value)').extract_first()
            scroll_y = response.css('input#__SCROLLPOSITIONY::attr(value)').extract_first()
            post_action = response.xpath('//*[@id="_f"]/@action').extract_first()
            eventtarget = '_sectionLayoutContainer$ctl01$_resultGrid2'
            body = {
                '__EVENTTARGET': eventtarget,
                '__EVENTARGUMENT': eventargument,
                '__LASTFOCUS': '',
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__SCROLLPOSITIONX': scroll_x,
                '__SCROLLPOSITIONY': scroll_y,
                '__EVENTVALIDATION': eventvalidation,
                '_searchText': '',
                '_sectionLayoutContainer$ctl01$_textTextBox': '',
                '_sectionLayoutContainer$ctl01$_termNrCombo': period,
                '_sectionLayoutContainer$ctl01$_meetingNrCombo': '0',
                '_sectionLayoutContainer$ctl01$_cptTextBox': '',
                '_sectionLayoutContainer$ctl01$_dateFromTextBox': date_from,
                '_sectionLayoutContainer$ctl01$_dateToTextBox': '',
                '_sectionLayoutContainer$ctl01$Type': '_searchTypeFullTextOption',
                '_sectionLayoutContainer$ctl00$_calendarYear': '2018',
                '_sectionLayoutContainer$ctl00$_calendarMonth': '3',
                '_sectionLayoutContainer$ctl00$_calendarApp': 'nrhpo',
                '_sectionLayoutContainer$ctl00$_calendarLang': '',
                '_sectionLayoutContainer$ctl00$_monthSelector': '3',
                '_sectionLayoutContainer$ctl00$_yearSelector': '2018',

            }
            yield SplashRequest(
                '{}{}'.format(self.BASE_URL, post_action),
                self.parse_pages,
                args={
                    'http_method': 'POST',
                    'body': urlencode(body),
                },
                meta={'page': True, 'period_num': period}
            )
        items = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__resultGrid2"]/tbody/tr[position()>1 and position()<last()]')
        for item in items:
            press_num = item.xpath('td[4]/a/text()').extract_first()
            if press_num:
                press_num = re.search(r'(\d+)', press_num).groups()[0]
            press_url = item.xpath('td[4]/a/@href').extract_first()
            item_url = item.xpath('td[6]/a/@href').extract_first()
            if item_url:
                url = '{}{}'.format(self.BASE_URL, item_url)
                yield scrapy.Request(
                    url,
                    callback=self.parse_voting,
                    meta={
                        'period_num': period,
                        'press_num': press_num,
                        'press_url': press_url,
                    }
                )

    def parse_voting(self, response):
        voting = scrapy.loader.ItemLoader(item=VotingItem())
        voting.add_value('type', 'voting')
        period_num = response.meta['period_num']
        url_parsed = urlparse(response.url)
        voting.add_value('external_id', int(parse_qs(url_parsed.query)['ID'][0]))
        voting.add_value(
            'topic',
            response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div/div[4]/span/text()'
            ).extract_first())
        dstring = response.xpath(
            '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div/div[2]/span/text()'
        ).extract_first().strip()
        voting.add_value('datetime',
                         datetime.strptime(dstring, '%d. %m. %Y %H:%M'))
        session_num = response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01_ctl00__schodzaLink"]/text()'
            ).extract_first().strip()
        if session_num:
            session_num = re.search(r'(\d+)', session_num).groups()[0]
        voting.add_value(
            'session_num',
            session_num
            )
        voting_num = response.xpath(
                '//*[@id="_sectionLayoutContainer__panelContent"]/div[1]/div/div[3]/span/text()'
            ).extract_first().strip()
        voting.add_value(
            'voting_num',
            voting_num,
            )
        voting.add_value(
            'result',
            response.xpath(
                '//*[@id="_sectionLayoutContainer_ctl01_ctl00__votingResultCell"]/span/text()'
            ).extract_first())
        voting.add_value('period_num', period_num)
        voting.add_value('press_num', response.meta['press_num'])
        voting.add_value('press_url', response.meta['press_url'])
        voting.add_value('url', response.url)
        voting_votes = []
        votes = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__resultsTable"]/tr/td[not(@class)]')

        for vote in votes:
            voted = VotingVoteItem()
            vote_value = vote.xpath('text()').extract_first()
            if not vote_value:
                continue
            voted['vote'] = re.match(r'(\[)(.*)([\]]).*', str(vote_value)).groups()[1]
            voted_url = vote.xpath('a/@href').extract_first()
            if voted_url is None:
                continue
            url_parsed = urlparse(voted_url)
            voted['external_id'] = int(parse_qs(url_parsed.query)['PoslanecID'][0])
            voting_votes.append(voted)
        voting.add_value('votes', voting_votes)
        yield voting.load_item()

        # daily club
        daily_club = scrapy.loader.ItemLoader(item=DailyClubItem())
        daily_club.add_value('type', 'daily_club')
        daily_club.add_value('period_num', period_num)
        daily_club.add_value('date', datetime.strptime(
            dstring, '%d. %m. %Y %H:%M').replace(hour=12, minute=0, second=0, microsecond=0))
        daily_clubs = {}
        daily_club_votes = response.xpath('//*[@id="_sectionLayoutContainer_ctl01__resultsTable"]/tr/td')
        current_club = None
        for vote in daily_club_votes:
            if 'class' in vote.root.attrib and vote.root.attrib['class'] == 'hpo_result_block_title':
                current_club = vote.xpath('text()').extract_first()
                if current_club not in daily_clubs:
                    daily_clubs[current_club] = []
                continue
            voter_url = vote.xpath('a/@href').extract_first()
            if voter_url is None:
                continue
            if not current_club:
                continue
            url_parsed = urlparse(voter_url)
            member_external_id = int(parse_qs(url_parsed.query)['PoslanecID'][0])
            daily_clubs[current_club].append(member_external_id)
        transformed_clubs = [[k, v] for (k, v) in daily_clubs.items()]
        daily_club.add_value('clubs', transformed_clubs)
        yield daily_club.load_item()
