# clickup_to_joplin
Script to convert a Clickup CSV export file into a Joplin JEX file for import.

Adapted from [tiddlywiki_to_joplin](https://github.com/FloatingBoater/tiddlywiki_to_joplin/)

## Args
    No external args, only internal constant definitions

## Parameters
    InputFile    (str):  Constant string filename of the CSV export from Clickup.
    OutputDir    (str):  Constant string directory name created to hold exported MD files.
    Author       (str):  Creator name.
    DoNotConvert (list): List of statuses. Tasks with these statuses will not be converted.

## Usage
*  Obtain a Clickup CSV export.
*  Edit the filename parameters below.
*  Run this script.
*  Check the directory of individual *.md files, each containing one Clickup task.
*  After checking the *.md files, create a tar file of the note files - which is what a JEX file consists of:
      $ cd clickup_notes
      $ tar cvf clickup_export.jex *.md
*  You can them import the file 'joplin_conversion.jex' into Joplin.
*  After import, inside Joplin, you will find all your Space folders inside a clickup_notes notebook. IF desired, you can drag the Space folders onto the "Notebooks" header to move them to the top level. If there are any tasks left in clickup_notes, they were probably "open" (converted) children of a "closed" (non-converted) parent task.

## Notes/Caveats:
*  This script was made for my own use and is not exaustive. Fields from the Clickup CSV export which aren't handled include attachments, priority, assignees, time related fields (sans creation date) and assignee comments.

*  This script only handles CSV task export, and therefore does not support doc pages, attachments, exported views, dashboard cards, or alternative export formats.

*  Clickup CSV export does not preserve task order, formatting of any sort, checkbox item status, list descriptions, task linking, reminders, or anything fancy like that.

*  Since Joplin doesn't have subtasks/subnotes, tasks which have children will be converted to a folder. If the task had any content, that data will be put into its own note as a child to the new folder, with order 1 (meaning it will show at the top of the notebook when sorting by custom order).

## Useful references:
    https://joplinapp.org/api/references/rest_api/
    https://help.clickup.com/hc/en-us/articles/6310551109527-Workspace-Task-Data-Export-CSV-
"""
