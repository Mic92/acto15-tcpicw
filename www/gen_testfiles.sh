#!/bin/sh

for i in 1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384; do
  dd if=/dev/urandom of=${i}kb bs=1024 count="${i}"
done
