# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as f:
    long_desc = "".join(f.readlines())

setup(
    name = "jiracli",
    version = "0.1",
    packages = find_packages(),
    scripts = ['jiracli'],
    package_data = {
        '': ['README.md', 'LICENSE'],
    },
    install_requires = [
        'jira-python>=0.13',
        'termcolor',
        'setuptools',
    ],
    author = "Thomas Bechtold",
    author_email = "thomasbechtold@jpberlin.de",
    description = "command line interface for jira",
    long_description=long_desc,
    license = "GPL-3",
    keywords = "jira cli atlassian REST",
    url = "https://github.com/toabctl/jiracli",

    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Utilities",
    ],
)
