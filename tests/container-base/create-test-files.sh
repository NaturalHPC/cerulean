#!/bin/bash

mkdir /home/cerulean/test_files
mkdir /home/cerulean/test_files/links

# files
echo 'Hello World' >/home/cerulean/test_files/links/file0
touch /home/cerulean/test_files/links/file1

# symlink
ln -s /home/cerulean/test_files/links/file0 /home/cerulean/test_files/links/link0

# link to link
ln -s /home/cerulean/test_files/links/link0 /home/cerulean/test_files/links/link1

# broken link
ln -s /doesnotexist /home/cerulean/test_files/links/link2

# link loop
ln -s /home/cerulean/test_files/links/link3 /home/cerulean/test_files/links/link4
ln -s /home/cerulean/test_files/links/link4 /home/cerulean/test_files/links/link3

# fifo
mkfifo /home/cerulean/test_files/fifo

# character device
mknod /home/cerulean/test_files/chardev c 0 0

# block device
mknod /home/cerulean/test_files/blockdev b 0 0
