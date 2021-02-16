#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple Bot to reply to Blogue do Caloni searches based on echobot.py sample.

author Wanderley Caloni <wanderley.caloni@gmail.com>
date 2020-06
"""
import sys
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from telegram import InlineQueryResultArticle
import xml.etree.ElementTree as ET
from time import sleep
import urllib.request
import re
import argparse
import feedparser
import os

update_id = None
thumb_url_sample = "http://caloni.com.br/images/caloni.png"
rss_cache = None

response_sample = [

    InlineQueryResultArticle('1'
        , u'Wanderley Caloni'
        , telegram.InputTextMessageContent('https://caloni.com.br/caloni/')
        , url='https://caloni.com.br/caloni/'
        , thumb_url=thumb_url_sample)

    , InlineQueryResultArticle('2'
        , 'Search'
        , telegram.InputTextMessageContent('https://caloni.com.br/search/')
        , url='https://caloni.com.br/search/'
        , thumb_url=thumb_url_sample)
]


def request_posts(path, cache=None):
    if path.find('http') == 0:
        data = feedparser.parse(path, etag=cache['headers']['etag']) if cache else feedparser.parse(path)
        if len(data['entries']) > 0:
            cache = data
    else:
        if cache:
          cache['entries'] = ET.parse(path)
        else:
          cache = { 'entries': ET.parse(path) }
    return cache


def find_posts(regex, entries=None):
    lastLink = None
    links = []

    counter = 1
    if entries:
        for entry in entries:
            title = entry['title']
            desc = entry['description']
            link = entry['link']
            mt = re.search(regex, title, flags=re.I) 
            md = desc if desc == None else re.search(regex, desc, flags=re.I) 
            if mt or md:
                content = telegram.InputTextMessageContent(link)
                links.append(InlineQueryResultArticle(str(counter), title, content, url=link, description=desc, thumb_url=thumb_url_sample))
                counter += 1
                if counter > 50: break
    else:
        links = response_sample

    return links[0:50]


def echo(params, bot):
    """Echo the message the user sent."""
    global update_id
    global rss_cache
    # Request updates after the last update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1

        if update.inline_query:
            regex = update.inline_query['query']
            rss_cache = request_posts(os.environ["RSS"], rss_cache)
            response = find_posts(regex, rss_cache['entries'])
            update.inline_query.answer(response)


def main():

    global rss_cache
    argparser = argparse.ArgumentParser('Caloni BOT')
    argparser.add_argument('--find-post', help="Find single post test.")
    params = argparser.parse_args()

    if params.find_post:
        rss_cache = request_posts(os.environ["RSS"])
        resp = find_posts(params.find_post, rss_cache['entries'])
        for r in resp:
            print(r)
        return

    logger = logging.getLogger()
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    """Run the bot."""
    global update_id
    global response
    # Telegram Bot Authorization Token
    bot = telegram.Bot(token=os.environ["TOKEN"])

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            echo(params, bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            # The user has removed or blocked the bot.
            update_id += 1


if __name__ == '__main__':
    main()

