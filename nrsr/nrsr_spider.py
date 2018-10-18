"""
Common __init__ for spiders
"""

from scrapy import Spider


class NRSRSpider(Spider):

    def __init__(self, daily='false', period='', **kwargs):
        self.daily = True if daily == 'true' else False
        self.period = None if period == '' else int(period)
        super().__init__(**kwargs)
