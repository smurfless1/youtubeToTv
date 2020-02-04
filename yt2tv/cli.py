import click
from youtubeToTv.yt2tv.playlists import PlaylistList
from youtubeToTv.yt2tv.playlists import Playlist
from .youtubetag import run


@click.group()
def playlist():
    """Youtube playlist urls and names."""


@playlist.command()
def lsplaylist():
    try:
        PlaylistList.load()
        for cc in PlaylistList.lists.keys():
            print(cc)
    except:
        print("Whoooooa. That didn't work.")


@playlist.command()
@click.argument("name")
@click.argument("url")
def mkplaylist(name, url):
    cc = Playlist(name, url)
    cc.save()  # cache it

    # save it to the global list too
    PlaylistList.load()
    PlaylistList.lists[name] = cc
    PlaylistList.save()


@playlist.command()
@click.argument("name")
def rmplaylist(name):
    PlaylistList.load()
    cc = PlaylistList.lists[name]
    if cc is not None:
        print(f"Removing cached playlist {name}")
        del PlaylistList.lists[name]
        PlaylistList.save()
    else:
        print("Could not find that cluster")


@click.command()
@click.option("--itunes", "-i", help='iTunes base dir', default='/itunes/youtube')
@click.option("--dir", "-d", help='dir to scan', default=os.path.dirname(os.path.abspath(__file__)))
@click.option('--outdir', '-o', help='output dir', default='~/Downloads')
def download(itunes, dir, outdir):
    run(itunes, dir, outdir)