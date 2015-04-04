#!/usr/bin/env python3

import difflib
import mimetypes
import re
import sys
import xml.sax

from os import path
from urllib.request import urlopen

class SubdivxDownload(xml.sax.handler.ContentHandler):
    def __init__(self, searchstr):
        # Just some flags to determine if we're in that node
        self.state = { "item" : False, "title" : False,
                       "link" : False, "description": False }
        self.title, self.link, self.description = "", "", ""
        self.searchstr = searchstr
        self.items = []

    def startElement(self, name, attrs):
        if name in self.state:
            self.state[name] = True

    def endElement(self, name):
        if name in self.state:
            self.state[name] = False
        if name == "item":
            self.items.append({
                "title": self.title,
                "link": self.link,
                "desc": self.description
            })

    def characters(self, data):
        if self.state["item"]:
            if self.state["title"]:
                self.title = data
            elif self.state["link"]:
                self.link = data
            elif self.state["description"]:
                self.description= data

    def __iter__(self):
        stream = urlopen('http://www.subdivx.com/feed.php?buscar=' + self.searchstr)
        self.items = []
        parser = xml.sax.make_parser()
        parser.setContentHandler(self)
        parser.parse(stream)
        return self

    def __next__(self):
        try:
            return self.items.pop()
        except:
            raise StopIteration

def build_searchstr(scrapeurl):
    try:
        base, episode, rest = re.split(
            "([sS][0-9]{2}[eE][0-9]{2}|[0-9]{1,2}x[0-9]{1,2})",
            scrapeurl, maxsplit=1)
    except ValueError:
        sys.stderr.write("Failed to scrape url\n")
        sys.exit(1)
    else:
        if 'x' in episode:
            episode = "S{:02d}E{:02d}".format(
                *[int(x) for x in episode.split('x')])

    base = re.sub("^magnet:.*=", "", base)
    base = re.sub("^http:.*/", "", base)
    searchstr = re.sub("[._]", "+", base) + episode
    return searchstr, base, episode, rest


def subdivx_link(searchstr, rest):
    best = None
    m = difflib.SequenceMatcher(lambda x: x in " \t:-,.&%#$!+[]{}=")
    for s in SubdivxDownload(searchstr):
        m.set_seqs(rest, s["desc"])
        ratio = m.ratio()
        if not best or ratio > best["ratio"]:
            best = s
            best["ratio"] = ratio
    if best:
        html = urlopen(best["link"]).read().decode("latin-1")
        l = re.search('"(?P<link>http://www.subdivx.com/bajar.php?[^"]*)"', html)
        if l:
            return l.group("link")
    return None


def load_processed_urls(processed):
    excluded = set()
    try:
        with open(processed) as uf:
            excluded = set(l.rstrip() for l in uf)
    except FileNotFoundError:
        pass
    return excluded

def update_processed_urls(processed, newset):
    with open(processed, "w") as uf:
        uf.writelines(l + '\n' for l in newset)


if __name__ == '__main__':
    subspath = "/data/torrents"
    subsdone = path.join(
        path.dirname(path.realpath(__file__)), "downloaded-subs.log")
    pendingsubs = path.join(
        path.dirname(path.realpath(__file__)), "processed-torrents.log")

    exclude = load_processed_urls(subsdone)
    pending = load_processed_urls(pendingsubs) - exclude

    for torrenturl in pending:
        searchstr, base, episode, rest = build_searchstr(torrenturl)
        suburl = subdivx_link(searchstr, rest)
        try:
            stream = urlopen(suburl)
            contenttype = stream.getheader("Content-Type")
            sub = stream.read()
        except:
            sys.stderr.write("Failed to add %s [%s]\n" % (title, link))
        else:
            extension = mimetypes.guess_extension(contenttype)
            subfile = (re.sub("[^a-zA-Z0-9.]", "_", base) + "_" +
                       re.sub("[^a-zA-Z0-9.]", "_", episode) +
                       extension)
            subfile = path.join(subspath, subfile)
            with open(subfile, "wb") as sf:
                sf.write(sub)
        finally:
            exclude.add(torrenturl)
    # don't download the same thing
    update_processed_urls(subsdone, exclude)
