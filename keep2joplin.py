#!/usr/bin/env python3

# 1. Use Google Takeout to get a full dump of Keep Notes.
# 2. Run this script as 'python keep2joplin.py <note1.json> <note2.json> ... > /tmp/keep-import.enex'
# 3. Use Joplin's import -> enex as markdown

import base64
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time

from typing import Optional, IO, List, Tuple, Dict


def parseDt(dttm: str) -> Optional[dt.datetime]:
    FORMATS: list[str] = [
        "%b %d, %Y, %I:%M:%S %p",
    ]
    for fmt in FORMATS:
        try:
            return dt.datetime.strptime(dttm, fmt)
        except ValueError:
            pass
    return None


def getImageSize(path: str) -> Tuple[int, int]:
    proc = subprocess.run(f"identify {path}",
                          shell=True,
                          stdout=subprocess.PIPE,
                          check=True)
    size: str = proc.stdout.split()[2].decode('utf-8')
    assert size
    dimensions: List[str] = size.split("x")
    return (int(dimensions[0]), int(dimensions[1]))


def formatResource(attachment: Dict[str, str]) -> Tuple[str, str]:
    width, height = getImageSize(attachment['filePath'])
    digest: str
    b64: str
    with open(attachment['filePath'], "rb") as afile:
        abytes: bytes = afile.read()
        digest = hashlib.md5(abytes).hexdigest()
        b64: str = base64.b64encode(abytes).decode('utf-8')

    return (f"""<div>
<en-media
    type="{attachment["mimetype"]}"
    width="{width}"
    height="{height}"
    hash="{digest}"/>
</div>""", f"""<resource>
<data encoding="base64">{b64}</data>
<mime>{attachment["mimetype"]}</mime>
<resource-attributes>
    <file-name>{attachment['filePath']}</file-name>
</resource-attributes>
</resource>""")


def translateNote(path: str):
    ifile: IO
    with open(path) as ifile:
        note = json.load(ifile)
        title: str = note['title'].replace("&", "&amp;")

        # Parse note dates
        noteCreated: str = time.strftime(
            '%Y%m%dT%H%M%SZ', time.gmtime(note['createdTimestampUsec'] / 1e6))
        noteUpdated: str = time.strftime(
            '%Y%m%dT%H%M%SZ',
            time.gmtime(note['userEditedTimestampUsec'] / 1e6))

        # Parse note tags
        tags: List[str] = ['keep']
        if 'labels' in note:
            tags.extend(l['name'] for l in note['labels'])
        if note['isArchived']:
            tags.append("archived")
        if note['isTrashed']:
            tags.append("trashed")
        if note['isPinned']:
            tags.append("pinned")
        noteTags: str = "\n".join(f"<tag>{t}</tag>" for t in tags)

        # Format images into note
        mediaTags: Tuple[str, ...] = tuple()
        resources: Tuple[str, ...] = tuple()
        if 'attachments' in note:
            mediaTags, resources = zip(
                *[formatResource(a) for a in note['attachments']])

        content: str = (
            note['textContent'].replace("\n", "<br/>")
            if 'textContent' in note
            else "\n".join(
                f'<en-todo checked="{str(t["isChecked"]).lower()}"/>{t["text"]}<br/>'
                for t in note['listContent']
            )
            if 'listContent' in note
            else "EMPTY"
        )

        return """<note>
<title>{title}</title>
<content>
<![CDATA[<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd"><en-note style="word-wrap: break-word; -webkit-nbsp-mode: space; -webkit-line-break: after-white-space;">{content}</en-note>{tags}]]>
</content>
<created>{noteCreated}</created>
<updated>{noteUpdated}</updated>
{noteTags}
<note-attributes>
  <latitude>0</latitude>
  <longitude>0</longitude>
  <source>google-keep</source>
  <reminder-order>0</reminder-order>
</note-attributes>
{resources}
</note>""".format(title=title,
                  content=content,
                  tags="\n".join(mediaTags),
                  noteCreated=noteCreated,
                  noteUpdated=noteUpdated,
                  noteTags=noteTags,
                  resources="\n".join(resources))


def keep2enex(notePaths: List[str]) -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="{exdate}" application="Evernote/Windows" version="6.x">
{notes}
</en-export>""".format(exdate=dt.datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                       notes="\n".join(translateNote(n) for n in notePaths))


if __name__ == "__main__":
    print(keep2enex(sys.argv[1:]))

sys.exit(0)
