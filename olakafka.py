#!./venv/bin/python3
import json
from station import getStationName
from config import *
from datetime import datetime
from confluent_kafka import Consumer, TopicPartition

def CreateKafkaConsumer(): 
    config = {
    'bootstrap.servers': kafka_server,
    'security.protocol': 'SASL_SSL',
    #'sasl.mechanism': 'SCRAM-SHA-256',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': kafka_username,
    'sasl.password': kafka_password,
    'group.id': kafka_group_id,
    'auto.offset.reset': 'earliest'
    }
    
    # Create Consumer instance
    return Consumer(config)


def FetchKafkaOffsets(date_in, date_out, consumer): 
    
    topic = "queue.train.customer-information.operational-log.v1"

    #This topic has only one partition, setting it to 0 static  
    partition = 0

    # Fetch offsets for the specified times
    offsets_start = consumer.offsets_for_times([TopicPartition(topic, partition, int(date_in.timestamp() * 1000))])
    offsets_stop = consumer.offsets_for_times([TopicPartition(topic, partition, int(date_out.timestamp() * 1000))])

    # Extract offsets
    start_offset = offsets_start[0].offset if offsets_start[0] else None
    stop_offset = offsets_stop[0].offset if offsets_stop[0] else None

    #print(f'Start Offset: {start_offset}, Stop Offset: {stop_offset}')

    if start_offset is None or stop_offset is None:
        print("Could not find valid offsets. Exiting.")
        return 
    else:
        offsets = [start_offset, stop_offset]
        return offsets
        

def GetKafkaMessages(date_start, date_stop):
    
    # Create Consumer instance
    consumer = CreateKafkaConsumer()

    offsets = FetchKafkaOffsets(date_start, date_stop, consumer) 
    start_offset = offsets[0]
    stop_offset = offsets[1]
    
    #Number of messages to show per page
    page_messages=25

    num_pages = GetNumPages(start_offset, stop_offset, page_messages)
    num_messages = GetNumMessages(stop_offset, start_offset)
    #print(num_pages) 
   # print(num_messages)
    
    topic = "queue.train.customer-information.operational-log.v1"

    #This topic has only one partition, setting it to 0 static  
    partition = 0

    # Assign the topic partition with the start offset
    consumer.assign([TopicPartition(topic, partition, start_offset)])
    
    #Creating a list to hold the messages from kafka 
    kafka_messages = []

    # Now consume messages until we reach the stop offset
    while True:
        message = consumer.poll(timeout=1.0)
        if message is None:
            continue  # No message, poll again
        if message.error():
            print(f'Error: {message.error()}')
            continue

        # Use the correct way to access the offset attribute
        current_offset = message.offset()  
       
       # Print the message if it is within the desired offset range
        if current_offset <= stop_offset:
            kafka_messages.append(message.value().decode('utf-8'))
            #print(message.value().decode('utf-8') + "\n)  # Decode if message value is in bytes
        else:
            break  # Stop consuming when we've passed the stop offset
    
    # Close the consumer
    consumer.close()
    
    return kafka_messages

#A function that returns number of pages based in number of messages per page and offsets
def GetNumPages(start_offset, stop_offset, page_messages):
    num_messages = stop_offset - start_offset
    num_pages = round(num_messages / page_messages)
    return num_pages


#A function that returns the number of messages btweeen two offsets
def GetNumMessages(stop_offset, start_offset): 
    num_messages = stop_offset - start_offset
    return num_messages


#A functon that converts a timeformat
def converttime(time, source):
    # Check for the correct source and format
    if source == "kafka": 
        oldformat = "%Y-%m-%dT%H:%M:%S%z"  # Kafka format with timezone
        newformat = "%d-%m-%Y %H:%M:%S"
    elif source == "user": 
        # Check the format of the incoming time string
        try:
            # Try to parse the time as 'Y-m-d H:M:S'
            oldformat = "%Y-%m-%d %H:%M:%S"
            newformat = "%d-%m-%Y %H:%M:%S"
            datetime.strptime(time, oldformat)  # Try parsing with user format
        except ValueError:
            # If the above format doesn't work, assume it's 'd-m-Y H:M:S'
            oldformat = "%d-%m-%Y %H:%M:%S"
            newformat = "%d-%m-%Y %H:%M:%S"
        
    else:
        raise ValueError(f"Unknown source: {source}")
    
    try:
        # Parse the time string with the correct old format
        time = datetime.strptime(time, oldformat).strftime(newformat)
    except ValueError as e:
        print(f"Error parsing time '{time}' with format '{oldformat}': {e}")
        raise  # Re-raise the exception after logging the error
    
    return time

