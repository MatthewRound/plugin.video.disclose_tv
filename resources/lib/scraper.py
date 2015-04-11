#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import re
import sys
import urllib

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen

MAIN_URL = 'http://www.disclose.tv/'


class Scraper:


    def do_search(self, searchString):
        #log('do_search started')
        q = urllib.quote(searchString)
        videos = []
        limit = "20"
        url = 'https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num='+limit+'&hl=en&prettyPrint=false&source=gcsc&gss=.tv&sig=cb6ef4de1f03dde8c26c6d526f8a1f35&cx=partner-pub-4295593939052550:t6ujbcvse69&q='+q+'&sort=&googlehost=www.google.com'
        res = self.__get_url(url)
        aa = json.loads(res)
        results = aa['results']
        for rs in results:
            rsnip = rs['richSnippet']
            if rsnip.has_key('videoobject'):
                vo = rsnip['videoobject']
                duration = vo['duration']
                thumbnail = vo['thumbnailurl']
                title = vo['name']
                path = vo['url'].split('/')[6].lower()
                id = vo['url'].split('/')[5]
                video = {
                    'thumbnail': thumbnail,
                    'id': id,
                    'path': path,
                    'title': title,
                    'duration': self.__secs_from_duration(duration, True)
                }
                videos.append(video)
        return videos


    def get_video_topics(self):
        #log('get_video_topics started')
        path = 'action/videolist/page/1/all/filter/'
        url = MAIN_URL + path
        tree = self.__get_tree(url)
        ul = tree.find('ul', {'id': 'videos-media-box-filter'})
        topics = []
        for li in ul.findAll('li'):
            topics.append({
                'title': li.a.string,
                'id': li.a['href'].split('/')[5]
            })
        return topics
        

    def get_videos(self, topic_id, page):
        #log('get_videos_by_topic_id started with topic_id=%s' % topic_id)
        url = MAIN_URL + 'action/videolist/page/%d/%s/filter/' % (
            int(page), topic_id
        )
        tree = self.__get_tree(url)
        div = tree.find('div', {'id': 'videos-media-box-list'})
        videos = []
        for li in div.findAll('li'):
            a = li.find('a')
            img = a.find('img')['data-src']
            title = a['title']
            video_id, path = a['href'].split('/')[3:5]
            span_content = li.find('span', {'class': 'types typeV'}).contents
            if len(span_content) == 1:
                duration = span_content[0].split(' ')[1]
            elif len(span_content) == 2:
                duration = span_content[1].strip()
            else:
                duration = ''
            video = {
                'id': video_id,
                'thumbnail': self.__img(img),
                'path': path,
                'title': title,
                'duration': self.__secs_from_duration(duration)
            }
            videos.append(video)
        return videos


    def get_video_url(self, video_id):
        url = MAIN_URL + 'videos/config/xxx/%s.js' % video_id
        data = self.__get_url(url)
        match = re.search(r"'(http(s)://.*\.(flv|mp4|webm))'", data)
        if match:
            return match.group(1).replace('http://', 'https://')


    @staticmethod
    def __secs_from_duration(d, fromSearch = False):
        seconds = 0
        if (fromSearch):
            bits = d.split('S')
            m = bits[1].split('M')[0]
            s = bits[1].split('M')[1]
            h = bits[0].split('T')[1]
            seconds = (int(h)*60*60) + (int(m) * 60) + int(s);
        else:
            for part in d.split(':'):
                seconds = seconds * 60 + int(part)
        return seconds


    @staticmethod
    def __img(url):
        return url.replace('135x76', '').split('?')[0]

    def __get_tree(self, url):
        html = self.__get_url(url)
        return BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)

    def __get_url(self, url):
        #log('__get_url opening url: %s' % url)
        response = urlopen(url).read()
        #log('__get_url got %d bytes' % len(response))
        return response


def log(text):
    print u'Scraper: %s' % text
