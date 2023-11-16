#!/usr/bin/python3
""" clickup_to_joplin.py

Script to convert a Clickup CSV export file into a Joplin JEX file for import.

Adapted from tiddlywiki_to_joplin: https://github.com/FloatingBoater/tiddlywiki_to_joplin/

Args:
    No external args, only internal constant definitions

Parameters:
    InputFile    (str):  Constant string filename of the CSV export from Clickup.
    OutputDir    (str):  Constant string directory name created to hold exported MD files.
    Author       (str):  Creator name.
    DoNotConvert (list): List of statuses. Tasks with these statuses will not be converted.

Usage:
    Obtain a Clickup CSV export.
    Edit the filename parameters below.
    Run this script.
    Check the directory of individual *.md files, each containing one Clickup task.

    After checking the *.md files, create a tar file of the note files - which is what a JEX file consists of:
      $ cd clickup_notes
      $ tar cvf clickup_export.jex *.md
    You can them import the file 'joplin_conversion.jex' into Joplin.

    After import, inside Joplin, you will find all your Space folders inside a clickup_notes notebook. IF desired, you can drag the Space folders onto the "Notebooks" header to move them to the top level. If there's any tasks left in clickup_notes, they were probably open/etc children of a closed/etc parent task.

Notes/Caveats:
    This script was made for my own use and is not exaustive. Fields from the Clickup CSV export which aren't handled include attachments, priority, assignees, time related fields (sans creation date) and assignee comments.

    This script only handles CSV task export, and therefore does not support doc pages, attachments, exported views, dashboard cards, or alternative export formats.

    Clickup CSV export does not preserve task order, formatting of any sort, checkbox item status, list descriptions, task linking, reminders, or anything fancy like that.

    Since Joplin doesn't have subtasks/subnotes, tasks which have children will be converted to a folder. If the task had any content, that data will be put into its own note as a child to the new folder, with order 1 (meaning it will show at the top of the notebook when sorting by custom order).

Useful references:
    https://joplinapp.org/api/references/rest_api/
    https://help.clickup.com/hc/en-us/articles/6310551109527-Workspace-Task-Data-Export-CSV-
"""

import datetime
import csv
import uuid
import os
import re
import ast
from enum import Enum
from pathlib import Path

###
### change these values as needed
###
InputFile = 'clickupExport.csv'
OutputDir = 'clickup_notes'
Author = ''
DoNotConvert = ['closed', 'complete']

ConvertToFolder = set() # Tasks which have subtasks and therefore need to be converted into folders since Joplin doesn't support subtasks

class Type(Enum):
    TYPE_NOTE = 1
    TYPE_FOLDER = 2
    TYPE_SETTING = 3
    TYPE_RESOURCE = 4
    TYPE_TAG = 5
    TYPE_NOTE_TAG = 6
    TYPE_SEARCH = 7
    TYPE_ALARM = 8
    TYPE_MASTER_KEY = 9
    TYPE_ITEM_CHANGE = 10
    TYPE_NOTE_RESOURCE = 11
    TYPE_RESOURCE_LOCAL_STATE = 12
    TYPE_REVISION = 13
    TYPE_MIGRATION = 14
    TYPE_SMART_FILTER = 15

def format_content( text ):
    return text.replace('\\n', '<br />')

def format_checklist( text ):
    if get_valid_string(False, text):
        text = text.split(':', 1)
        header = text[0][2:-1]
        items = ast.literal_eval(text[1][0:-1])
        text = "### " + header + "\n"
        for item in items:
            text += "- [ ] " + item + "\n"
    return text

def write_note_to_file(note_id, parent_id, name, created_time, updated_time, user_created_time, user_updated_time, type, order=0, content=None, checklists=None):
    ClickupFile = open(OutputDir + '/' + note_id + '.md', 'x')
    ClickupFile.write(name + '\n')
    ClickupFile.write('\n')
    if get_valid_string(False, content):
        ClickupFile.write(content + '\n')
        ClickupFile.write('\n')
    if get_valid_string(False, checklists):
        ClickupFile.write(checklists + '\n')
        ClickupFile.write('\n')
    ClickupFile.write('id: ' + note_id + '\n')
    ClickupFile.write('parent_id: ' + parent_id + '\n')
    ClickupFile.write('created_time: ' + created_time + '\n')
    ClickupFile.write('updated_time: ' + updated_time + '\n')
    ClickupFile.write('is_conflict: 0' + '\n')
    ClickupFile.write('latitude: 55.088' + '\n')
    ClickupFile.write('longitude: -1.5863' + '\n')
    ClickupFile.write('altitude: 0.0000' + '\n')
    ClickupFile.write('author: ' + Author + '\n')
    ClickupFile.write('is_todo: 0' + '\n')
    ClickupFile.write('todo_due: 0' + '\n')
    ClickupFile.write('todo_completed: 0' + '\n')
    ClickupFile.write('source: com.clickup' + '\n')
    ClickupFile.write('source_application: clickup_to_joplin' + '\n')
    ClickupFile.write('application_data: ' + '\n')
    ClickupFile.write('order: ' + str(order) + '\n')
    ClickupFile.write('user_created_time: ' + user_created_time + '\n')
    ClickupFile.write('user_updated_time: ' + user_updated_time + '\n')
    ClickupFile.write('encryption_cipher_text: ' + '\n')
    ClickupFile.write('encryption_applied: 0' + '\n')
    # no '\n' on the last line - it causes Joplin import errors
    ClickupFile.write('type_: ' + str(type))
    ClickupFile.close()

