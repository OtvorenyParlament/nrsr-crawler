"""
Common __init__ for spiders
"""

from datetime import datetime, timedelta

from scrapy import Spider
from scrapy.utils.project import get_project_settings


class NRSRSpider(Spider):

    def __init__(self, daily='false', period='', **kwargs):
        settings = get_project_settings()
        self.daily = True if daily == 'true' else False
        self.period = None if period == '' else int(period)
        self.daily_history_days = settings.get('DAILY_HISTORY_DAYS')
        self.mongo_uri = settings.get('MONGO_URI')
        self.mongo_database = settings.get('MONGO_DATABASE')
        self.mongo_col = settings.get('MONGO_COL')

        if self.daily:
            self.date_from = (datetime.utcnow() - timedelta(
                days=self.daily_history_days)).strftime('%d. %m. %Y')
        else:
            self.date_from = ''
        super().__init__(**kwargs)