#def converttime(time, source):
#    if source == "kafka": 
#        oldformat = "%Y-%m-%dT%H:%M:%S%z"
#        newformat = "%d-%m-%Y %H:%M:%S"
#    if source == "user": 
#        oldformat = "%Y-%m-%d %H:%M:%S"
#        newformat = "%d-%m-%Y %H:%M:%S"
#
#    time = datetime.strptime(time,oldformat).strftime(newformat)
#    return time


#A function that compares a Kafka message to a file containting templates of data we want to present
def compareToTemplate(messages, template):
    if len(messages) == len(template):
        for messages_key, messages_value in messages.items():
            if not messages_key in template.keys():
                return False
            if isinstance(messages_value, dict):
                return (compareToTemplate(messages[messages_key], template[messages_key])) 
    else:
        return False
    return True

#a function that makes trainnumbers 5 digits by addin leading 0
def make5digit(trainnumber): 
    while len(trainnumber)<5:
        trainnumber = "0"+trainnumber
    
    return trainnumber


#a function that checks if the kafka message contains what the user searched for
def searchmatch(line, searchfilter):
    # Convert dates and format train number in search filter
    if searchfilter['date_from'] != "": 
        searchfilter['date_from'] = converttime(searchfilter['date_from'], "user")
    if searchfilter['date_to'] !="": 
        searchfilter['date_to'] = converttime(searchfilter['date_to'], "user")
    
    searchfilter['trainnumber'] = make5digit(searchfilter['trainnumber'])
    
    if searchfilter['trainnumber'] == "00000":
        searchfilter['trainnumber'] = ""
    
    # Initialize counter for matches
    nummatch = 0 
    
    # Loop through each key-value pair in search filter
    for searchkey, searchval in searchfilter.items():
        if searchval:  # Only match if there's a value
            if searchkey == 'date_from':
                # Parse both searchval and kafka_time as datetime for comparison
                date_from = datetime.strptime(searchval, "%d-%m-%Y %H:%M:%S")
                kafka_time = datetime.strptime(line.get('time'), "%d-%m-%Y %H:%M:%S") 
                if date_from <= kafka_time:
                    nummatch += 1
            
            elif searchkey == 'date_to':
                # Parse both searchval and kafka_time as datetime for comparison
                date_to = datetime.strptime(searchval, "%d-%m-%Y %H:%M:%S")
                kafka_time = datetime.strptime(line.get('time'), "%d-%m-%Y %H:%M:%S") 
                if date_to >= kafka_time:
                    nummatch += 1

            elif searchkey == 'station':  # Partial match for station
                if searchval.lower() in line.get(searchkey, '').lower():
                    nummatch += 1
            else:  # Exact match for other keys
                if searchval == line.get(searchkey):
                    nummatch += 1
        else:
            # Consider it a match by default if searchval is empty
            nummatch += 1

    # Return True if all search filters match
    return nummatch == len(searchfilter)



