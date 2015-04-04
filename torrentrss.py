#!/usr/bin/env python3

from subprocess import check_call, DEVNULL
import sys
import xml.sax

from os import path
from urllib.request import urlopen

class ArgenteamMiner(xml.sax.handler.ContentHandler):
    def __init__(self):
        # Just some flags to determine if we're in that node
        self.state = { "item" : False, "title" : False, "link" : False }
        self.title, self.link = "", ""
        self.mapping = {}

    def startElement(self, name, attrs):
        if name in self.state:
            self.state[name] = True

    def endElement(self, name):
        if name in self.state:
            self.state[name] = False
        if name == "item":
            self.mapping[self.title] = self.link
            self.link = ""

    def characters(self, data):
        if self.state["item"]:
            if self.state["title"]:
                self.title = data
            elif self.state["link"]:
                self.link += data

    def __iter__(self):
        stream = urlopen('http://www.argenteam.net/rss/tvseries_torrents.xml')
        self.mapping = {}
        parser = xml.sax.make_parser()
        parser.setContentHandler(self)
        parser.parse(stream)
        return self

    def __next__(self):
        try:
            title, link = self.mapping.popitem()
        except:
            raise StopIteration
        else:
            return (title, link)


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
    shows = set([
        "GameOfThrones",
        "BigBangTheory",
    ])
    processed = path.join(
        path.dirname(path.realpath(__file__)), "processed-torrents.log")

    exclude = load_processed_urls(processed)
    torrents = set((title, link) for title, link in ArgenteamMiner()
                                  if link not in exclude)
    for title, link in torrents:
        matchshows = set(s for s in shows if title.startswith(s))
        if len(matchshows):
            try:
                check_call(
                    ["/usr/bin/transmission-remote", "--add", link],
                    stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, timeout=5)
            except:
                sys.stderr.write("Failed to add %s [%s]\n" % (title, link))
            finally:
                exclude.add(link)
            shows -= matchshows
    # don't download the same thing
    update_processed_urls(processed, exclude)
