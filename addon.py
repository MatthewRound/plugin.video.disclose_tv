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

from xbmcswift2 import Plugin
from resources.lib.scraper import Scraper
from SimpleDownloader import DialogDownloadProgress
import xbmc
import urllib2


STRINGS = {
    'page': 30001,
    'download video': 30002
}

plugin = Plugin()
scraper = Scraper()


@plugin.route('/')
def show_topics():
    topics = scraper.get_video_topics()
    items = [{
        'label': topic['title'],
        'path': plugin.url_for(
            endpoint='show_videos',
            topic_id=topic['id'],
            page='1'
        )
    } for topic in topics]
    items.insert(0, {
        'label': 'Search',
        'path' : plugin.url_for(
            endpoint='search_videos_prompt'
        )
    })
    return plugin.finish(items)



@plugin.route('/searchprompt')
def search_videos_prompt():
    searchString = ''
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        searchString = keyboard.getText()
        #log('searchString %s' % searchString)
        videos = scraper.do_search(searchString)
        items = __format_videos(videos)
        return plugin.finish(items)





@plugin.route('/videos/<topic_id>/<page>/')
def show_videos(topic_id, page):
    page = int(page)
    videos = scraper.get_videos(topic_id, page)
    items = __format_videos(videos)
    if True:  # FIXME: find a way to detect...
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='show_videos',
                topic_id=topic_id,
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='show_videos',
                topic_id=topic_id,
                page=previous_page,
                update='true')
        })
    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode') == 'true':
        finish_kwargs['view_mode'] = plugin.get_setting('viewmode_id')
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<video_id>')
def play_video(video_id):
    video_url = scraper.get_video_url(video_id)
    return plugin.set_resolved_url(video_url)


def __format_videos(videos):
    items = [{
        'label': video['title'],
        'icon': video['thumbnail'],
        'thumbnail': video['thumbnail'],
        'info': {
            'count': i,
        },
        'stream_info': {
            'video': {'duration': video['duration']}
        },
        'is_playable': True,
        'replace_context_menu': True,
        'context_menu': [(
            _('download video'), 
            'XBMC.RunPlugin(%s)' % plugin.url_for('download_video', video_id=video['id'], video_title=video['title']),
        )],
        'path': plugin.url_for(
            endpoint='play_video',
            video_id=video['id']
        ),
    } for i, video in enumerate(videos)]
    return items


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


@plugin.route('/download_video/<video_id>/<video_title>')
def download_video(video_id, video_title):
    clean_title = "".join(i for i in video_title if i not in "\/[](){}':!*?<>|")
    video_url = scraper.get_video_url(video_id)
    path = plugin.get_setting('download_path')
    if path == 'NOTSET':
        path = xbmc.translatePath("special://temp")
    filename = video_url.split('/')[-1]
    saveLocation = path + filename
    dialog = DialogDownloadProgress.DownloadProgress()
    u = urllib2.urlopen(video_url)
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    dialog.create('Downloading', "%s Bytes: %s" % (filename, file_size))
    f = open(saveLocation, 'wb')
    block_sz = 8192
    file_size_dl = 0
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            dialog.close()
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        dialog.update(0, clean_title, status)
    f.close()


def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    plugin.run()
