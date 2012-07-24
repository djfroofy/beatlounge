#!/bin/bash
curl -L -O http://sourceforge.net/projects/fluidsynth/files/fluidsynth-1.1.5/fluidsynth-1.1.5.tar.bz2/download
tar jxvf download
cd fluidsynth-1.1.5
./configure
make
make install
