from midnight_sheets import *
import json, sys

PREFS_SHEET_ID = "16a_DVp-Tq5mhHbhUX1xUWUK0O-gOjzHPyfOYiXiaAF4"
MIDNIGHT_PREFS_RANGE = "Form Responses 1!D2:D22"
DAY_PREFS_RANGE = "Form Responses 1!E2:E22"
PREF_NAMES_RANGE = "Form Responses 1!B2:B22"
MASTER_NAMES_RANGE = "Total Points!A2:A28"

TASK_VALUE_RANGES = ["%s!C2:C12" % WEEK, "%s!C14:C23" % WEEK, "%s!C25:C33" % WEEK, "%s!C35:C44" % WEEK, "%s!C46:C54" % WEEK, "%s!C56:C62" % WEEK]


def add_prefs(d: dict):
    midnightPreferences, dayPreferences = {}, {}
    names = flatten_nested_list(read_vals(PREFS_SHEET_ID, PREF_NAMES_RANGE))
    mPrefs = flatten_nested_list(read_vals(PREFS_SHEET_ID, MIDNIGHT_PREFS_RANGE))
    dPrefs = flatten_nested_list(read_vals(PREFS_SHEET_ID, DAY_PREFS_RANGE))
    for i, boi in enumerate(names):
        midnightPreferences[boi] = [m.strip() for m in mPrefs[i].split(",")]
        dayPreferences[boi] = [d.strip() for d in dPrefs[i].split(",")]
    d["midnightPreferences"] = midnightPreferences
    d["dayPreferences"] = dayPreferences

def add_points(d: dict):
    names = flatten_nested_list(read_vals(MASTER_SHEET_ID, MASTER_NAMES_RANGE))
    pts = flatten_nested_list(read_vals(MASTER_SHEET_ID, POINTS_RANGE))
    d["progress"] = {n: float(p) for n, p in zip(names, pts)}

def add_midnights(d: dict):
    dayToMidnights, midnightPointValues = {}, {}
    for i, entry in enumerate(read_vals(MASTER_SHEET_ID, MASTER_WEEK_DAY_RANGE)):
        if not entry:
            continue
        day = entry[0]
        if day in day_order:
            day_idx = day_order.index(day)
            task_range = TASK_RANGES[day_idx]
            dayMidnights = flatten_nested_list(read_vals(MASTER_SHEET_ID, task_range))  # List of day's midnights
            value_range = TASK_VALUE_RANGES[day_idx]
            dayMidnightValues = flatten_nested_list(read_vals(MASTER_SHEET_ID, value_range))

            dayAssignments = []
            assert len(dayMidnights) == len(dayMidnightValues)
            for m, val in zip(dayMidnights, dayMidnightValues):
                dayAssignments.append(m)
                midnightPointValues[m] = float(val)
            dayToMidnights[day] = dayAssignments
    d["dayToMidnights"] = dayToMidnights
    d["midnightPointValues"] = midnightPointValues

def generate_JSON():
    d = {}
    add_prefs(d)
    add_points(d)
    add_midnights(d)
    return d


if __name__ == "__main__":
    result = generate_JSON()
    result["midnightsToNumReq"] = {m: 1 for m in result["midnightPointValues"]}
    result["people"] = [bro for bro in result["progress"]]
    for bro in result["people"]:
        if bro not in result["midnightPreferences"]:
            result["midnightPreferences"][bro] = list(result["midnightPointValues"].keys())
        if bro not in result["dayPreferences"]:
            result["dayPreferences"][bro] = list(result["dayToMidnights"].keys())
    outPath = sys.argv[1]
    with open(outPath, "w") as outfile:
        json.dump(result, outfile)
