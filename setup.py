#!/usr/bin/env python

from setuptools import setup


setup(
    name='yt2tv',
    author='daveb@smurfless.com',
    url='https://github.com/smurfless1/youtubeToTv',
    versioning='dev',
    setup_requires=['setupmeta'],
    dependency_links=['https://pypi.org/project/setupmeta'],
    packages=["yt2tv"],
    include_package_data=True,
    python_requires='>=3.4',
    install_requires=[
        'click',
        #'https://github.com/smurfless1/applescript.git'
        'applescript',
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
    youtubetotv=yt2tv.cli:playlist
    ''',
)

