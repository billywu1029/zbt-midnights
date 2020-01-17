"""
Implementation of the algorithm for ZBT midnights (AKA our system for doing chores throughout our fraternity house).
Uses the max flow code developed in this directory + input preferences + midnights structure to setup a Flow Network
and then use Ford Fulkerson to find the max flow (and obviously find the optimal midnights assignment for the week).

@author: Bill Wu
Date: 12/30/19
"""

from FlowNetwork import *
import json, sys

POINTS_REQ = 59
PERSON_BASE_COST = 10
# PREFER_DAY_PENALTY = 30
PREFER_MIDNIGHT_PENALTY = 10
STRONGLY_AGAINST_PENALTY = 50  # Could potentially be used later when implementing multiple levels of preferences
NEED_MIDNIGHT_REWARD = -50  # Reduce cost if really need this midnight and boi can do the midnight
LIMITED_OPTIONS_REWARD = -40  # Reduce cost if boi can only do limited amount of midnights and boi can do the midnight
LIMITED_OPTIONS_MIDNIGHTS_REQ = 2  # max number of midnights one can pref to qualify as having "limited options"
# Penalty for someone taking a higher point value midnight when they have higher point progress
POINT_FAIRNESS_PENALTY_MULTIPLIER = 5
MIDNIGHTS_PER_DAY_LIMIT = 1
MIDNIGHTS_PER_WEEK_LIMIT = 2
CAN_ASSIGN_NOT_PREF_MIDNIGHTS = True
CAN_ASSIGN_NOT_PREF_DAYS = False

def weightedPersonCost(pointsProgress: float) -> int:
    """
    Gets a weighted cost of assigning a midnight to each person, determined by:
        PERSON_BASE_COST ** (1 + person's pointsProgress / POINTS_REQ)
    Intuition: The more midnight points someone has, the less midnights they should be assigned, and vice versa.
    @param pointsProgress: number of midnight points the person has
    @return: int of max num of midnights one person should be allowed in a week
    """
    return int(round(PERSON_BASE_COST ** (1 + pointsProgress / POINTS_REQ)))

def getMidnightAssignments(G: FlowNetwork, people: list) -> dict:
    """
    Gets the mapping of midnight assignments for each person according to a Flow Network G.
    Assumes that max flow has already been found in G, behavior unspecified o/w.
    @param G: Input flow network, assumed to have optimal max flow values already filled in.
    @param people: input list of people (repr as name strings) available to do midnights for the week
    @return: dict mapping each person in people to list of midnights (with day) they should do
    """
    result = {}
    for boi in people:
        u = Vertex(boi)
        daysAssigned = (dayBoi for dayBoi in G.flowGraph.getChildren(u) if G.flowGraph.getWeight(u, dayBoi) > 0)
        result[boi] = []
        for day in daysAssigned:
            for m in G.capacityGraph.getChildren(day):
                if G.flowGraph.getWeight(day, m) > 0:
                    result[boi].append(m.val)
    return result

def createNewMidnightVertex(day: str, m: str, i: int) -> Vertex:
    """
    Create a new Vertex with string val that concatenates all three pieces of information together:
        day, midnight, and midnight number
    @param day: which day the midnight is assigned
    @param m: the midnight
    @param i: the midnight number, ie waitings 1 or waitings 2 would have i=1 and i=2 respectively
    @return: Vertex with str val that has all the information concatenated in a separable fashion
    """
    return Vertex("%s|%s|%r" % (day, m, i))

def createNewDayVertex(day: str, boi: str) -> Vertex:
    """Create a new Vertex containing a str value that concatenates day and boi together"""
    return Vertex("%s|%s" % (day, boi))

# def getDayCost(preferDay: bool) -> int:
#     """
#     Gets the cost associated with a edge from person to their day node, based on whether or not the day was preferred
#     @param preferDay: True if the day was preferred, and False o/w
#     @return: cost as an int following the formula: 1(dayPreffed) * PREFER_DAY_PENALTY
#     """
#     return PREFER_DAY_PENALTY if not preferDay else 0

