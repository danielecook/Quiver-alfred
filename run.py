#!/usr/bin/python
# encoding: utf-8

import sys

from workflow import Workflow, ICON_ERROR, ICON_INFO, ICON_SYNC
from workflow.background import run_in_background, is_running
from quiver_to_db import Note, NoteIndex, Tags, db
from peewee import *
import os
from subprocess import call
from playhouse.sqlite_ext import SqliteExtDatabase


def display_notes(notes):
    for note in notes:
        wf.add_item(note.title, arg=note.uuid, valid=True, icon="icons/note.png")


def search_notes(phrase):
    # Query the search index and join the corresponding Document
    # object on each search result.
    return (NoteIndex
            .select()
            .join(
                NoteIndex,
                on=(NoteIndex.id == NoteIndex.docid))
            .where(NoteIndex.match(phrase))
            .order_by(NoteIndex.bm25()))

def tag_filter_key(tag):
    return "#" + tag["tag"]


def main(wf):
    args = wf.args[0]
    # Do stuff here ...
    # Add an item to Alfred feedback
    libpath = wf.stored_data('library_location')

    if not libpath:
        wf.add_item('Set Quiver Library with qset', icon=ICON_INFO)
        wf.send_feedback()
        return
    db.connect()

    if not os.path.exists("quiver.db"):
        wf.add_item('Constructing database...', icon=ICON_INFO)
        call(['/usr/bin/python',
                           wf.workflowfile('quiver_to_db.py')])
        wf.send_feedback()

    # Add a notification if the script is running
    if is_running('update'):
        wf.add_item('Constructing database...', icon=ICON_INFO)

    icon_set = {"Inbox" : "icons/inbox.png", "Recents": "icons/recent.png", "Trash": "icons/trash.png"}

    tagset = list(Tags.select(Tags.tag, fn.COUNT(Tags.id).alias("count"))
                        .group_by(Tags.tag)
                        .distinct()
                        .dicts()
                        .execute())
    notebooks = list(Note.select(Note.notebook, fn.COUNT(Note.id).alias("count"))
                        .group_by(Note.notebook)
                        .distinct()
                        .dicts()
                        .execute())
    notebooks_list = [x["notebook"] for x in notebooks]
    try:
        notebooks_list.remove("Inbox")
        notebooks_list.remove("Trash")
    except:
        pass
    notebooks_list = ["Inbox", "Recents", "Trash"] + notebooks_list
    taglist = [x["tag"] for x in tagset]
    ttaglist = ["#" + x for x in taglist]
    targ = "#" + args
    # Searching by Tag
    if args.startswith(u"#"):
        if args in ttaglist:
            notes = Note.select(Tags, Note).filter(args.strip("#") == Tags.tag).join(Tags).distinct().execute()
            display_notes(notes)
        else:
            tag_filter = wf.filter(args, tagset, tag_filter_key)
            for tag in tag_filter:
                tag_name = tag_filter_key(tag)
                wf.add_item(tag_name, str(tag["count"]) + " item(s)",  autocomplete=tag_name, icon="icons/tag.png")

    # Searching by Notebook
    elif args in notebooks_list:
        if args == "Recents":
            # Show Recents
            display_notes(Note.select().order_by(-Note.last_modified).distinct().limit(10).execute())
        else:
            display_notes(Note.select().filter(Note.notebook == args).execute())
    else:
        notebooks_q = {x["notebook"]: x for x in notebooks}
        if len(args) > 0:
            notebooks_list = wf.filter(args, notebooks_list)
        for n in notebooks_list:
            if n in icon_set:
                icon = icon_set[n]
            else:
                icon = "icons/notebook.png"
            if n == "Recents":
                wf.add_item("Recents", autocomplete="Recents", icon=icon)
            else:
                # Default retrieval `notebook = n' with `count = 0' to prevent keyerror on empty Index / Trash
                notebook = notebooks_q.get(n, {"notebook": n, "count": 0})
                wf.add_item(notebook["notebook"], str(notebook["count"]) + " item(s)", autocomplete = n, icon = icon)

        if len(args) > 0:
            # Perform Search!
            results = NoteIndex.search_bm25(
                                    args,
                                    weights={'title': 2.0, 'content': 1.0},
                                    with_score=True,
                                    score_alias='search_score').order_by(NoteIndex.rank())
            if len(results) == 0:
                wf.add_item("No Results", icon=ICON_ERROR)
            else:
                for result in results:
                    r = Note.get(uuid=result.uuid)
                    wf.add_item(r.title, str(result.search_score) + "-" + unicode(result.content),  arg=r.uuid, valid=True, icon="icons/note.png")


    wf.send_feedback()

    # Regenerate database if it is old.
    if not wf.cached_data_fresh('update_db', 3600):
        log.debug("REWRITING DB!!!")
        run_in_background('update',
                          ['/usr/bin/python',
                           wf.workflowfile('quiver_to_db.py')])


if __name__ == '__main__':
    # Create a global `Workflow` object
    wf = Workflow(update_settings={'github_slug': 'danielecook/Quiver-alfred', 'version': '0.5'})
    if wf.update_available:
        # Download new version and tell Alfred to install it
        wf.start_update()
    # Call your entry function via `Workflow.run()` to enable its helper
    # functions, like exception catching, ARGV normalization, magic
    # arguments etc.
    log = wf.logger
    sys.exit(wf.run(main))
