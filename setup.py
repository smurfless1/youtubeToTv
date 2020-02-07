#!/usr/bin/env python

from setuptools import setup


setup(
    name='youtubetotv',
    author='daveb@smurfless.com',
    url='https://github.com/smurfless1/youtubeToTv',
    versioning='dev',
    setup_requires=['setupmeta'],
    dependency_links=[
        'https://pypi.org/project/setupmeta',
    ],
    packages=["youtubetotv"],
    include_package_data=True,
    python_requires='>=3.4',
    install_requires=[
        'click',
        'click-log',
        'lameapplescript@https://github.com/smurfless1/applescript/archive/master.zip',
        'subler',
        'xdg',
        'youtube_dl',
    ],
    extras_require={
        'dev': [
            'behave',
            'flake8',
            'invoke',
            'tox',
            'pytest'
        ]
    },
    entry_points='''
    [console_scripts]
    yttt=youtubetotv.cli:playlist
    ''',
)

