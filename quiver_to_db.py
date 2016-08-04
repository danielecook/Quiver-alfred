#!/usr/bin/python
# encoding: utf-8
import sys
from workflow import Workflow
from peewee import *
from glob import iglob
import json
import os
from playhouse.sqlite_ext import SqliteExtDatabase, SearchField, FTSModel
import datetime
wf = Workflow()
libpath = wf.stored_data('library_location')

db = SqliteExtDatabase("quiver.db")
if os.path.exists("quiver.db"):
    os.remove("quiver.db")

# Create the database

class Note(Model):
    uuid = CharField()
    title = CharField(index = True)
    notebook = CharField(index = True)
    last_modified = DateTimeField()

    class Meta:
        database = db


class NoteIndex(FTSModel):
    uuid = CharField()
    title = SearchField()
    content = SearchField()

    class Meta:
        database = db
        extension_options = {'tokenize': 'porter'}


class Tags(Model):
    note = ForeignKeyField(Note, related_name='Tags')
    tag = CharField(index = True)

    class Meta:
        database = db

#class Snippets(Model):
#    note = ForeignKeyField(Note, related_name='Snippets')
#    language = CharField(index = True)
#
#    class Meta:
#        database = db
#
#class SnippetsIndex(FTSModel):
#    uuid = CharField()
#    title = SearchField()
#    content = SearchField()
#
#    class Meta:
#        database = db



db.create_tables([Note, NoteIndex, Tags], safe = True)

def load_json(f):
    return json.loads(open(f, 'r').read())

# Store notes
with db.atomic():
    for notebook in iglob(libpath + "/*"):
        meta = load_json(list(iglob(notebook + "/meta.json"))[0])
        nb_name = meta["name"]

        for c in iglob(notebook + "/*.qvnote/content.json"):
            meta = load_json(c.replace("content.json", "meta.json"))
            content = load_json(c)
            tagset = meta["tags"]
            full_content = ' '.join([x["data"] for x in content["cells"]])
            snippets = [x for x in content["cells"] if x["type"] == "code"]
            # Store Notes
            n = Note.create(uuid = meta["uuid"],
                 title = meta["title"],
                 notebook = nb_name,
                 last_modified = datetime.datetime.fromtimestamp(meta["updated_at"]))
            NoteIndex.insert({
                NoteIndex.docid: n.id,
                NoteIndex.uuid: n.uuid,
                NoteIndex.title: n.title,
                NoteIndex.content: full_content}).execute()
            # Store tags
            for tag in tagset:
                Tags.create(note = n, tag = tag)
            #for snip in snippets:
            #    s = Snippets.create(note = n.id, language = snip["language"])
            #    SnippetsIndex.insert({
            #                            SnippetsIndex.docid: s.id,
            #                            SnippetsIndex.uuid: n.uuid,
            #                            SnippetsIndex.title: n.title,
            #                            SnippetsIndex.content: snip["data"]
            #                        }).execute()
def item():
    return 1
wf.cached_data('update_db', item, max_age=10)