#A function that filter kafka messages and presents it readable
def filterKafkaMessages(messages, searchfilter):
    
    #reading a json container templates to use in order filter messages
    templates = []                        
    with open("message_templates.json", "r") as message_templates: 
        for line in message_templates: 
            templates.append(json.loads(line))
    message_templates.close()

    #creating a list that gets updated with filtered data
    filteredData = []
    for line in messages:
        match = False
        for template in templates:
            if match == False:
                match = compareToTemplate(line,template)
        
        if match:
        #if "id" in line and "type" in line:
            #line = json.loads(line)

            trigger = line["type"]
            timestamp = line["timestamp"]
            
            if "topic" in line["data"]: 
                topic = line["data"]["topic"]
            else: 
                topic = "no_topic"
            
            #VICOS
            if line["type"] != "DepartureDetected" and line["type"] != "ArrivalDetected" and line["type"] != "ApproachDetected":
                
                correlationId = line["context"]["$correlationId"]
                
                if topic == "vicos-common":
                    system = "VICOS"
                    if trigger != "OccupyReported":
                        payload = line["data"]["payload"]
                        payload = payload.split()
                        if "TTS" in payload[2] or "TAB" in payload[2]: 
                            traffic_central=payload[0]
                            trainnumber = payload[2]
                            trainnumber = trainnumber[4:9]
                            stationShort = payload[3][0:3]
                            
                            #calling getStationName to fetch full station name from it's short form
                            station = getStationName(stationShort)
                            
                            #We will use the short form if we could not find the station in the json lookup
                            if station == False:
                                station = stationShort

                            description = "Belagt"
                            trigger = "-"
                            track = "-" 
                            if len(payload) == 5:
                                sporfelt = payload[3]
                                sporfelt = sporfelt[3:len(sporfelt)] + payload[4]
                                description = "Signal stilt"
                                trigger = payload[3] + " " + payload[4]
                            signal = payload[2]
                            signal = (signal[9:13])
                    else: 
                        trainnumber = line["data"]["train"]
                        station = line["data"]["position"]["station"]
                        signal = line["data"]["position"]["name"]
                    
                    timestamp = converttime(timestamp, "kafka")
                    newline = {'time':timestamp,
                                   'trainnumber':trainnumber, 
                                   'station':station, 
                                   'track':track, 
                                   'signal':signal, 
                                   'system':system, 
                                   'trigger':trigger, 
                                   'description':description}
                    
                    if searchmatch(newline, searchfilter) == True:
                        filteredData.append(newline)

            
                #railmanager
                if topic == "railmanager-common":
                    #removing keep-alives
                    payload = line["data"]["payload"]
                    payload = payload.split()
                    trigger = payload[2]
                    system=payload[0]
                    if trigger == "D" or trigger == "E" or trigger =="F":
                        if len(payload) == 6: 
                            trainnumber = payload[5]
                            stationShort = payload[3][6:9]
                            signal = payload[4]
                        else: 
                            trainnumber = payload[4]
                            stationShort = payload[2][6:0]
                            signal = payload[3]
                        
                        #calling getStationName to fetch full station name from it's short form
                        station = getStationName(stationShort)

                        #We will use the short form if we could not find the station in the json lookup
                        if station == False:
                            station = stationShort

                        description = ""
                        track = "-" 
                        if trigger == "D":
                            description = "Stilt togvei"
                        if trigger == "E":
                            description = "Signal belagt"
                        if trigger == "F":
                            description = "Signal passert"
                    
                        timestamp = converttime(timestamp, "kafka")
                        
                        newline = {'time':timestamp,
                                   'trainnumber':trainnumber, 
                                   'station':station, 
                                   'track':track, 
                                   'signal':signal, 
                                   'system':system, 
                                   'trigger':trigger, 
                                   'description':description}
                    
                        if searchmatch(newline, searchfilter) == True:
                            filteredData.append(newline)


                #EBICOS
                if topic == "ebicos-common":
                    system = "EBICOS"
                    payload = line["data"]["payload"]
                    payload = payload.split()
                    trigger = payload[2][0:2]
                    #Only fetching trigger "FA", "EA" and "DA"
                    if trigger == "FA" or trigger == "EA" or trigger == "DA": 
                        signal = payload[2][11:14]
                        trainnumber = payload[2][(len(payload[2])-5):(len(payload[2]))]
                        stationShort = payload[2][8:11]
                        
                        #calling getStationName to fetch full station name from it's short form
                        station = getStationName(stationShort)

                        #We will use the short form if we could not find the station in the json lookup
                        if station == False:
                            station = stationShort

                        description = ""
                        track = "-" 

                        if trigger == "FA":
                            description = "Signal passert"
                        if trigger == "EA":
                            description = "Signal belagt"
                        if trigger == "DA":
                            description = "Stilt togvei"
                         
                        timestamp = converttime(timestamp, "kafka")
                        
                        newline = {'time':timestamp,
                                   'trainnumber':trainnumber, 
                                   'station':station, 
                                   'track':track, 
                                   'signal':signal, 
                                   'system':system, 
                                   'trigger':trigger, 
                                   'description':description}
                    
                        if searchmatch(newline, searchfilter) == True:
                            filteredData.append(newline)

                
                #KARI
                #KARI messages has no topic
                if topic == "no_topic": 
                    trigger = line["type"]
                    track = "-"
                    signal = "-"
                    
                    #Returning only "LeaveReported" and "OccupyReported"
                    if trigger == "ApproachTriggered" or trigger == "LeaveReported" or trigger == "OccupyReported" :
                        track = "-"
                        if trigger == "LeaveReported" or trigger == "OccupyReported" :
                            track = "-"
                            stationShort = line["data"]["position"]["station"]
                            signal = line["data"]["position"]["name"]
                    #Fetching Arrival, Depature and SetRoute
                    if trigger == "ArrivalTriggered" or trigger == "DepatrureTriggered" or trigger == "SetRouteTriggered":
                        if "track" in line["data"]:
                            track = line["data"]["track"]
                        else: 
                            track = "-"
                        stationShort = line["data"]["station"]

                    
                    #calling getStationName to fetch full station name from it's short form
                    station = getStationName(stationShort)

                    #We will use the short form if we could not find the station in the json lookup
                    if station == False:
                        station = stationShort


                    description = "-"
                    
                    #offsets will be added to description
                    if "offset" in line["data"]:
                        offset = line["data"]["offset"]
                        for key, value in offset.items():
                            description = f"{key}: {value}"


                    trainnumber = line["data"]["train"]
                    system = "KARI"
                    trigger = trigger.replace("Triggered", '')
                    trigger = trigger.replace("Reported", '')
                    
                    #Ensuring train numbers always have 5 digits by adding leading 0
                    
                    timestamp = converttime(timestamp, "kafka")
                    

                    trainnumber = make5digit(trainnumber)

                    newline = {'time':timestamp,
                               'trainnumber':trainnumber, 
                               'station':station, 
                               'track':track, 
                               'signal':signal, 
                               'system':system, 
                               'trigger':trigger, 
                               'description':description}
                    
                    if searchmatch(newline, searchfilter) == True:
                        filteredData.append(newline)

    return filteredData
            


