import concurrent
import json
import os
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from pathlib import Path
from time import sleep
from typing import Any, List

# Implementation libs
import click_log
import lameapplescript
import youtube_dl
from youtubetotv.mylogger import MyLogger

from .playlists import PlaylistList

if platform.system() == "Darwin":
    from subler import Atom, Subler

logger = getLogger(__name__)
click_log.basic_config(logger)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

PlaylistList.load()

JSON_EPISODE_TAG = "playlist_index"
JSON_TV_SHOW_TAG = "TV Show"
JSON_TV_SHOW_NAME = "playlist"
JSON_TV_SHOW_EPISODE = "playlist_index"
JSON_EPISODE_NAME = "title"


# todo loop across multiple playlists
# todo track current position in a playlist
# todo start various downloads


def defer_rmtrash(i):
    sleep(3)
    os.system("rmtrash %s" % i)  # nosec B605


def tag_and_enqueue_add(
    infojsonfile: Path,
    source_file: Path,
    output_directory: Path,
    created_futures: List[Any],
    add_pool: ThreadPoolExecutor,
    rmtrash_pool: ThreadPoolExecutor,
) -> None:
    """Given the movie and info file, tag and queue the add."""
    time.sleep(3)  # fs sync?
    with infojsonfile.open() as jsonfile:
        logger.debug("opening json file")
        ytdl_update_dict = json.load(jsonfile, encoding="utf-8")

    kind2 = Atom("Media Kind", JSON_TV_SHOW_TAG)
    episode = Atom("TV Episode #", ytdl_update_dict[JSON_TV_SHOW_EPISODE])
    show = Atom("TV Show", ytdl_update_dict[JSON_TV_SHOW_NAME].encode("ascii", "ignore").decode("ascii"))
    name = Atom("Name", ytdl_update_dict[JSON_EPISODE_NAME].encode("ascii", "ignore").decode("ascii"))

    tagged_file = output_directory.joinpath(source_file.name)

    tagger = Subler(str(source_file), dest=str(tagged_file), media_kind=JSON_TV_SHOW_TAG)
    try:
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
        logger.debug(f"tagging {source_file}")
        tagger = Subler(str(source_file), dest=str(tagged_file), media_kind=JSON_TV_SHOW_TAG, metadata=metadata)
        tagger.tag()
    except BaseException as be:
        logger.error(be)
        logger.error("Tags didnt get set, adding anyway")

    logger.debug(f"creating script for {source_file}")
    # add to itunes directly
    script = """
try
tell application "TV"
set file_ to (POSIX file "%s" as alias)
set newFile to add file_ to playlist "Library" of source "Library"
tell newFile to set media kind to TV show
end tell
end try
""" % str(
        tagged_file
    )
    logger.debug(script)

    def applescript_then_trash(inscript, infojsonfile, outfile, tagged):
        try:
            logger.debug(f"submitting applescript for {outfile}")
            lameapplescript.run(inscript)
        except ChildProcessError:
            logger.error(f"failed applescript for {outfile}")
        logger.debug(f"submitting trash jobs for {outfile}")
        created_futures.append(rmtrash_pool.submit(defer_rmtrash, infojsonfile))
        created_futures.append(rmtrash_pool.submit(defer_rmtrash, outfile))
        created_futures.append(rmtrash_pool.submit(defer_rmtrash, tagged))

        logger.debug(f"submitting applescript job for {outfile}")

    created_futures.append(add_pool.submit(applescript_then_trash, script, infojsonfile, source_file, tagged_file))


