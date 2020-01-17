# zbt-midnights
Graph and FlowNetwork classes + methods

Repurposed to be applied to assigning ZBT midnights (our house chores). WIP, but works (sorta?) (as of 1/17), but the goal is to eventually have a script that automatically emails out a Google form to gather brothers' preferences for the week, enters them into a midnights master Google spreadsheet, reads those values and convert the fields to a JSON, passes it into the core max flow algorithm, converts the JSON of assignments + points gained into a CSV, and then imports it into a copy of the midnights master spreadsheet for that week. 

Currently have:
 1. Google form set up linked to a prefs spreadsheet
 2. Master spreadsheet for points and tabs/sheets for the midnights of different weeks
 3. Script to read from/write to all these spreadsheets (must manually enter ranges though...I'll change this soon), that also converts the info into a JSON ready to be used
 4. The core algorithm that uses the above generated JSON to generate assignments + max flow etc
 5. Script to populate the assignments + points into the master spreadsheet (also manual ranges needed, rip)

### TODO:
1. Make the ranges adjustable/automatic for both the master spreadsheet and the preferences
2. When ready, use the Spring prefs spreadsheet ID instead of the one for the Copy of Fall prefs
3. **IMPORTANT:** Make a new google account for zbt midnights and create the spreadsheets using that account, so that any cloned repo can request access tokens as long as they know the username/password of the zbt google account.
4. Finish TODOs in Graph.py and FlowNetwork.py
5. (if time permits) automatic emailing out of the prefs form each week

### Usage
(as of 1/17)
1. **(Spreadsheets are WIP Still)** Clone this repo locally via HTTPS or SSH key (tutorial here: https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)
2. Send out the Spring midnights pref form each week. This includes midnight preferences (eg dishes + commons etc.) and day preferences (eg M, W, F).
3. Read in all preferences, points, and midnight tasks/values via some fancy script boi: In the terminal, run: ```python3 read_prefs_pts_tasks.py <insert-path-to-output-JSON>```
4. Find the min-cost max flow assignments, and save them: In the terminal, run ```python3 midnights.py <path-to-JSON-from-step3> <path-to-output-assignments-JSON>```
5. Update + populate the master spreadsheet with new point/assignment values: In the terminal, run ```python3 midnight_sheets.py <path-to-assignments-JSON-from-step4>```
6. Repeat steps 2-5 each subsequent week.
