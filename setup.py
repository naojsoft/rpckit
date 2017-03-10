#! /usr/bin/env python
#
try:
    from setuptools import setup

except ImportError:
    from distutils.core import setup
from rpckit.version import version
import os

srcdir = os.path.dirname(__file__)

from distutils.command.build_py import build_py

def read(fname):
    buf = open(os.path.join(srcdir, fname), 'rt').read()
    return buf

setup(
    name = "rpckit",
    version = version,
    author = "Software Division, Subaru Telescope, National Astronomical Observatory of Japan",
    author_email = "ocs@naoj.org",
    description = ("Python package for making SunRPC compatible calls."),
    long_description = read('README.txt'),
    license = "GPL",
    keywords = "NAOJ, subaru, telescope, instrument, data",
    url = "http://naojsoft.github.com/rpckit",
    packages = ['rpckit'],
    package_data = { },
    scripts = ['scripts/rpcgen.py'],
    classifiers = [
    ],
    cmdclass={'build_py': build_py}
)
