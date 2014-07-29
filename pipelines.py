# coding=utf-8
import json
from urlparse import urlparse
#from scrapy.exceptions import *
from scrapy.conf import settings
from scrapy import log
from twisted.enterprise import adbapi
#import datetime
import codecs
import MySQLdb
import MySQLdb.cursors
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from scrapy.http import Request


class MysqlPipeline(object):

    def __init__(self):
        conn = MySQLdb.connect(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor
        )
        self.cursor = conn.cursor()
        self.conn = conn

    def process_item(self, item, spider):
        entity_id = item['_id']
        self.cursor.execute("""SELECT id, hash FROM entities WHERE id = %s""", (entity_id,))
        result = self.cursor.fetchone()

        if result:
            if result['hash'] != item['_hash']:
                sql = """
                UPDATE entities SET symbol = %s, type = %s, hash = %s, body = %s WHERE id = %s
                """
                param = (item['_symbol'], item['_type'], item['_hash'], json.dumps(dict(item), ensure_ascii=False), entity_id)
                self.cursor.execute(sql, param)
                self.conn.commit()
        else:
            sql = """
            INSERT INTO entities (id, symbol, type, hash, body)
            VALUES (%s, %s, %s, %s, %s)
            """
            param = (entity_id, item['_symbol'], item['_type'], item['_hash'], json.dumps(dict(item), ensure_ascii=False))
            self.cursor.execute(sql, param)
            self.conn.commit()

        return item

    def __exit__(self, type, value, traceback):
        self.cursor.close()
        self.conn.close()


# from https://github.com/darkrho/dirbot-mysql/blob/master/dirbot/pipelines.py
class MysqlTwistedPipeline(object):

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
        return cls(dbpool)

    def process_item(self, item, spider):
        # run db query in the thread pool
        d = self.dbpool.runInteraction(self._do_upsert, item, spider)
        d.addErrback(self._handle_error, item, spider)
        # at the end return the item in case of success or failure
        d.addBoth(lambda _: item)
        # return the deferred instead the item. This makes the engine to
        # process next item (according to CONCURRENT_ITEMS setting) after this
        # operation (deferred) has finished.
        return d

    def _do_upsert(self, conn, item, spider):
        conn.execute("""
                     INSERT INTO entities (id, symbol, type, hash, body)
                     VALUES (%s, %s, %s, %s, %s)
                     on duplicate key update
                     symbol = values(symbol),
                     type = values(type),
                     hash = values(hash),
                     body = values(body)
                     """, (item['_id'], item['_symbol'], item['_type'], item['_hash'], json.dumps(dict(item), ensure_ascii=False)))
        #spider.log("Item stored in db: %s %r" % (item['_id'], item))

    def _handle_error(self, failure, item, spider):
        log.err(failure)

    def _get_guid(self, item):
        return item['_id']


class MongoPipeline(object):

    def __init__(self):
        import pymongo
        connection = pymongo.Connection(
            settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
        self.db = connection[settings['MONGODB_DB']]
        self.collection = self.db[settings['MONGODB_COLLECTION']]
        if self.__get_uniq_key() is not None:
            self.collection.create_index(self.__get_uniq_key(), unique=True)

    def process_item(self, item, spider):
        if self.__get_uniq_key() is None:
            self.collection.insert(dict(item))
        else:
            self.collection.update(
                {self.__get_uniq_key():
                 item[self.__get_uniq_key()]},
                dict(item),
                upsert=True)
        log.msg("Item wrote to MongoDB database %s/%s" %
                (settings['MONGODB_DB'], settings['MONGODB_COLLECTION']),
                level=log.DEBUG, spider=spider)
        return item

    def __get_uniq_key(self):
        if not settings['MONGODB_UNIQ_KEY'] or settings['MONGODB_UNIQ_KEY'] == "":
            return None
        return settings['MONGODB_UNIQ_KEY']


class FilePipeline(object):

    def process_item(self, item, spider):
        url = urlparse(item['url'].rstrip('/'))
        filename = 'index.json' if url.path == '/' else url.path.split("/")[-1] + \
            '.json'
        filepath = settings['DOWNLOAD_FILE_FOLDER'] + '/' + filename

        codecs.open(filepath, 'wb',
                    encoding='utf-8').write(json.dumps(dict(item), ensure_ascii=False))
        return item


class ImagesPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        if 'image_urls' in item:
            for image_url in item['image_urls']:
                yield Request(image_url)

            if item.has_key('photos') and item['photos']:
                for image_url in item['photos']:
                    yield Request(image_url)


    def image_key(self, url):
        # keep original path
        url = urlparse(url)
        return 'full/%s' % (url.path)

    def item_completed(self, results, item, info):
        return item