def getCostBoiDayToMidnight(preferMidnight: bool, midnightVal: int, boiPoints: int, numPref: int, numAvail: int) -> int:
    """
    Gets the cost for an edge from a person to any corresponding midnight. Intuitively, should assign low cost for
    midnights that are more preferred, and higher cost if not preferred. Can even use different levels of preference
    so that strongly prefer -> 0 cost, strongly do not prefer -> super high cost.
    @param preferMidnight: True to indicate that the midnight is preferred, False o/w
    @param midnightVal: How many points the midnight is worth
    @param boiPoints: How many points the person has
    @param numPref: Number of people who pref'ed the midnight
    @param numAvail: Total number of midnights that the current person can do/number of midnights pref'ed
    @return: int generated via formula:
        1(preferMidnight) * PREFER_MIDNIGHT_PENALTY
    """
    # TODO: Different levels of preference to potentially create useful backdoors to guarantee midnights you want
    midnightPrefPenalty = STRONGLY_AGAINST_PENALTY if not preferMidnight else 1
    # If only 1 person can do the midnight, then reduce the cost dramatically for the one that can do it
    midnightNeededReward = NEED_MIDNIGHT_REWARD if preferMidnight and numPref == 1 else 0
    # If the person can only do 1 or 2 midnights, then reduce the cost if the midnight is one they actually can do
    # eg. poker/sports/adt bois only get back really late so they can only do like commons or sth easy later at night
    limitedOptionsReward = LIMITED_OPTIONS_REWARD if preferMidnight and numAvail <= LIMITED_OPTIONS_MIDNIGHTS_REQ else 0
    return midnightPrefPenalty + midnightNeededReward + limitedOptionsReward \
           + int(midnightVal ** 2 * boiPoints / POINTS_REQ * POINT_FAIRNESS_PENALTY_MULTIPLIER)

def getPeopleMidnightsToDayAssignments(peopleTasksMap: dict) -> dict:
    """
    Given a mapping of people to their list of midnights, return a new map that maps each day to the corresponding
    people that are in turn mapped to whichever midnights they were assigned to do for that particular day.
    """
    result = {"Monday": {}, "Tuesday": {}, "Wednesday": {}, "Thursday": {}, "Friday": {}, "Saturday": {}, "Sunday": {}}
    for boi in peopleTasksMap:
        for m in peopleTasksMap[boi]:
            day, midnight, idx = m.strip().split("|")  # Stay safe by stripping, remember that kids
            if boi in result[day]:
                result[day][boi].append(midnight)
            else:
                result[day][boi] = [midnight]
    return result

def getPeoplePointsGain(dayToAssignments: dict, pointsMap: dict) -> dict:
    """
    Given a mapping of day to midnight assignments for each person, output a mapping of each person to points gained
    @param dayToAssignments: input mapping taking the form: {M: {Jack: [bathrooms, dinings], Bill: [commons], ...}, ...}
    @param pointsMap: maps midnights to their associated point values
    @return: mapping taking the form: {Bill: 1, Jack: 2, ...}
    """
    result = {}
    for day in dayToAssignments:
        for person in dayToAssignments[day]:
            if person not in result:
                result[person] = 0
            for m in dayToAssignments[day][person]:
                result[person] += pointsMap[m]
    return result

