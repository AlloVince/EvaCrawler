# coding=utf-8
from scrapy.spider import BaseSpider
#from scrapy.shell import inspect_response
from scrapy.http import Request
import urlparse
from evacrawler.items import JsonItem
#from evacrawler import p
from scrapy.exceptions import CloseSpider
from scrapy.conf import settings
import json
import hashlib
import urllib
import time


class JsonSpider(BaseSpider):
    name = "json"
    allowed_domains = []
    start_urls = []

    # Custom setting:
    depth_limit = 0
    download_delay = 0
    # 列表是否就已经包含了Item
    item_inner = False

    # 翻页规则
    pagination_arg = 'page'
    pagination_num = 1
    pagination_step = 1

    def __init__(self, depth=0, delay=0, *a, **kw):
        if self.depth_limit > 0:
            settings.overrides['DEPTH_LIMIT'] = self.depth_limit

        if depth > 0:
            settings.overrides['DEPTH_LIMIT'] = depth

        if self.download_delay > 0:
            settings.overrides['DOWNLOAD_DELAY'] = self.download_delay

        if delay > 0:
            settings.overrides['DOWNLOAD_DELAY'] = delay

        super(JsonSpider, self).__init__(*a, **kw)

    def next_page(self, url):
        self.pagination_num += self.pagination_step
        url = urlparse.urlparse(url)._asdict()
        parameters = dict(urlparse.parse_qsl(url['query']))
        parameters[self.pagination_arg] = self.pagination_num
        url['query'] = urllib.urlencode(parameters)
        url = urlparse.urlunparse(url.values())
        return url

    def parse(self, response):
        url = self.next_page(response.url)
        res = json.loads(response.body)
        if not res:
            raise CloseSpider('Not more list found')

        items = self.parse_list(res, response)
        if items:
            for item in items:
                yield Request(url=item, callback=self.parse_item)

        yield Request(url=url)

    def parse_list(self, items, response):
        return None

    def parse_item(self, response):
        return [self.parse_item_base(response)]

    def parse_item_base(self, response):
        item = JsonItem()
        item['_id'] = hashlib.md5(response.url).hexdigest()
        item['_symbol'] = self.name
        item['_type'] = 'json'
        item['_raw'] = response.body
        item['_hash'] = hashlib.md5(response.body).hexdigest()
        item['url'] = response.url
        item['updated'] = int(time.time())
        return item
