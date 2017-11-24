'''
Created on Oct 28, 2017

@author: Auxilio
'''
import re
from time import sleep

from cfg import cfg
from system.utils import chat, twitchConnect, log, startupThreads, addCommand, getCommands, getCommand


CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

twitchSocket = twitchConnect()
startupThreads()
log(message="AuxBot started successfully", idNum=0)

while True:
    print("Ready to receive commands")
    response = twitchSocket.recv(1024).decode("utf-8")
    if response == "PING :tmi.twitch.tv\r\n":
        log(message="Received ping", idNum=1)
        twitchSocket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    else:
        print("Received response: " + response)
        username = re.search(r"\w+", response).group(0)
        message = CHAT_MSG.sub("", response)
        print("sub'd message: " + message)
        parsedMessage = message.split()
        if parsedMessage[0] == "!command":
            if parsedMessage[1] == "add":
                addCommand(twitchSocket, parsedMessage[2], parsedMessage[3])
        else:
            print(str(getCommands()))            
            if parsedMessage[0] in getCommands():
                chat(sock=twitchSocket, msg=getCommand(parsedMessage[0]))
    sleep(1 / cfg.RATE)