def extractData(inPath: str) -> tuple:
    """
    Given a filename path to an input JSON file, extracts the data into a tuple of dictionaries
    @param inPath: input file str, must point to valid JSON file following the format:
        "dayToMidnights": {M: [bathrooms, dinings, ...], T: [...], ...}
        "midnightPointValues": {bathrooms: 1, dinings: 2, ...}
        "midnightsToNumReq: {bathrooms: 1, dinings: 2, ...}
        "people": [Bill, Jack, Daniel, Eric, ...]
        "dayPreferences": {Bill: [M, W, F], Jack: [F, Sa, Su], ...}
        "midnightPreferences": {Bill: [bathrooms, dinings, ...], Jack: [commons, dishes, ...], ...}
        "progress": {Bill: 21, Jack: 35, ...}
    @return: tuple of dictionaries + lists from the JSON, ordered as such:
        (dayToMidnights, midnightPointValues, midnightsToNumReq, people, dayPreferences, midnightPreferences, progress)
    """
    with open(inPath, "r") as infile:
        info = json.load(infile)
        dayToMidnights = info["dayToMidnights"]
        midnightPointValues = info["midnightPointValues"]
        midnightsToNumReq = info["midnightsToNumReq"]
        people = info["people"]
        dayPreferences = info["dayPreferences"]
        midnightPreferences = info["midnightPreferences"]
        progress = info["progress"]
    return dayToMidnights, midnightPointValues, midnightsToNumReq, people, dayPreferences, midnightPreferences, progress

def generateMidnightsFlowNetwork(dayToMidnights: dict,
                                 midnightPointValues: dict,
                                 midnightsToNumReq: dict,
                                 people: list,
                                 dayPreferences: dict,
                                 midnightPreferences: dict,
                                 progress: dict,
                                 outPath: str = None) -> FlowNetwork:
    """
    Given midnights preferences/points info, generates a Flow Network to model the ZBT midnights assignment problem
    Optionally, write the Flow Network to an output JSON file, specified with path outPath
    @param dayToMidnights: Days mapped to midnights needed that day
    @param midnightPointValues: Point values for each midnight
    @param midnightsToNumReq: Midnights mapped to number of people req for each chore
    @param people: List of all people available for midnights
    @param dayPreferences: Midnight preferences for which days are best
    @param midnightPreferences: Which midnights each person prefers
    @param progress: Number of midnights points each person has
    @param outPath: (optional) output file str, if doesn't exist, then creates the file under the tests/ directory.
        Follows format specified in FlowNetwork's serializeJSON method
    @return: Flow Network that models the midnights assignment problem
    """
    S, T = Vertex("S"), Vertex("T")
    G = FlowNetwork(S, T)
    v = {}  # Stores the mapping of string to Vertex wrapper (used to identify/add edges to/from bois in graph)

    for boi in people:
        v[boi] = Vertex(boi)
        # Edges from source to people limited by number of midnights per week, and cost based on midnight point progress
        G.addEdge(S, v[boi], MIDNIGHTS_PER_WEEK_LIMIT, weightedPersonCost(progress[boi]))

    for boi in people:
        for boisDay in dayToMidnights:  # all 7 days for each boi to capture midnights/day limit
            if CAN_ASSIGN_NOT_PREF_DAYS:
                dayWithBoi = createNewDayVertex(boisDay, boi)
                G.addEdge(v[boi], dayWithBoi, MIDNIGHTS_PER_DAY_LIMIT, 1)
            else:
                # TODO: Refactor so this isn't copy-paste
                # Limit by day preferences, ie only days pref'ed will have an edge from the boi -> day
                if boisDay in dayPreferences[boi]:
                    dayWithBoi = createNewDayVertex(boisDay, boi)
                    G.addEdge(v[boi], dayWithBoi, MIDNIGHTS_PER_DAY_LIMIT, 1)

    # Gather midnight preference counts per midnight, so as to weight midnights that can only be done by 1 person
    # very negative, so that they are guaranteed to be assigned to them
    midnightsPrefCountMap = {}
    for boi in midnightPreferences:
        for midnight in midnightPreferences[boi]:
            midnightsPrefCountMap[midnight] = midnightsPrefCountMap.get(midnight, 0) + 1

    for day in dayToMidnights:
        for m in dayToMidnights[day]:
            for i in range(midnightsToNumReq[m]):
                midnightWithDay = createNewMidnightVertex(day, m, i)
                # Edges from midnights to sink with weight 1, cost 1
                G.addEdge(midnightWithDay, T, 1, 1)
                for boi in people:
                    if CAN_ASSIGN_NOT_PREF_MIDNIGHTS:
                        dayWithBoi = createNewDayVertex(day, boi)  # Just re-obtaining the dayboi Vertex for reference
                        # Edge from every boi's day to every midnight pref'ed, cost depends on progress
                        costBoiDayToMidnight = getCostBoiDayToMidnight(
                            m in midnightPreferences[boi],
                            midnightPointValues[m],
                            progress[boi],
                            midnightsPrefCountMap[m],
                            len(midnightPreferences[boi])
                        )
                        G.addEdge(dayWithBoi, midnightWithDay, 1, costBoiDayToMidnight)
                    else:
                        # TODO: Refactor so this isn't copy-paste
                        # Limit by midnight preferences, ie only midnights pref'ed will have edge (boiDay, midnight)
                        if m in midnightPreferences[boi]:
                            dayWithBoi = createNewDayVertex(day, boi)
                            # Edge from every boi's day to every midnight pref'ed, cost depends on progress
                            costBoiDayToMidnight = getCostBoiDayToMidnight(
                                m in midnightPreferences[boi],
                                midnightPointValues[m],
                                progress[boi],
                                midnightsPrefCountMap[m],
                                len(midnightPreferences[boi])
                            )
                            G.addEdge(dayWithBoi, midnightWithDay, 1, costBoiDayToMidnight)

    if outPath is not None:
        G.serializeToJSON(outPath)

    return G

