import pprint
import csv
import json

pp = pprint.PrettyPrinter(indent=4)
filename = 'kamernet/kamers1309.csv'

rows = []

# Read file
with open(filename, newline='') as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Format string to be json
        adProperties = row['woningdetails'].replace("'", '"')
        adProperties = json.loads(adProperties)

        # Make keys lowercase
        adProperties = dict((k.lower(), v) for k,v in adProperties.items())

        del row['woningdetails']
        # pp.pprint(adProperties)
        row = { **row,
                **adProperties }

        # Add row to list of rows
        rows.append(row)


# pp.pprint(rows)