def run(resultdir: str, workdir: str, force: bool):
    # workdir is ~/Downloads - working directory for the download
    # resultdir is ~/Movies is where they should go when tagged
    os.chdir(Path(workdir).absolute())  # youtube-dl seems to only work here for now

    created_futures = []
    workdir_expanded = Path(workdir).expanduser()

    dl_pool = ThreadPoolExecutor(max_workers=3)
    tagpool = ThreadPoolExecutor(max_workers=3)
    add_pool = ThreadPoolExecutor(max_workers=3)
    rmtrash_pool = ThreadPoolExecutor(max_workers=9)

    def handle_raw_ytdl_updates(ytdl_update_dict):
        """
        Callback for youtube-dl. Enqueue work in tagpool.

        This is at this scope to capture tagpool and created_futures
        """
        if platform.system() != "Darwin":
            return
        if ytdl_update_dict["status"] == "finished":
            created_futures.append(tagpool.submit(handle_ytdl_updates, ytdl_update_dict))

    def handle_ytdl_updates(ytdl_update_dict):
        """
        Given an update dict from youtube-dl
        When I can find both files
        When I read the json file
        Then I tag the movie with tags from the json
        And I enqueue the add to TV.app step

        :param ytdl_update_dict:
        :return:
        """
        if platform.system() != "Darwin":
            return

        if ytdl_update_dict["status"] == "finished":
            logger.info("Done downloading, now adding to iTunes ...")

            """
            Example:

            {
            u'status': u'finished',
            u'downloaded_bytes': 226255302,
            u'_elapsed_str': u'01:07',
            u'filename': u'Subnautica--02--Subnautica_Part_2_OCEAN_=_DEATH.mp4',
            u'elapsed': 67.5114598274231,
            u'total_bytes': 226255302,
            u'_total_bytes_str': u'215.77MiB'
            }"""
            logger.debug(ytdl_update_dict)

            updated_file_path = Path(ytdl_update_dict["filename"])
            ext = updated_file_path.suffix
            if ext != ".mp4":
                return

            # build the desired output file Path in resultdir
            outfile = workdir_expanded.joinpath(updated_file_path)
            infojsonfile = Path(outfile).with_suffix(".info.json")

            tag_and_enqueue_add(infojsonfile, outfile, Path(resultdir).expanduser(), created_futures, add_pool, rmtrash_pool)

    ydl_default_opts = {
        "call_home": False,
        "format": "best[ext=mp4]/best",
        "ignoreerrors": True,
        "logger": MyLogger(),
        "merge_output_format": "mp4",
        "outtmpl": "%(playlist)s--%(playlist_index)s--%(title)s.%(ext)s",
        "postprocessors": [{"key": "FFmpegMetadata"}],
        "progress_hooks": [handle_raw_ytdl_updates],
        "restrictfilenames": True,
        "writeinfojson": True,
        # 'playliststart': 5,
        # 'playlistend': 6,
        # 'playlist_items': [], #  Specific indices of playlist to download.
    }

    if not force:
        ydl_default_opts["download_archive"] = PlaylistList.archive

    ydl_opts = ydl_default_opts
    # todo ask itunes: see what episodes of each show we don't have yet
    # episode_list = range(1, 10)
    # ydl_opts['playlist_items'] = episode_list
    # todo a. find show name

    try:
        urls = [list.url for list in PlaylistList.lists.values()]

        def do_download(url_):
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download(url_)

        for url in urls:
            logger.info(f"submitting download job for {url}")
            created_futures.append(dl_pool.submit(do_download, [url]))

    finally:
        pass

    while True:  # I hate this
        try:
            logger.debug(f"watching for threads to exit")
            finished, unfinished = concurrent.futures.wait(created_futures, timeout=60 * 1000, return_when=concurrent.futures.ALL_COMPLETED)
            if len(list(unfinished)) == 0:
                logger.debug(f"all threads out!")
                break
        except ValueError:
            logger.debug(f"More threads going (value error)")
            continue

    for pool in [dl_pool, tagpool, add_pool, rmtrash_pool]:
        logger.debug(f"Telling pool it's shutdown time.")
        pool.shutdown(wait=True)
    logger.info("Done!")


def postprocess(dir):
    for subdir, dirs, files in os.walk(dir):
        for thisfile in files:
            (unused, ext) = os.path.splitext(thisfile)
            if ext == ".mp4":
                return
