import click
import os
import pickle
from xdg import XDG_CONFIG_HOME

configfile_dir = XDG_CONFIG_HOME / "ntscli.develop"
configfile_path = configfile_dir / "config.ini"
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PlaylistList:
    cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlists.pkl")
    lists = {}
    archive = os.path.expanduser('~/.config/youtube-dl/downloaded_by_python')

    @staticmethod
    def load():
        if os.path.exists(PlaylistList.cache):
            PlaylistList.lists = pickle.load(open(PlaylistList.cache, "rb"))

    @staticmethod
    def save():
        pickle.dump(PlaylistList.lists, open(PlaylistList.cache, "wb"))


class Playlist:
    cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "currentplaylist.pkl")

    def __init__(self, name, url):
        self.name = name
        self.url = url

    def save(self):
        pickle.dump(self, open(Playlist.cache, "wb"))

    @staticmethod
    def load():
        try:
            if os.path.exists(Playlist.cache):
                return pickle.load(open(Playlist.cache, "rb"))
            raise Exception("Ouch")
        except:
            print("Unable to load a currently selected playlist.")


