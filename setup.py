#!/usr/bin/env python

from setuptools import setup, find_packages
from txbeatlounge import version as VERSION

PKGNAME = 'txbeatlounge'

def load_requirements(requirements):
    fd = open(requirements)
    entries = []
    for line in fd:
        entry = line.strip()
        if not entry:
            continue
        if entry[0] in ('-', '#'):
            continue
        dep, v = entry.split('==')
        entries.append(entry)
    fd.close()
    return entries

requirements = load_requirements('requirements.txt')
packages = [PKGNAME] + [ ( '%s.%s' % (PKGNAME, pkg) ) for pkg in find_packages(PKGNAME) ]

setup(
    name='Twisted Beat Lounge',
    author = "Beatscape Drone Unicorns",
    version=VERSION,
    description='Twisted Beat Lounge is a framework for laying beats with fluidsynth',
    packages=packages,
    install_requires = requirements,
    include_package_data=True,
    zip_safe=False,
    entry_points = { 'console_scripts' :
        ['playsf2 = txbeatlounge.sf2tester:main',
        'beatlounge = txbeatlounge.console:main'] },
)

