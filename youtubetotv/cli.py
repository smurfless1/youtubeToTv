import os
from pathlib import Path

import click

from youtubetotv.playlists import Playlist
from youtubetotv.playlists import PlaylistList
from youtubetotv.run import logger, run
import click_log


@click.group()
def playlist():
    """Youtube playlist urls and names."""


@playlist.command()
def lsplaylist():
    try:
        PlaylistList.load()
        for cc in PlaylistList.lists.keys():
            print(cc)
            print(PlaylistList.lists[cc])
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
        print("Could not find that playlist")


@playlist.command()
@click.option("--dir", "-d", help='dir to scan', default=Path("~/Movies").expanduser())
@click.option('--outdir', '-o', help='output dir', default=Path("~/Downloads").expanduser())
@click.option('--force', '-f', help='force download', is_flag=True)
@click_log.simple_verbosity_option(logger)
def download(dir, outdir, force):
    run(dir, outdir, force)


if __name__ == "__main__":
    download()