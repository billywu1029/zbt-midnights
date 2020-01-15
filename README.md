# zbt-midnights
Graph and FlowNetwork classes + methods

Repurposed to be applied to assigning ZBT midnights (our house chores). Very WIP as of now (1/15), but the goal is to eventually have a script that automatically emails out a Google form to gather brothers' preferences for the week, enters them into a midnights master Google spreadsheet, reads those values and convert the fields to a JSON, passes it into the core max flow algorithm, converts the JSON of assignments + points gained into a CSV, and then imports it into a copy of the midnights master spreadsheet for that week. 

(Currently limited to just the core algorithm and a hacky CSV->JSON converter that requires 3 CSV documents in some predefined format. So someone would have to manually export spreadsheets to CSV, run the converter script on the CSVs, run the algorithm on the produced JSON, and then manually parse the JSON and update assignments + points in the spreadsheet.)

### TODO:
1. Make the CSV->JSON converter a CLI that takes in input paths of CSVs to be converted
2. Make a uniform format for CSVs that is more intuititve + allows for just 1 master spreadsheet instead of 3
3. Finish TODOs in Graph.py and FlowNetwork.py
4. (if time permits) Script that automatically fills in assignments + points in a Google spreadsheet given the output JSON.

### Usage
(as of 1/15, a lot of setup needs to be manually done still)
1. Make a Google form to gather everyone's preferences. This includes midnight preferences (eg dishes + commons etc.) and day preferences (eg M, W, F).
2. Create 3 Google spreadsheets, with formats specified in CSVtoJSON.py
3. Populate each spreadsheet with its corresponding data, ie midnightPoints starts with everyone's name followed by their total points in the 4th column (if 0 indexing it's the "3rd col"). (Take the Google form results for preferences and put it into midnightPrefs according to the format specified, and manually fill in weekMidnights)
4. Export all 3 to CSVs and save them in a directory with the CSVtoJSON.py script (alter the script if needed)
5. Run the converter script to generate the JSON
6. Pass in the JSON to the midnights.py script and run it, via python3 midnights.py \<insert-path-to-JSON-here\> \<insert-path-to-output-JSON-here\>
7. Take the values from the outputted JSON, fill in the Google spreadsheet with the assignments + new point values
8. After the first week, repeat steps 4-7 each week lol (step 3 as well if midnight requirements change)
