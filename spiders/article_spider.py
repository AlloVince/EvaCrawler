# coding=utf-8
from scrapy.contrib.spiders import CrawlSpider
#from scrapy.http import Request
#import urlparse
from evacrawler.items import ArticleItem
#from scrapy.shell import inspect_response
#from evacrawler import p
#from scrapy.exceptions import CloseSpider
from scrapy.conf import settings
from pyquery import PyQuery
from readability.readability import Document
import hashlib
from tidylib import tidy_document
from tidylib import tidy_fragment
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
from HTMLParser import HTMLParser
import jieba
import jieba.analyse
import re
from lxml.html.clean import Cleaner


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class ArticleHtmlSpider(CrawlSpider):
    #Scrapy default:
    name = "article"
    allowed_domains = []
    start_urls = []
    rules = []

    #Custom setting:
    depth_limit = 0
    remove_link_flag = False
    download_delay = 0
    watch_mode = False
    watch_depth = 1
    selectors = {}
    encoding = False

    def __init__(self, depth=0, delay=0, *a, **kw):
        if self.depth_limit > 0:
            settings.overrides['DEPTH_LIMIT'] = self.depth_limit

        if depth > 0:
            settings.overrides['DEPTH_LIMIT'] = depth

        if self.download_delay > 0:
            settings.overrides['DOWNLOAD_DELAY'] = self.download_delay

        if delay > 0:
            settings.overrides['DOWNLOAD_DELAY'] = delay

        super(ArticleHtmlSpider, self).__init__(*a, **kw)

    def strip_tags(self, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    def get_text(self, html):
        text = self.strip_tags(html)
        pattern = re.compile(r'\s{2}')
        text = re.sub(pattern, ' ', text)
        pattern = re.compile(r'\n{2}')
        text = re.sub(pattern, '\n', text)
        return text.strip()

    def get_text_length(self, html):
        text = self.get_text(html)
        return len(text)

    def get_unicode_html(self, response):
        if self.encoding:
            body = response.body.decode(self.encoding)
        else:
            body = response.body
            if not isinstance(body, unicode):
                body = response.body.decode('utf-8')
        return body

    def convert_links(self, dom, response):
        base_url = get_base_url(response)
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        def replace_link(index, node):
            node = PyQuery(node)
            if not node.attr('href'):
                return node

            link = node.attr('href').strip()
            if regex.match(link):
                try:
                    node.attr('href', urljoin_rfc(base_url, link))
                except:
                    pass
            return node
        dom('a').each(replace_link)

    def remove_links(self, dom):
        if not self.remove_link_flag:
            return dom

        def remove_link(index, node):
            node = PyQuery(node)
            node.replaceWith(node.text())
            return node
        dom('a').each(remove_link)
        return dom

    def convert_imgs(self, dom, response):
        base_url = get_base_url(response)

        def replace_img(index, node):
            node = PyQuery(node)
            if not node.attr('src'):
                return node
            try:
                node.attr('src', urljoin_rfc(base_url, node.attr('src')))
            except:
                pass
            return node

        dom('img').each(replace_img)
        return dom

    def clean_html_document(self, body):
        content, errors = tidy_document(body,
                                        options={"output-xhtml": 1,
                                                 "doctype": 'strict'})
        return content

    def clean_html_fragment(self, body):
        content, errors = tidy_fragment(body,
                                        options={"output-xhtml": 1,
                                                 "doctype": 'strict'})
        return content

    def laundry_document(self, html, response):
        html = self.clean_html_document(html)

        #replace a tag to text
        #remove class / id
        cleaner = Cleaner(style=False, links=False, add_nofollow=False,
                          page_structure=True, safe_attrs_only=True)
        html = cleaner.clean_html(html)

        dom = PyQuery(html)
        dom = self.convert_imgs(dom, response)
        dom = self.remove_links(dom)
        html = dom.html()

        #need to remove empty tags
        return html

    def get_html_dom(self, response):
        html = self.get_unicode_html(response)
        #html = self.clean_html(html)
        dom = PyQuery(html)
        #dom = self.convert_links(dom, response)
        return dom

    def analyse_tags(self, html, num=3):
        tags = self.strip_tags(html)
        tags = jieba.analyse.extract_tags(tags, num)
        return tags

    def parse_basic(self, response):
        item = ArticleItem()
        item['_id'] = hashlib.md5(response.url).hexdigest()
        item['_symbol'] = self.name
        item['_type'] = 'article'
        item['_hash'] = hashlib.md5(response.body).hexdigest()
        item['url'] = response.url
        item['title'] = Document(response.body).short_title()
        item['content'] = Document(response.body).summary()
        #item['_raw'] = response.body
        if not self.selectors:
            return item

        dom = PyQuery(response.body)
        for key, select in self.selectors:
            item[key] = dom(select).text()

        return item

"""
from evacrawler.spiders.article_spider import ArticleHtmlSpider
hs = ArticleHtmlSpider()
hs.encoding = 'gbk'
dom = hs.get_html_dom(response)
content = dom('.pages_box_content .text').html()
content = hs.laundry_document(content, response)
hs.get_text(content)
hs.get_text_length(content)

pattern = re.compile(ur'【在线答疑】')
content = re.sub(pattern, '', content)
"""
