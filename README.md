# zbt-midnights
Graph and FlowNetwork classes + methods

Repurposed to be applied to assigning ZBT midnights (our house chores). There are scripts that currently read in the results of a Google form of brothers' preferences for the week, converts the fields to a JSON, passes this JSON into the core min-cost max flow algorithm, and then utilizes the JSON of the week's assignments + points gained to populate a midnights master spreadsheet. 

Currently have:
 1. Google form set up linked to a prefs spreadsheet
 2. Master spreadsheet for points and tabs/sheets for the midnights of different weeks
 3. Script to read from/write to all these spreadsheets (must manually enter ranges though...I'll change this soon), that also converts the info into a JSON ready to be used
 4. The core algorithm that uses the above generated JSON to generate assignments + max flow etc
 5. Script to populate the assignments + points into the master spreadsheet (also manual ranges needed, rip)

### TODO:
1. **Finished** Make the ranges adjustable/automatic for both the master spreadsheet and the preferences
2. When ready, use the Spring prefs spreadsheet ID instead of the one for the Copy of Fall prefs
3. Finish TODOs in Graph.py and FlowNetwork.py
4. (if time permits) automatic emailing out of the prefs form each week

### Usage
*Setup*
1. Clone this repo locally via HTTPS or SSH key (tutorial here: https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)
2. (For this step, use an incognito broswer if you don't want your current google account login to be messed up) Log in to zbtmidnights@gmail.com
3. Follow steps 1 and 2 on this page: https://developers.google.com/sheets/api/quickstart/python (Note: use pip3 instead of pip and ensure that you have python3 by typing in your terminal ```which python3``` and make sure it says something like /usr/bin/python3, or /home/bill/anaconda3/bin/python3 if you're in an anaconda env)
4. Set up the authentication flow (basically the same as step 4 of the above quickstart tutorial): Run ```python3 authFlowSetup.py```. Now you should have read + write access to the spreadsheets linked to the ZBT account. You can verify that this step was successful if a token.pickle file was saved and contains "https://www.googleapis.com/auth/spreadsheet" inside somewhere (it can have random characters before and after, but as long as that is there and there's no "readonly" then you're gucci). There will also be a credentials.json that you should download into this directory on your local machine (move it from Downloads to wherever this dir is)

*Actual Usage*

5. Ok now everything's set up, you can send out the midnights pref form for the current week. This includes midnight preferences (eg dishes + commons etc.) and day preferences (eg M, W, F).
6. Read in all preferences, points, and midnight tasks/values via some fancy script boi: In the terminal, run: ```python3 read_prefs_pts_tasks.py <insert-path-to-output-JSON>```
7. Find the min-cost max flow assignments, and save them: In the terminal, run ```python3 midnights.py <path-to-JSON-from-step6> <path-to-output-assignments-JSON>```
8. Update + populate the master spreadsheet with new point/assignment values: In the terminal, run ```python3 midnight_sheets.py <path-to-assignments-JSON-from-step7>```
9. Repeat steps 5-8 each subsequent week.