def write_tag_to_file(tag_id, name, created_time, updated_time, user_created_time, user_updated_time):
    path = Path(OutputDir + '/' + tag_id + '.md')
    if not path.is_file():
        ClickupFile = open(path, 'x')
        ClickupFile.write(name + '\n')
        ClickupFile.write('\n')
        ClickupFile.write('id: ' + tag_id + '\n')
        ClickupFile.write('created_time: ' + created_time + '\n')
        ClickupFile.write('updated_time: ' + updated_time + '\n')
        ClickupFile.write('user_created_time: ' + user_created_time + '\n')
        ClickupFile.write('user_updated_time: ' + user_updated_time + '\n')
        ClickupFile.write('encryption_cipher_text: ' + '\n')
        ClickupFile.write('encryption_applied: 0' + '\n')
        ClickupFile.write('is_shared: 0' + '\n')
        # no '\n' on the last line - it causes Joplin import errors
        ClickupFile.write('type_: ' + str(Type.TYPE_TAG.value))
        ClickupFile.close()

def write_tag_association_to_file(id, note_id, tag_id, created_time, updated_time, user_created_time, user_updated_time):
    path = Path(OutputDir + '/' + id + '.md')
    if not path.is_file():
        ClickupFile = open(path, 'x')
        ClickupFile.write('id: ' + id + '\n')
        ClickupFile.write('note_id: ' + note_id + '\n')
        ClickupFile.write('tag_id: ' + tag_id + '\n')
        ClickupFile.write('created_time: ' + created_time + '\n')
        ClickupFile.write('updated_time: ' + updated_time + '\n')
        ClickupFile.write('user_created_time: ' + user_created_time + '\n')
        ClickupFile.write('user_updated_time: ' + user_updated_time + '\n')
        ClickupFile.write('encryption_cipher_text: ' + '\n')
        ClickupFile.write('encryption_applied: 0' + '\n')
        ClickupFile.write('is_shared: 0' + '\n')
        # no '\n' on the last line - it causes Joplin import errors
        ClickupFile.write('type_: ' + str(Type.TYPE_NOTE_TAG.value))
        ClickupFile.close()

# Convert a name to an id by removing non-alphanumerical characters
def as_id(string):
    return ''.join(s for s in string if s.isalnum())

# Return the first string in the list which isn't empty/None or "null"/"hidden"/"{}"/"[]" (Clickup "keywords"). Else return default.
# A "hidden" folder value means the list has no folder.
def get_valid_string(default, *strings):
    for s in strings:
        if s and s != "null" and s != "hidden" and s != "{}" and s != "[]":
            return s
    return default

if not os.path.exists(InputFile):
    print("InputFile does not exist - check script filename <" + InputFile + ">.")
    quit(-1)

