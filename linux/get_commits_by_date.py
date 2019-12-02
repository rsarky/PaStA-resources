#!/usr/bin/env python3

import git
from datetime import datetime

def parse_ymd(ymd):
    return datetime.strptime(ymd, "%Y-%m-%d")

d_repo = './repo'
upstream_head = 'v5.4'
after = parse_ymd('2019-05-01')
before = parse_ymd('2030-01-01')

repo = git.Repo(d_repo)

log = repo.git.log('--pretty=format:%H %ai', '--no-merges', upstream_head).splitlines()
for line in log:
    line = line.split(' ')
    hash, date = line[0], line[1]
    date = parse_ymd(date)
    if after <= date <= before:
        print(hash)
