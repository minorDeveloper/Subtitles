import socket
import json
from datetime import datetime, timedelta
import time

import websocket
import _thread
import rel


# Server IP
UDP_IP = "127.0.0.1"
UDP_PORT = 5180

subtitleActive = False
initialTimestamp = 0
subtitleFilename = ""

subtitleList = []

lastCue = None
lastStartTime = None

def timedelta_to_timestamp(timedelta):
        hrs, secs_remainder = divmod(timedelta.seconds, 3600)
        hrs += timedelta.days * 24
        mins, secs = divmod(secs_remainder, 60)
        msecs = timedelta.microseconds // 1000
        return "%02d:%02d:%02d,%03d" % (hrs, mins, secs, msecs)

class Subtitle(object):
    def __init__(self, index, start, end, content) -> None:
        self.index = index
        self.start = start
        self.end = end
        self.content = content

    def __lt__(self, other):
        return (self.start, self.end, self.index) < (other.start, other.end, other.index)
    
    def to_srt(self, eol="\n"):
        output_content = self.content

        if eol is None:
            eol = "\n"
        elif eol != "\n":
            output_content = output_content.replace("\n", eol)
        
        template = "{idx}{eol}{start} --> {end}{eol}{content}{eol}{eol}"

        return template.format(
            idx = self.index or 0,
            start = timedelta_to_timestamp(self.start),
            end = timedelta_to_timestamp(self.end),
            content = self.content,
            eol = eol,
        )

def stopSubtitle():
    global subtitleActive, lastCue, lastStartTime, initialTimestamp
    if not subtitleActive: return

    if lastCue != None:
        gma2Cue(lastCue, datetime.now())

    if len(subtitleList) == 0: return

    f = open(subtitleFilename, "w")

    for subtitle in subtitleList:
        f.write(subtitle.to_srt())

    subtitleActive = False

def startSubtitle(timestamp, filename):
    global subtitleActive, initialTimestamp, subtitleFilename
    if subtitleActive: stopSubtitle()

    initialTimestamp = timestamp
    subtitleFilename = filename

    subtitleActive = True

def gma2Cue(cue, timestamp):
    global initialTimestamp, lastCue, lastStartTime
    relativeTime = timestamp - initialTimestamp

    if subtitleActive == False: return

    if lastCue == None:
        lastCue = cue
        lastStartTime = relativeTime
        return
    
    if len(subtitleList) > 0:
        index = subtitleList[-1].index + 1
    else:  
        index = 0

    cueString = "LX: " + str(lastCue)
    
    subtitle = Subtitle(index, lastStartTime, relativeTime, cueString)
    subtitleList.append(subtitle)

    lastCue = cue
    lastStartTime = relativeTime

def convertTimestampString(timestampString):
    datetime_object = datetime.strptime(timestampString, 'Y-m-')
    return datetime_object

def handleMessage(data):
    jsonData = json.loads(data)

    command = jsonData['command']

    if command == "startSubtitle":
        timestamp = convertTimestampString(jsonData['timestamp'])
        filename = jsonData['filename']
        startSubtitle(timestamp, filename)

    elif command == "stopSubtitle":
        stopSubtitle()

    elif command == "gma2Cue":
        timestamp = convertTimestampString(jsonData['timestamp'])
        cue = jsonData['cue']
        gma2Cue(cue, timestamp)



def on_message(ws, message):
    print("Message: " + message)
    jsonData = json.loads(message)
    
def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://192.168.31.111:4445",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    
    print("I got to this line")
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
    print("There was a keyboard interrupt")




# now = datetime.now()
# print(now)
# jsonTestData = "{\"command\":\"startSubtitle\", \"timestamp\": \"" + str(now) +"\", \"filename\": \"test2.srt\"}"
# handleMessage(jsonTestData)


# time.sleep(1)
# now = datetime.now()
# #gma2Cue(2.5, now)
# jsonTestData = "{\"command\":\"gma2Cue\", \"timestamp\": \"" + str(now) +"\", \"cue\": \"2.5\"}"
# handleMessage(jsonTestData)

# time.sleep(3)
# now = datetime.now()
# #gma2Cue(8.2, now)
# jsonTestData = "{\"command\":\"gma2Cue\", \"timestamp\": \"" + str(now) +"\", \"cue\": \"8.2\"}"
# handleMessage(jsonTestData)

# time.sleep(3)
# now = datetime.now()
# #gma2Cue(17.25, now)
# jsonTestData = "{\"command\":\"gma2Cue\", \"timestamp\": \"" + str(now) +"\", \"cue\": \"17.25\"}"
# handleMessage(jsonTestData)

# time.sleep(2)
# now = datetime.now()

# #stopSubtitle()
# jsonTestData = "{\"command\":\"stopSubtitle\"}"
# handleMessage(jsonTestData)


#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#sock.bind((UDP_IP, UDP_PORT))

#while True:
#    data, addr = sock.recvfrom(1024)
#    handleMessage(data)
#    print ("received message: %s" & data)