#!/bin/bash

name=$1; src=$2

~/mosdepth -t 24 "$name" "$src"
mkdir -p "$name";
cd "$name" || exit;
gzip -cd "../""$name"".per-base.bed.gz" | ../bed2cov/convert_Linux
cd ../

