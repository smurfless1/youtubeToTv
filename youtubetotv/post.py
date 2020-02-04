import json
from subler import Atom, Subler
import argparse
import os
import applescript
import pickle
from playlists import Playlist, PlaylistList

# cd one level up
mydir = os.path.dirname(os.path.abspath(__file__))
os.chdir(mydir)

# todo arg parse/count
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--itunes', help='iTunes base dir', default='/Volumes/itunes')
parser.add_argument('-d', '--dir', help='dir to scan', default=mydir)
parser.add_argument('-o', '--outdir', help='output dir', default='~/Downloads')
args = parser.parse_args()
print(args)

json_episode_tag = u'playlist_index'
json_tv_show_tag = u'TV Show'
json_tv_show_name = u'playlist'
json_tv_show_episode = u'playlist_index'
json_episode_name = u'title'

outbase = os.path.expanduser(args.outdir)

for subdir, dirs, files in os.walk(args.dir):
    for thisfile in files:
        (unused, ext) = os.path.splitext(thisfile)
        if ext == '.mp4':
            bpath = os.path.abspath(args.dir)
            abs = os.path.join(bpath, thisfile)
            outfile = os.path.join(outbase, os.path.basename(abs))
            if os.path.exists(outfile):
                continue

            (fname, unused) = os.path.splitext(os.path.basename(abs))
            infojsonfile = os.path.join(bpath, fname + '.info.json')
            if os.path.exists(infojsonfile):
                #print('exists')
                with open(infojsonfile) as jsonfile:
                    #print('opening')
                    d = json.load(jsonfile, encoding='utf-8')

                    kind2 = Atom(u'Media Kind', json_tv_show_tag)
                    episode = Atom(u'TV Episode #', d[json_tv_show_episode])
                    show = Atom(u'TV Show', d[json_tv_show_name].encode('ascii','ignore').decode('ascii'))
                    name = Atom(u'Name', d[json_episode_name].encode('ascii','ignore').decode('ascii'))

                    tagger = Subler(unicode(abs), media_kind=json_tv_show_tag)
                    metadata = tagger.existing_metadata

                    metadata.append(show)
                    metadata.append(name)
                    metadata.append(kind2)
                    metadata.append(episode)

                    print(outfile)
                    try:
                        tagger = Subler(abs, dest=outfile, media_kind=json_tv_show_tag, metadata=metadata)
                        tagger.tag()

                        # add to itunes directly
                        script = """
try
tell application "iTunes"
	set file_ to (POSIX file "%s" as alias)
	set newFile to add file_ to playlist "Library" of source "Library"
end tell
end try
                        """ % outfile
                        #print(script)
                        applescript.run(script)

                        # todo check presence of rmtrash?
                        os.system('rmtrash %s' % infojsonfile)
                        os.system('rmtrash %s' % abs)
                        os.system('rmtrash %s' % outfile)
                    except:
                        pass