def generateMinCostMaxFlowAssignments(G: FlowNetwork, people: list, midnightPointValues: dict, outPath: str):
    """
    Finds the min-cost max flow given a Flow Network, G, and writes the results to a JSON file w format:
        "cost": min cost max flow total cost
        "maxFlow": total flow
        "dayAssignments": mapping of day to a sub-mapping of person mapped to list of assigned midnights for that day
        "pointsGained": mapping of people to their corresponding point values gained for the week, based on midnights
    @param G: input Flow Network
    @param people: list of people
    @param midnightPointValues: mapping of midnights to their corresponding point values
    @param outPath: path to output file - output file will be created/overwritten
    """
    cost, maxFlow = G.getMinCostMaxFlow()
    print("Min-cost Max Flow identified...")
    peopleMidnightMap = getMidnightAssignments(G, people)
    dayToMidnightAssignmentsMap = getPeopleMidnightsToDayAssignments(peopleMidnightMap)
    peoplePointsGain = getPeoplePointsGain(dayToMidnightAssignmentsMap, midnightPointValues)
    result = {"cost": cost, "maxFlow": maxFlow, "dayAssignments": dayToMidnightAssignmentsMap,"pointsGained": peoplePointsGain}
    with open(outPath, "w") as outfile:
        json.dump(result, outfile)


if __name__ == "__main__":
    inpPath = sys.argv[1]  # Path of the input JSON containing prefs, points, etc.
    outPath = sys.argv[2]  # Path of the output JSON of max flow assignments
    flowNetworkSave = "flowboiTest.json"
    dayToMidnights, midnightPointValues, midnightsToNumReq, people, dayPreferences, midnightPreferences, progress = extractData(inpPath)
    print("Data extracted from JSON...")
    G = generateMidnightsFlowNetwork(dayToMidnights, midnightPointValues, midnightsToNumReq, people, dayPreferences,
                                     midnightPreferences, progress)
    print("Flow Network generated...")
    generateMinCostMaxFlowAssignments(G, people, midnightPointValues, outPath)
    print("Assignments saved to %s" % outPath)
    G.serializeToJSON(flowNetworkSave)  # Serializing after finding the min cost max flow
    print("Flow Network saved to %s" % flowNetworkSave)
