#!/bin/sh
sudo cmake [Dhelib_DIR=~/helib_install/helib_pack/share/cmake/helib] .
sudo make
./main -d "/home/rami742/Documents/he-testing/powerData/2023/power/power-fifteen-20230101.csv" -p "/home/rami742/Documents/he-testing/powerData/points.csv" -i "491"