'''
Created on Mar 4, 2018

@author: meisl
'''
from cfg import REQUEST_COST
from utils import getUserPebbles, chat, userExists, addPebbles, subtractPebbles,\
    userHasRequest, addSongRequest


def givePoints(numPebbles, givingUser, toUser, twitchSocket):
    """
    Transfers a number of pebbles from one user to another
    numPebbles -- The number of pebbles to transfer
    givingUser -- The user who is giving pebbles
    toUser -- The user receiving pebbles
    twitchSocket -- The socket connection to twitch
    """
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
        chat(sock=twitchSocket, msg="@" + givingUser + " gave @" + toUser + " " + str(numPebbles) + " pebbles!")

def getPoints(username, twitchSocket):
    """
    Reports the number of pebbles a user currently has
    username -- The user to get pebbles for
    twitchSocket -- The socket connection to twitch
    """
    chat(sock=twitchSocket, msg="@" + username + ", you have " + str(getUserPebbles(username)) + " pebbles")

def songRequest(username, url, twitchSocket, requestType=None):
    """
    Adds a song to the queue, user must have enough pebbles as determined in cfg
    username -- the user requesting a song
    twithcSocket -- The socket connection to twitch
    """
    numPebbles = getUserPebbles(username)
    if numPebbles < REQUEST_COST:
        chat(sock=twitchSocket, msg="@" + username + ", you need: " + str(REQUEST_COST) + ", but only have: " + str(numPebbles) + " pebbles.")
    else:
        if userHasRequest(username=username):
            chat(sock=twitchSocket, msg="Sorry, @" + username + ", you already have a song in the queue. Limit is 1")
        else:
            addSongRequest(username, url, requestType)
            subtractPebbles(numPebbles=REQUEST_COST, username=username)
        