def main(): 
    # Set up your timestamps
    date_start  = datetime(2024, 11, 8, 9, 0, 0) #year, month, day, hour, minute, seconds
    date_stop = datetime(2024, 11, 8, 9, 15, 0)
    #searchfilter = {'trainnumber':"2838", 'station':"Oslo", 'date_from': '2024-10-09 13:30:00', 'date_to': '2024-10-09 13:53:00'}
    searchfilter = {'trainnumber':"", 'station':"Oslo", 'date_from': '', 'date_to': ''}
    


    #Fetching messages from Kafka
    kafka_messages = "local json"
    #kafka_messages = GetKafkaMessages(date_start, date_stop)
    
    #A list to hold data from kafka
    messages = []
    
    #kafka did not return any data
    if not kafka_messages: 
        print("No data returned from Kafka")
    
    #We are testing on local data
    elif kafka_messages == "local json": 
        with open("sample_one_hour.json", "r") as kfk_messages:
            for line in kfk_messages:
                messages.append(json.loads(line))
        kfk_messages.close()
        
        #filter the data an make i readable for humans
        filteredData = filterKafkaMessages(messages, searchfilter)

        for line in filteredData:
            print ("{:<23} {:<9} {:<18} {:<6} {:<10} {:<18} {:<15} {:<15}".format
                   (line["time"],line["trainnumber"],line["station"],line["track"],line["signal"],line["system"],line["trigger"],line["description"]))


    #we are working on data fron kafka
    else: 
        for line in kafka_messages:
            messages.append(json.loads(line))

        #filter the data an make i readable for humans
        filteredData = filterKafkaMessages(messages, searchfilter)

        for line in filteredData:
            print ("{:<23} {:<9} {:<18} {:<6} {:<10} {:<18} {:<15} {:<15}".format(
                line["time"],line["trainnumber"],line["station"],line["track"],line["signal"],line["system"],line["trigger"],line["description"]))
    #       line = line.split()
    #        if len(line[2]) <=3 and line[2].isupper(): 
    #            print(line[2])

if __name__ == '__main__':
    main()
