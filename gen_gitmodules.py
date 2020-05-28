#!/usr/bin/env python3

"""
PaStA - Patch Stack Analysis

Copyright (c) OTH Regensburg, 2020

Author:
  Ralf Ramsauer <ralf.ramsauer@oth-regensburg.de>

This work is licensed under the terms of the GNU GPL, version 2.  See
the COPYING file in the top-level directory.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.
"""

import re
import requests

from time import sleep
from collections import defaultdict
from lxml import html

url_kernel_org = 'https://git.kernel.org/pub/scm/public-inbox'
url_lore = 'https://lore.kernel.org/lists.html'
url_github = 'https://raw.githubusercontent.com/lfd/mail-archiver/linux-archives/.gitmodules'

pubin_providers = ['git.kernel.org', 'lore.kernel.org', 'github.com']

lore_map = dict()

blacklist = {
    'kernelnewbies.org': {'kernelnewbies'},
    'lists.kernelnewbies.org': {'kernelnewbies'},
    'NetBSD.org': {'radiotap'},
    'dpdk.org': {'dev'},
    'linux.kernel.org': {'keys'},
    'lists.cip-project.org': {'cip-testing', 'cip-testing-results'},
    'lists.linuxfoundation.org': {'linux-kernel-mentees'},
    'lore.kernel.org': {'linux-firmware', 'signatures'},
    'vger.kernel.org': {'backports', 'fstests', 'linux-trace-users', 'linux-kernel', 'selinux-refpolicy', 'git', 'linux-rt-users'},
}

def get_tree(url):
    code = 0
    retries = 5
    while code != 200:
        resp = requests.get(url)
        code = resp.status_code
        if code != 200:
            print('Crap. sleeping.')
            sleep(5)
            retries -= 1
        if retries < 0:
            raise ValueError('Maximum retries reached')

    return html.fromstring(resp.content)


def get_kernel_org():
    ret = defaultdict(dict)

    tree = get_tree(url_kernel_org)
    links = tree.xpath('/html/body//a[@title]/@href')
    links = [link[len('/pub/scm/public-inbox/'):-1] for link in links]
    links = [link.split('/') for link in links]
    links = [link for link in links if len(link) == 3]

    for hoster, listname, shard in links:
        shard = int(shard[0:-4])
        hoster = ret[hoster]

        if listname not in hoster:
            hoster[listname] = 0
        hoster[listname] = max(shard, hoster[listname])

    return ret


def get_lore():
    lore_git_rgx = re.compile('\tgit clone --mirror (.+)(\d+) .*')

    ret = defaultdict(dict)

    tree = get_tree(url_lore)
    lists = tree.xpath('/html/body/table/tr/td/text()')
    lists = [list.split('.', 1) for list in lists]
    links = tree.xpath('/html/body/table/tr/td/a/@href')

    for list, link in zip(lists, links):
        list.append(link)

    for listname, hoster, link in lists:
        print('Working on %s - %s' % (hoster, listname))
        tree = get_tree(link)
        text = tree.xpath('/html/body//pre')[-1].text
        text = text.split('\n')
        max_shard = 0
        for line in text:
            match = lore_git_rgx.match(line)
            if not match:
                continue

            git = match.group(1)
            lore_map[listname] = git
            max_shard = max(int(match.group(2)), max_shard)

        ret[hoster][listname] = max_shard

    return ret


def get_github():
    ret = defaultdict(dict)

    matcher = re.compile('\tpath = archives/(.*)')
    project_matcher = re.compile('([^\.]+)\.(.*)\.(\d+)')
    gitmodules = requests.get(url_github).content.decode().split('\n')
    for line in gitmodules:
        match = matcher.match(line)
        if not match:
            continue
        project = match.group(1)
        if project.startswith('ASSORTED'):
            continue

        if project == 'b.a.t.m.a.n.lists.open-mesh.org.0':
            listname = 'b.a.t.m.a.n'
            hoster = 'lists.open-mesh.org'
            shard = 0
        else:
            match = project_matcher.match(project)
            listname, hoster, shard = match.group(1), match.group(2), match.group(3)
        shard = int(shard)

        hoster = ret[hoster]
        if listname not in hoster:
            hoster[listname] = 0
        hoster[listname] = max(shard, hoster[listname])

    return ret

def fill_missing(result, lists, uri_scheme):
    for hoster, lists in lists.items():
        if hoster not in result:
            result[hoster] = dict()
        for list in lists.keys():
            if list not in result[hoster]:
                result[hoster][list] = uri_scheme
    return result


def split_provider(provider_filter, data):
    ret = defaultdict(list)

    for hoster, lists in data.items():
        for listname, provider in lists.items():
            if provider != provider_filter:
                continue

            ret[hoster].append(listname)
    return ret

def generate_submodule(provider, hoster, listname, shard):
    ret = list()
    dst = 'linux/resources/mbox/pubin/%s/%s/%u.git' % (hoster, listname, shard)

    if provider == 'git.kernel.org':
        url = 'git://git.kernel.org/pub/scm/public-inbox/%s/%s/%u.git' % (hoster, listname, shard)
    elif provider == 'lore.kernel.org':
        url = '%s%u' % (lore_map[listname], shard)
    elif provider == 'github.com':
        url = 'https://github.com/linux-mailinglist-archives/%s.%s.%s' % (listname, hoster, shard)

    ret.append('[submodule "%s"]' % dst)
    ret.append('\tpath = %s' % dst)
    ret.append('\turl = %s' % url)
    return ret

data = dict()
data['git.kernel.org'] = get_kernel_org()
data['lore.kernel.org'] = get_lore()
data['github.com'] = get_github()

tmp = dict()
for provider in pubin_providers:
    tmp = fill_missing(tmp, data[provider], provider)

config = str()
for hoster in sorted(tmp.keys()):
    lists = set(tmp[hoster].keys())

    if hoster in blacklist:
        lists -= blacklist[hoster]

    if len(lists) == 0:
        continue

    config += '\n"%s" = [\n' % hoster
    for listname in sorted(lists):
        config += '\t"%s",\n' % listname
    config += ']\n'
    with open('linux-config', 'w') as f:
        f.write(config)


gitmodules = list()
for provider in pubin_providers:
    result = split_provider(provider, tmp)

    gitmodules.append('')
    gitmodules.append('##################################################')
    gitmodules.append('# Linux Public Inboxes hosted by %s' % provider)
    gitmodules.append('##################################################')

    for hoster in sorted(result.keys()):
        listnames = set(result[hoster])
        if hoster in blacklist:
            listnames -= blacklist[hoster]

        if len(listnames) == 0:
            continue

        gitmodules.append('')
        gitmodules.append('## %s' % hoster)
        for listname in sorted(listnames):
            max_shard = data[provider][hoster][listname] + 1
            for shard in range(0, max_shard):
                gitmodules += generate_submodule(provider, hoster, listname, shard)

gitmodules = '\n'.join(gitmodules)
with open('gitmodules', 'w') as f:
    f.write(gitmodules + '\n')
