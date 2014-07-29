# coding=utf-8
from scrapy.item import Item, Field


class JsonItem(Item):
    _id = Field()
    _symbol = Field()
    _type = Field()
    _hash = Field()
    _raw = Field()
    url = Field()
    updated = Field()


class HtmlItem(Item):
    _id = Field()
    _symbol = Field()
    _type = Field()
    _hash = Field()
    _raw = Field()
    url = Field()
    updated = Field()


class ArticleItem(Item):
    _id = Field()
    _symbol = Field()
    _type = Field()
    _hash = Field()
    _raw = Field()
    title = Field()
    url = Field()
    author = Field()
    create_time = Field()
    updated = Field()
    content = Field()
    source = Field()
    source_url = Field()
    tags = Field()


class MovieItem(Item):
    _id = Field()
    _symbol = Field()
    _type = Field()
    _hash = Field()
    _raw = Field()
    url = Field()
    symbol_original = Field()
    symbol = Field()
    title = Field()
    original_title = Field()
    alt = Field()
    rating = Field()
    subtype = Field()
    directors = Field()
    casts = Field()
    writers = Field()
    maker = Field()
    maker_label = Field()
    series = Field()
    tags = Field()
    website = Field()
    pubdates = Field()
    saledates = Field()
    year = Field()
    languages = Field()
    durations = Field()
    genres = Field()
    countries = Field()
    summary = Field()
    photos = Field()
    image_urls = Field()  # Scrapy default field
    images = Field()  # Scrapy default field


class CelebrityItem():
    _id = Field()
    _symbol = Field()
    _type = Field()
    _hash = Field()
    _raw = Field()
    name = Field()
    name_en = Field()
    alt = Field()
    avatars = Field()
    aka = Field()
