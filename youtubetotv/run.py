import json
import os

from youtubeToTv.youtubetotv.mylogger import MyLogger

if os.path.exists('/Volumes'):
    from subler import Atom, Subler
import applescript
from .playlists import PlaylistList
from threading import Thread
from time import sleep
import youtube_dl

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PlaylistList.load()

json_episode_tag = u'playlist_index'
json_tv_show_tag = u'TV Show'
json_tv_show_name = u'playlist'
json_tv_show_episode = u'playlist_index'
json_episode_name = u'title'

# todo loop across multiple playlists
# todo track current position in a playlist
# todo start various downloads


def defer_rmtrash(i):
    sleep(3)
    os.system('rmtrash %s' % i)



def run(itunes, dir, outdir):
    # todo itunes no longer used
    # this includes captures of above args
    def handle_ytdl_updates(d):
        if not os.path.exists('/Volumes'):
            return
        outbase = os.path.expanduser(outdir)

        if d['status'] == 'finished':
            print('Done downloading, now adding to iTunes ...')
            # print(d) # {u'status': u'finished', u'downloaded_bytes': 226255302, u'_elapsed_str': u'01:07', u'filename': u'Subnautica--02--Subnautica_Part_2_OCEAN_=_DEATH.mp4', u'elapsed': 67.5114598274231, u'total_bytes': 226255302, u'_total_bytes_str': u'215.77MiB'}
            thisfile = d['filename']
            (unused, ext) = os.path.splitext(thisfile)
            if ext == '.mp4':
                bpath = os.path.abspath(dir)
                abs = os.path.join(bpath, thisfile)
                outfile = os.path.join(outbase, os.path.basename(abs))
                if os.path.exists(outfile):
                    return

                (fname, unused) = os.path.splitext(os.path.basename(abs))
                infojsonfile = os.path.join(bpath, fname + '.info.json')
                if os.path.exists(infojsonfile):
                    # print('exists')
                    with open(infojsonfile) as jsonfile:
                        # print('opening')
                        d = json.load(jsonfile, encoding='utf-8')

                        kind2 = Atom(u'Media Kind', json_tv_show_tag)
                        episode = Atom(u'TV Episode #', d[json_tv_show_episode])
                        show = Atom(u'TV Show', d[json_tv_show_name].encode('ascii', 'ignore').decode('ascii'))
                        name = Atom(u'Name', d[json_episode_name].encode('ascii', 'ignore').decode('ascii'))

                        tagger = Subler(abs, media_kind=json_tv_show_tag)
                        metadata = tagger.existing_metadata
                        metadata.append(show)
                        metadata.append(name)
                        metadata.append(kind2)
                        metadata.append(episode)
                        # description = Atom(u'Description', tagger.existing_metadata['description'].decode('utf-8').encode('ascii', 'ignore'))
                        # metadata.append('description)
                        # todo tag with playlist url somehow
                        # todo un-unicode comments type tags

                        # todo set dest for completed files to correct itunes dir to avoid moves later
                        print(outfile)
                        try:
                            try:
                                tagger = Subler(abs, dest=outfile, media_kind=json_tv_show_tag, metadata=metadata)
                                tagger.tag()
                            except:
                                print('Tags didnt get set, adding anyway')
                                pass

                            # add to itunes directly
                            script = """
try
tell application "iTunes"
    set file_ to (POSIX file "%s" as alias)
    set newFile to add file_ to playlist "Library" of source "Library"
end tell
end try
                            """ % outfile
                            applescript.run(script)

                            # todo check presence of rmtrash?
                            # todo defer - list?
                            t = Thread(target=defer_rmtrash, args=(infojsonfile,))
                            t.start()
                            t = Thread(target=defer_rmtrash, args=(abs,))
                            t.start()
                            os.system('rmtrash %s' % outfile)
                        except:
                            pass

    ydl_default_opts = {
        'call_home': False,
        'download_archive': PlaylistList.archive,
        'format': 'best[ext=mp4]/best',
        'ignoreerrors': True,
        'logger': MyLogger(),
        'merge_output_format': 'mp4',
        'outtmpl': "%(playlist)s--%(playlist_index)s--%(title)s.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegMetadata',
        }],
        'progress_hooks': [handle_ytdl_updates],
        'restrictfilenames': True,
        'writeinfojson': True,
        # 'playliststart': 5,
        # 'playlistend': 6,
        # 'playlist_items': [], #  Specific indices of playlist to download.
    }

    ydl_opts = ydl_default_opts
    # todo ask itunes: see what episodes of each show we don't have yet
    #episode_list = range(1, 10)
    #ydl_opts['playlist_items'] = episode_list
    # todo a. find show name

    try:
        urls = [list.url for list in PlaylistList.lists.values()]
        print(urls)
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
    finally:
        # todo join rmtrash threads?
        pass

