#!./venv/bin/python3
# This script looks up a train station name based on it's short form from stations.json
import sys
import json


def getStationName(shortform):
    with open("stations.json", "r") as file: 
        stations = json.load(file)
        if shortform in stations:
            return stations[shortform]
        else:
            return False
    file.close()

def main(): 

# Check if the script has been given the right number of arguments
    if len(sys.argv) != 2 or sys.argv[1] == "--help" or  sys.argv[1] == "-h":
        print("Lookup a train station name based on it's short form")
        print(f"Usage: {sys.argv[0]} [SHORT_FORM]")
        exit()

    stationShort = sys.argv[1].upper()
    station = getStationName(stationShort)
    
    if station: 
        print(f"Short form: {stationShort}") 
        print(f"Stations name: {station}")
    else: 
        print(f"No result for station with short form {stationShort}")

if __name__ == '__main__':
    main()

