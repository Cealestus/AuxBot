'''
Created on Mar 4, 2018

@author: meisl
'''
from utils import getUserPebbles, chat, userExists, addPebbles, subtractPebbles

def givePoints(numPebbles, givingUser, toUser, twitchSocket):
    try:
        numPebbles = int(numPebbles)
    except ValueError:
        chat(sock=twitchSocket, msg="Sorry, @" + givingUser + ", but I don't think that was a number.")
        return
    if getUserPebbles(givingUser) < numPebbles:
        chat(sock=twitchSocket, msg="Sorry, @" + givingUser + ", but you don't have enough pebbles to give.")
    elif not userExists(toUser):
        chat(sock=twitchSocket, msg="Sorry, @" + givingUser + ", but I can't find that user.")
    else:
        addPebbles(numPebbles, toUser)
        subtractPebbles(numPebbles, givingUser)
        chat(sock=twitchSocket, msg="@" + givingUser+ " gave @" + toUser + " " + str(numPebbles) + " pebbles!")