with open(InputFile) as csv_file:
    clickup_project = csv.DictReader(csv_file, delimiter=',')

    # Create a directory for tasks as Joplin notes
    if not os.path.exists(OutputDir):
        os.mkdir(OutputDir)
        print("Output directory ", OutputDir,  " created")
    else:
        print("Output directory ", OutputDir,  " already exists")

    top_level_notebook_id = uuid.uuid4().hex
    dt_created  = datetime.datetime.now().isoformat('T','milliseconds')

    # Create the top level Notebook called ClickupImport to contain imported notes
    write_note_to_file(
        note_id = top_level_notebook_id,
        parent_id = "", # blank parent_id as top-level notebook
        name = 'Clickup Import',
        created_time = dt_created,
        updated_time = dt_created,
        user_created_time = dt_created,
        user_updated_time = dt_created,
        type = Type.TYPE_FOLDER.value
    )

    # Do an initial loop to determine which tasks have subtasks
    for task in clickup_project:
        if task['Status'].lower() in DoNotConvert:
            continue
        # If parent id exists, add it to list of tasks which need to be turned into folders
        if (get_valid_string(task['Parent ID'])):
            ConvertToFolder.add(task['Parent ID'])

    # Go back to beginning of CSV file
    csv_file.seek(0)
    next(clickup_project)

    # Create sets of tuples of
    #   1. clickup spaces/folders/lists id (the name in this case)
    #   2. parent id
    #   3. grandparent id (for a List, this is the Space, regardless if the Folder is hidden/nonexistent)
    clickup_spaces = set()
    clickup_folders = set()
    clickup_lists = set()
    for row in clickup_project:
        if row['Status'].lower() in DoNotConvert:
            continue
        clickup_spaces.add((row['Space Name'], top_level_notebook_id, ''))
        if (get_valid_string(False, row['Folder Name'])): # ignore "hidden" folders
            clickup_folders.add((row['Folder Name'], row['Space Name'], top_level_notebook_id))
            clickup_lists.add((row['List Name'], row['Folder Name'], row['Space Name']))
        else:
            clickup_lists.add((row['List Name'], row['Space Name'], top_level_notebook_id))

    # Create a notebook for each Clickup space, folder, and list
    # Using space/folder/list name + parent name as ID isn't really the best, but eh, it's decently unique
    for entry in clickup_spaces | clickup_folders | clickup_lists:
        write_note_to_file(
            note_id = as_id(entry[0] + "IN" + entry[1]), # use name + parent id as unique id (strip the non-alphanumerical chars)
            parent_id = as_id(entry[1] + "IN" + entry[2]), # similarly, parent id + grandparent id
            name = entry[0],
            created_time = dt_created,
            updated_time = dt_created,
            user_created_time = dt_created,
            user_updated_time = dt_created,
            type = Type.TYPE_FOLDER.value
        )

    line_count = 0

    # Go back to beginning of CSV file
    csv_file.seek(0)
    next(clickup_project)

    for task in clickup_project:
        # The Clickup heirarchy looks like: Clickup Project -> Space -> Folder -> List -> Task -> Subtask

        if line_count == 0:
            print(f'Column names are:\t{", ".join(task)}\n')
            print(f'parent_id:\t{top_level_notebook_id}\n')
            line_count += 1
            continue

        if task['Status'].lower() in DoNotConvert:
            continue

        note_id = task['Task ID']
        parent_id = task.get('Parent ID') if get_valid_string(False, task.get('Parent ID')) else as_id(task.get('List Name') + "IN" + get_valid_string(task['Space Name'], task['Folder Name']))

        # Clickup "Date Created" uses epoch time in milliseconds
        # Joplin uses '2017-12-07T12:56:17.000Z' which is basically ISO 8601 format with mS
        dt_created = datetime.datetime.fromtimestamp(float(task['Date Created']) / 1000.0).isoformat( 'T','milliseconds')
        type = Type.TYPE_NOTE.value
        content = format_content(task['Task Content'])
        checklists = format_checklist(task['Checklists'])
        tags = task['Tags'][1:-1]
        tags = tags.split(',') if tags != "" else []

        # If task has subtasks, convert it to a folder instead
        if note_id in ConvertToFolder:
            type = Type.TYPE_FOLDER.value
            # If task contains content, create a new task to house the content
            if get_valid_string(False, content, checklists):
                write_note_to_file(
                    note_id = note_id + "TaskContent",
                    parent_id = note_id,
                    name = "Original content from " + task[' Task Name'],
                    created_time = dt_created,
                    updated_time = dt_created,
                    user_created_time = dt_created,
                    user_updated_time = dt_created, # no modified date in clickup
                    type = Type.TYPE_NOTE.value,
                    content = content,
                    checklists = checklists,
                    order = 1 # Display this task at top of notebook
                )
            content = None
            checklists = None

        write_note_to_file(
            note_id = note_id,
            parent_id = parent_id,
            name = task[' Task Name'],
            created_time = dt_created,
            updated_time = dt_created,
            user_created_time = dt_created,
            user_updated_time = dt_created, # no modified date in clickup
            type = type,
            content = content,
            checklists = checklists
        )

        if tags:
            for tag in tags:
                tag_id = as_id("TAG" + tag)
                write_tag_to_file(
                    tag_id = tag_id,
                    name = tag,
                    created_time = dt_created,
                    updated_time = dt_created,
                    user_created_time = dt_created,
                    user_updated_time = dt_created
                )
                write_tag_association_to_file(
                    id = tag_id + "ASSOCIATEDWITH" + note_id,
                    note_id = note_id,
                    tag_id = tag_id,
                    created_time = dt_created,
                    updated_time = dt_created,
                    user_created_time = dt_created,
                    user_updated_time = dt_created
                )

        line_count += 1

    print('===============')
    print(f'Processed {line_count} lines.')
    print(f'created a new Notebook with id:\t{top_level_notebook_id}\n')
