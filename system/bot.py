'''
Created on Oct 28, 2017

@author: Auxilio
'''
import re
from time import sleep

from botFuncs import givePoints, getPoints, songRequest
import cfg
from utils import twitchConnect, log, startupThreads


CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

twitchSocket = twitchConnect()
startupThreads(twitchSocket)
log(message="AuxBot started successfully", idNum=0)

while True:
    response = twitchSocket.recv(1024).decode("utf-8")
    if response == "PING :tmi.twitch.tv\r\n":
        log(message="Received ping", idNum=1)
        twitchSocket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    else:
        username = re.search(r"\w+", response).group(0)
        message = CHAT_MSG.sub("", response)
        lowerCase = message.lower()
        parsedMessage = message.split()
        if parsedMessage[0][0] == '!':
            if parsedMessage[0] == "!givepoints":
                givePoints(parsedMessage[1], username, parsedMessage[2], twitchSocket)
            elif parsedMessage[0] == "!greglespebbles":
                getPoints(username=username, twitchSocket=twitchSocket)
            elif parsedMessage[0] == "!bangthatdrum" or parsedMessage[0] == "!sr":
                songRequest(username=username, twitchSocket=twitchSocket)
            elif parsedMessage[0] == "!command":
                if parsedMessage[1] == "add":
                    print("Add command")
#                     addCommand(twitchSocket, parsedMessage[2], ' '.join(parsedMessage[3:]), username=username)
            else:
                print("else")
#                 print(str(getCommands()))            
#                 if parsedMessage[0][1:] in getCommands():
#                     chat(sock=twitchSocket, msg=getCommand(parsedMessage[0][1:]))
    sleep(1 / cfg.RATE)
