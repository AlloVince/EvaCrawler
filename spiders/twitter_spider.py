# coding=utf-8
from scrapy.spider import BaseSpider
from scrapy.shell import inspect_response
from scrapy.http import Request
import urlparse
from evacrawler.items import *
from evacrawler import p
from scrapy.exceptions import CloseSpider
from scrapy.conf import settings
import json
import hashlib
import oauth2 as oauth
import urllib
import timelib
import time


class TweetJsonSpider(BaseSpider):
    name = "tweet"
    allowed_domains = ["twitter.com"]
    start_urls = []

    basic_url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
    screen_names = []

    def get_oauth_request(self, url, method='GET', parameters={}):
        config = settings['TWITTER']

        consumer = oauth.Consumer(
            config['consumer_key'], config['consumer_secret'])
        token = oauth.Token(config['token_key'], config['token_secret'])

        url = urlparse.urlparse(url)._asdict()
        parameters = dict(urlparse.parse_qsl(url['query']))
        url['query'] = ''
        url = urlparse.urlunparse(url.values())

        oauth_request = oauth.Request.from_consumer_and_token(
            consumer=consumer, token=token, http_method=method, http_url=url, parameters=parameters)
        oauth_request.sign_request(
            oauth.SignatureMethod_HMAC_SHA1(), consumer, token)

        schema, rest = urllib.splittype(url)
        if rest.startswith('//'):
            hierpart = '//'
        else:
            hierpart = ''
        host, rest = urllib.splithost(rest)
        realm = schema + ':' + hierpart + host

        return {
            'url': url,
            'parameters': parameters,
            'headers':  oauth_request.to_header(realm=realm),
        }

    def start_requests(self):
        if not self.screen_names:
            raise CloseSpider('No screen name found')

        start_urls = []
        for screen_name in self.screen_names:
            start_urls.append(self.basic_url + '?screen_name=' + screen_name)

        requests = []
        for url in start_urls:
            oauth_request = self.get_oauth_request(url)
            requests.append(Request(url=url, headers=oauth_request['headers']))
        return requests

    def parse(self, response):
        res = json.loads(response.body)

        if not res:
            raise CloseSpider('Scrawl finished')

        url = urlparse.urlparse(response.url)._asdict()
        parameters = dict(urlparse.parse_qsl(url['query']))
        parameters['count'] = len(res)
        parameters['max_id'] = res[-1]['id']
        url['query'] = urllib.urlencode(parameters)
        url = urlparse.urlunparse(url.values())
        oauth_request = self.get_oauth_request(url)
        yield Request(url=url, headers=oauth_request['headers'])

        for tweet in res:
            yield self.parse_tweet(tweet)

    def parse_tweet(self, tweet):
        item = JsonItem()
        item['_id'] = hashlib.md5(tweet['id_str']).hexdigest()
        item['url'] = 'https://twitter.com/' + tweet['user']['screen_name'] + '/' + '/status/' + tweet['id_str']
        item['create_time'] = int(time.mktime(timelib.strtodatetime(tweet['created_at']).timetuple()))
        item['raw'] = tweet
        return item
