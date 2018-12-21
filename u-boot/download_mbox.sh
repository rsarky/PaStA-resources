#!/bin/bash
#
# Copyright (c) OTH Regensburg, 2018
#
# Author:
#   Ralf Ramsauer <ralf.ramsauer@oth-regensburg.de>
#
# This work is licensed under the terms of the GNU GPL, version 2.  See
# the COPYING file in the top-level directory.

D_RAW="resources/mbox/raw"
MBOX="$D_RAW/mbox-uboot"
LINKS=$(lynx -dump -listonly https://lists.denx.de/pipermail/u-boot/ | grep .txt.gz | cut -b 7-)

mkdir -p $D_RAW

for link in $LINKS; do
	curl $link | zcat -d >> $MBOX
done
