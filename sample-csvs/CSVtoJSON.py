import re, json
# import argparse, os
import sys

# TODO: Make this a command-line interface Python script
def convertMidnightPrefs(inpPath: str) -> dict:
    """
    Given an input path to a csv file of midnight/day prefs, output a dictionary storing preferences.
    Format:
    Timestamp,name,week giving preferences for?,task preferences [str, ...],day preferences [str, ...]
    @param inpPath: path to the input .csv file storing preferences
    @return Mapping of dayPreferences and midnightPreferences acc. to format specified in midnights.py
    """
    with open(inpPath, "r") as infile:
        lines = infile.readlines()
        people = set()
        midnightPreferences = {}
        dayPreferences = {}
        for line in lines:
            data = re.split(",(?=\\S)", line)
            if data[0].strip() == "Timestamp":  # Skip title row
                continue
            name = data[1].strip()
            people.add(name)
            targetWeek = data[2].strip()
            midnightPrefs = [m.strip() for m in data[3][1:-1].split(",")]  # Remove \" from start and end
            midnightPreferences[name] = midnightPrefs
            dayPrefs = [d.strip() for d in data[4].strip()[1:-1].split(",")]
            dayPreferences[name] = dayPrefs

    return {"midnightPreferences": midnightPreferences, "dayPreferences": dayPreferences}

def convertMidnightsAndPoints(inpPath: str) -> dict:
    """
    Given path to input midnights .csv file, output a dictionary storing midnight requirements per day and point values
    @param inpPath: path to input .csv file containing midnight requirements and point values
    @return: Mapping of dayToMidnights, midnightPointValues acc. to format specified in midnights.py
    """
    dayToMidnights = {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []}
    midnightPointValues = {}
    with open(inpPath, "r") as infile:
        lines = infile.readlines()
        i = 0
        while i < len(lines):
            info = lines[i].split(",")
            day = info[0].strip()
            if day == "Day/Date":  # Skip title row
                i += 1
                continue
            if day in dayToMidnights:
                task, pointVal = info[1].strip(), info[2].strip()
                dayToMidnights[day].append(task)
                midnightPointValues[task] = float(pointVal)
                i += 1
                info = lines[i].split(",")
                while info[0].strip() not in dayToMidnights:
                    task, pointVal = info[1].strip(), info[2].strip()
                    if not task:
                        i += 1
                        if i >= len(lines):
                            break
                        info = lines[i].split(",")
                        continue
                    dayToMidnights[day].append(task)
                    midnightPointValues[task] = float(pointVal)
                    i += 1
                    if i >= len(lines):
                        break
                    info = lines[i].split(",")
            else:
                assert False  # Format invalid, specify day in row directly below end of previous midnights block

    return {"dayToMidnights": dayToMidnights, "midnightPointValues": midnightPointValues}

def convertPointsProgress(inpPath: str) -> dict:
    """
    Given path to input points .csv file, output a dictionary storing points progress
    @param inpPath: path to input .csv file containing midnight points progress for each person
    @return: Mapping of progress acc to midnights.py format
    """
    progress = {}
    with open(inpPath, "r") as infile:
        lines = infile.readlines()
        for line in lines:
            info = line.split(",")
            if info[0].strip() == "Brother":  # Make sure we skip the title row
                continue
            name, totalPoints = info[0].strip(), info[3].strip()
            assert name not in progress
            progress[name] = float(totalPoints)
    return {"progress": progress}
#
# def file_path(string):
#     if os.path.isfile(string):
#         return string
#     else:
#         raise FileNotFoundError(string)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Converts fields from 3 CSVs into a JSON required for midnights.py")
    # parser.add_argument('prefs', type=file_path, help='path to midnight + day preferences CSV')
    # parser.add_argument('week', type=file_path, help="path to the week's midnights CSV")
    # parser.add_argument('points', type=file_path, help='path to midnight points CSV')
    # args = parser.parse_args()
    assert len(sys.argv) >= 5  # ["CSVtoJSON.py", <path1>, <path2>, <path3>, <outpath>]

    preferencesMap = convertMidnightPrefs(sys.argv[1])
    midnightsMap = convertMidnightsAndPoints(sys.argv[2])
    progressMap = convertPointsProgress(sys.argv[3])
    result = {}
    for m in (preferencesMap, midnightsMap, progressMap):
        for k, v in m.items():
            result[k] = v
    result["midnightsToNumReq"] = {m: 1 for m in midnightsMap["midnightPointValues"]}
    result["people"] = [bro for bro in progressMap["progress"]]
    for bro in result["people"]:
        if bro not in preferencesMap["midnightPreferences"]:
            preferencesMap["midnightPreferences"][bro] = list(midnightsMap["midnightPointValues"].keys())
        if bro not in preferencesMap["dayPreferences"]:
            preferencesMap["dayPreferences"][bro] = list(midnightsMap["dayToMidnights"].keys())
    with open(sys.argv[4], "w") as outFile:
        json.dump(result, outFile)
