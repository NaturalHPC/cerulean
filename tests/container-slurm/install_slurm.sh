#!/bin/bash
#
# This script installs the necessary tools and libraries to compile slurm, then
# downloads a slurm version, compiles and installs it, and removes any unnecessary
# code and tools afterwards.

cd /usr/local

apt-get update
apt-get --no-install-recommends install -y gcc make libssl-dev libmunge-dev tar wget patch

NAME=`basename -s .tar.gz $1`

wget -nv https://github.com/SchedMD/slurm/archive/$1
tar -xzf $1

cd /usr/local/slurm-$NAME
patch -p0 </usr/local/etc/slurm_timeout.diff

./configure --prefix=/usr/local --sysconfdir=/usr/local/etc/slurm >/tmp/configure.log 2>&1
tail -n 20 /tmp/configure.log
make >/tmp/make.log 2>&1
tail -n 20 /tmp/make.log
make install >/tmp/make_install.log 2&>1
tail -n 20 /tmp/make_install.log

cd /usr/local
rm -rf /usr/local/slurm-$NAME
rm /usr/local/$1

# NOTE: removing tar seems to break stuff.
apt-get purge -y gcc make wget libssl-dev libmunge-dev
apt-get autoremove -y
apt-get clean -y
