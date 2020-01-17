from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json, sys

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Automatically converts entries to equations or dates, as opposed to "RAW"
# Docs: https://developers.google.com/sheets/api/reference/rest/v4/ValueInputOption
VALUE_INPUT_OPTION = "USER_ENTERED"

# Spring Prefs Master Spreadsheet
MASTER_SHEET_ID = "1NIMm76tU172GJtPkJleR_Vx9A7LgVwM3E_X3E7OuHEA"
WEEK = "12/8 to 12/14"
BROS_RANGE = "Total Points!A2:A28"
ASSIGN_RANGE = "%s!D2:D54" % WEEK
POINTS_RANGE = "Total Points!B2:B28"
MASTER_WEEK_DAY_RANGE = "%s!A2:A62" % WEEK
TASK_RANGES = ["%s!B2:B12" % WEEK, "%s!B14:B23" % WEEK, "%s!B25:B33" % WEEK, "%s!B35:B44" % WEEK, "%s!B46:B54" % WEEK, "%s!B56:B62" % WEEK]
ASSIGN_DAYS_RANGES = ["%s!D2:D12" % WEEK, "%s!D14:D23" % WEEK, "%s!D25:D33" % WEEK, "%s!D35:D44" % WEEK, "%s!D46:D54" % WEEK, "%s!D56:D62" % WEEK]

day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Saturday"]

def flatten_nested_list(L):
    """Flattens a list of the format [ [str], [str], ... ]"""
    result = []
    for i in L:
        result.append(i[0])
    return result

def convert_assignments_format(assignments: dict) -> dict:
    """Converts assignments from format of {day: {boi: midnight, ...}, ...}
    to format of {day: {midnight: boi, ...}, ...}"""
    result = {}
    for day in assignments:
        result[day] = {}
        for boi in assignments[day]:
            midnights = assignments[day][boi]
            for m in midnights:
                result[day][m] = boi
    return result

def populate_assignments_and_points(inPath: str, bros: list):
    """
    Uses Sheets API to fill in midnight assignments and points gained on the spreadsheet specified by WEEK_MIDNIGHT_ID.
    @param inPath: input path to assignments JSON file
    @param bros: list of brothers included in the current week of midnights, order must match that in the midnight sheet
        Is of type list<str>.
    """
    with open(inPath, "r") as infile:
        info = json.load(infile)
        pts = info["pointsGained"]
        assignments = convert_assignments_format(info["dayAssignments"])  # Converted to {day: {m: boi, ...}, ...}

        currPts = flatten_nested_list(read_vals(MASTER_SHEET_ID, POINTS_RANGE))
        assert len(bros) == len(currPts)
        pointsArr = []
        for i, bro in enumerate(bros):  # Add each bro's point gain in same order as they appeared in bros
            if bro not in pts:
                pointsArr.append([currPts[i]])
            else:
                # add points to prev total, if the bro gained points this week
                # also technically adding a "row of elements" so need a list wrapper here
                pointsArr.append([pts[bro] + float(currPts[i])])
        write_vals(MASTER_SHEET_ID, POINTS_RANGE, pointsArr)

        day_idx = 0
        days_col = read_vals(MASTER_SHEET_ID, MASTER_WEEK_DAY_RANGE)
        for entry in days_col:
            if not entry:
                continue
            day = entry[0]
            if day in day_order:
                dayAssignments = []
                task_range = TASK_RANGES[day_order.index(day)]
                dayMidnights = flatten_nested_list(read_vals(MASTER_SHEET_ID, task_range))  # List of day's midnights
                for m in dayMidnights:
                    if m not in assignments[day]:
                        continue
                    dayAssignments.append([assignments[day][m]])
                write_vals(MASTER_SHEET_ID, ASSIGN_DAYS_RANGES[day_idx], dayAssignments)
                day_idx += 1

def get_sheets_api():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    return service.spreadsheets()

def write_vals(sheet_id: str, sheet_range: str, values: list):
    """
    Writes in the values in the list of vals into the specified range for the spreadsheet with ID sheet_id
    @param sheet_id: input sheet ID, can be found in a spreadsheet's URL between spreadsheet/d/ ... /edit
    @param sheet_range: input specified range
    @param values: list of row values to write in, repr as a list of list of strs
    """
    sheet = get_sheets_api()
    body = {"values": values}
    result = sheet.values().update(
        spreadsheetId=sheet_id, valueInputOption=VALUE_INPUT_OPTION, range=sheet_range, body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))


def read_vals(sheet_id: str, sheet_range: str) -> list:
    """Gets a list of elements in a given sheet_range from the specified Sheet (via sheet_id)
    Handles authentication/sheets client automatically.
    @param sheet_id: input sheet ID, can be found in a spreadsheet's URL between spreadsheet/d/ ... /edit
    @param sheet_range: input specified range
    @return: list of elements from the specified sheet in the specified range. Note that this will be a list of lists
        since each row contains multiple elements
    """
    sheet = get_sheets_api()
    result = sheet.values().get(spreadsheetId=sheet_id,
                                range=sheet_range).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return []
    else:
        print("gimme those yummy cells")
        return values


if __name__ == '__main__':
    # assignmentsPath = sys.argv[1]
    assignmentsPath = "assignmentsOnlyPrefs.json"
    populate_assignments_and_points(assignmentsPath, flatten_nested_list(read_vals(MASTER_SHEET_ID, BROS_RANGE)))
    a = 1
