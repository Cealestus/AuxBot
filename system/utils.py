'''
Created on Nov 10, 2017

@author: Auxilio
'''

import json
from random import randint
import socket
from threading import Thread
from time import sleep

import psycopg2
import urllib3

import cfg


def chat(sock, msg):
    """
    Send a chat message to the server.
    Keyword arguments:
    sock -- the socket over which to send the message
    msg -- the message to be sent
    """
    sock.send("PRIVMSG {} :{}\r\n".format(cfg.CHAN, msg).encode('utf-8'))

def ban(sock, user):
    """
    Ban a user from the current channel.
    Keyword arguments:
    sock - the socket over which to send the ban command
    user - the user to be banned
    """
    chat(sock, ".ban {}".format(user))

def timeout(sock, user, secs=600):
    """
    Time out a user for a set period of time.
    Keyword arguments:
    sock -- the socket over which to send the timeout command
    user -- the user to be timed out
    secs -- the length of the timeout in seconds (Default 600)
    """
    chat(sock, ".timeout {}".format(user, secs))

def startupThreads(twitchSocket):
    """
    Starts the bot's threads for regular operation
    """
    thread_pullUsers = Thread(target=pullUsers)
    thread_pullUsers.start()

    thread_autoPebblerUpdater = Thread(target=autoPebblerUpdater)
    thread_autoPebblerUpdater.start()

    thread_rotatingMessages = Thread(target=chatRotatingMessages, args=(twitchSocket,))
    thread_rotatingMessages.start()

def twitchConnect():
    """
    Creates a socket connection to the twitch channel defined in cfg. returns the socket
    s -- The socket connecting to twitch. Needs to be closed after done using
    """
    s = socket.socket()
    s.connect((cfg.HOST, cfg.PORT))
    s.send("PASS {}\r\n".format(cfg.PASS).encode('utf-8'))
    s.send("NICK {}\r\n".format(cfg.NICK).encode('utf-8'))
    s.send("JOIN {}\r\n".format(cfg.CHAN).encode('utf-8'))
#     s.send("CAP REQ :twitch.tv/tags\r\n".encode('utf-8'))
    
    chat(s, "AuxBot joined chat\r\n")
    return s

def databaseConnect():
    """
    Create a connection to the database. Returns cursor, conn
    cursor -- The cursor used to run database transactions. Must be closed after done using
    conn -- The connection to the database. Must be closed after done using
    """
    try:
        conn = psycopg2.connect(database=cfg.DB_NAME, user=cfg.DB_USER, password=cfg.DB_PASS, host=cfg.DB_HOST)
        cursor = conn.cursor()
        return cursor, conn
    except:
        print("Unable to connect to database")
        quit

def log(message, idNum=None):
    """
    Add a log to the database for debugging purposes later
    id -- The ID of the error message, if defined (Optional)
    message -- The message to log to the database
    """
    cursor, conn = databaseConnect()
    if idNum is not None:
        cursor.execute("""INSERT INTO log VALUES (now(), '{}', '{}')""".format(idNum, message))
    else:
        cursor.execute("""INSERT INTO log VALUES (time, message) VALUES (now(), '{}')""".format(message))
    conn.commit()
    cursor.close()
    conn.close()

def addUser(username, userType):
    """
    Adds a user to the users table with the given username and userType
    username -- The name of the user to add
    userType -- The level of the user (viewer, mod, supermod, etc.)
    """
    cursor, conn = databaseConnect()
    SQL = "INSERT INTO users VALUES (%s, 0, 0, %s);"
    data = (username, userType)
    cursor.execute(SQL, data)
    conn.commit()
    cursor.close()
    conn.close()

def getUserType(username):
    """
    Gets the type of a user for permission purposes
    username -- The name of the user in question
    """
    try:
        cursor, conn = databaseConnect()
        SQL = "SELECT (usertype) FROM users WHERE username = %s;"
        data = (username,)
        cursor.execute(SQL, data)
        conn.commit()
        response = cursor.fetchone()
        cursor.close()
        conn.close()
        return response[0]
    except Exception as e:
        log(message="Problem encountered while user type from the database: " + str(e), idNum=9)
    

def autoPebblerUpdater():
    """
    Automatically updates every user in the database that's viewing the stream every 10 minutes
    """
    while True:
#         sleep(cfg.AUTO_UPDATE_INTERVAL)
        sleep(30)
        http = urllib3.PoolManager()
        streamWatchers = []
        try:
            req = http.request('GET', cfg.CHATTERS_URL)
            if req.status is not 200:
                log(message="Error connecting to twitch chatter service", idNum=3)
            else:
                response = json.loads(req.data)
                streamWatchers.extend(response["chatters"]["moderators"])
                streamWatchers.extend(response["chatters"]["staff"])
                streamWatchers.extend(response["chatters"]["admins"])
                streamWatchers.extend(response["chatters"]["global_mods"])
                streamWatchers.extend(response["chatters"]["viewers"])
                cursor, conn = databaseConnect()
                for watcher in streamWatchers:
                    if watcher != cfg.NICK:
                        SQL = "UPDATE users SET pebbles = pebbles + 5 WHERE username = %s;"
                        data = (watcher,)
                        cursor.execute(SQL, data)
                        print("Updated " + str(watcher) + "'s pebbles")
                conn.commit()
                cursor.close()
                conn.close()
                log(message="Completed auto updating pebbles", idNum=5)
        except Exception as e:
            log(message="Exception attempting to connect to twitch chatter service, " + str(e), idNum=4)

def getUserPebbles(username):
    """
    Get the number of pebbles a user has
    username -- The user to get pebbles of
    """
    cursor, conn = databaseConnect()
    cursor.execute("SELECT (pebbles) FROM users where username = '" + username + "';")
    pebbles = cursor.fetchone()
    cursor.close()
    conn.close()
    return pebbles[0]

def addPebbles(numPebbles, username=None):
    """
    Adds pebbles to a user
    username -- The user to add the pebbles to
    numPebbles -- The number of pebbles to add to the user
    """
    if numPebbles < 0:
        log(message="A request to add pebbles came in, but had negative pebbles", idNum=4)
    else:
        try:
            cursor, conn = databaseConnect()
            if username is not None:
                SQL = "UPDATE users SET pebbles = pebbles + %s WHERE username = %s;"
                data = (numPebbles, username)
                cursor.execute(SQL, data)
                conn.commit()
                cursor.close()
                conn.close()
    
            else:
                SQL = "UPDATE users SET pebbles = pebbles + %s"
                data = (numPebbles,)
                cursor.execute(SQL, data)
                conn.commit()
                cursor.close()
                conn.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

def subtractPebbles(numPebbles, username):
    """
    Removes pebbles from a user
    numPebbles -- The number of pebbles to remove from the user
    username -- The user to remove the pebbles from
    """
    if numPebbles < 0:
        log(message="A request to remove pebbles came in from " + username + ", but had negative pebbles", idNum=4)
    else:
        cursor, conn = databaseConnect()
        SQL = "UPDATE users SET pebbles = pebbles - %s WHERE username = %s;"
        data = (numPebbles, username)
        cursor.execute(SQL, data)
        conn.commit()
        cursor.close()
        conn.close()

def userExists(username):
    """
    Checks the database to see if a user exists
    username -- The user to check existence of
    """
    try:
        cursor, conn = databaseConnect()
        SQL = ("SELECT COUNT(*) FROM users WHERE username = %s")
        data = (username,)
        cursor.execute(SQL, data)
        count = cursor.fetchone()
        cursor.close()
        conn.close()
        return count[0] > 0
    except Exception as e:
        log(message="Problem encountered while checking if user exists in the database: " + str(e), idNum=8)

def pullUsers():
    """
    Pulls the currently watching users and adds them to the database if they aren't there
    """
    while True:
        http = urllib3.PoolManager()
        chattersMods = []
        chattersStaff = []
        chattersAdmins = []
        chattersGlobalMods = []
        chattersViewers = []
        parsedDbUsers = []
        
        try:
            req = http.request('GET', cfg.CHATTERS_URL)
            if req.status is not 200:
                log(message="Error connecting to twitch chatter service, status code is: " + str(req.status), idNum=3)
            else:
                response = json.loads(req.data)
                chattersMods.extend(response["chatters"]["moderators"])
                chattersStaff.extend(response["chatters"]["staff"])
                chattersAdmins.extend(response["chatters"]["admins"])
                chattersGlobalMods.extend(response["chatters"]["global_mods"])
                chattersViewers.extend(response["chatters"]["viewers"])
                
                cursor, conn = databaseConnect()
                cursor.execute("SELECT (username) FROM users;")
                dbUsers = cursor.fetchall()
                cursor.close()
                conn.close()
                
                for entry in dbUsers:
                    parsedDbUsers.extend(entry)
                
                for mod in chattersMods:
                    lowerCaseMod = mod.lower()
                    if lowerCaseMod not in parsedDbUsers and lowerCaseMod != cfg.NICK:
                        log(message="Adding user: " + lowerCaseMod + " to users db", idNum=2)
                        addUser(lowerCaseMod, "moderator")
                    else:
                        print("Found: " + lowerCaseMod + " in parsedDbUsers, so won't insert into database")
    
                for staff in chattersStaff:
                    lowerCaseStaff = staff.lower()
                    if lowerCaseStaff not in parsedDbUsers and lowerCaseStaff != cfg.NICK:
                        log(message="Adding user: " + lowerCaseStaff + " to users db", idNum=2)
                        addUser(lowerCaseStaff, "staff")
                    else:
                        print("Found: " + lowerCaseStaff + " in parsedDbUsers, so won't insert into database")
    
                for admin in chattersAdmins:
                    lowerCaseAdmin = admin.lower()
                    if lowerCaseAdmin not in parsedDbUsers and lowerCaseAdmin != cfg.NICK:
                        log(message="Adding user: " + lowerCaseAdmin + " to users db", idNum=2)
                        addUser(lowerCaseAdmin, "admin")
                    else:
                        print("Found: " + lowerCaseAdmin + " in parsedDbUsers, so won't insert into database")
    
                for globalMod in chattersGlobalMods:
                    lowerCaseGlobalMod = globalMod.lower()
                    if lowerCaseGlobalMod not in parsedDbUsers and lowerCaseGlobalMod != cfg.NICK:
                        log(message="Adding user: " + lowerCaseGlobalMod + " to users db", idNum=2)
                        addUser(lowerCaseGlobalMod, "globalmoderator")
                    else:
                        print("Found: " + lowerCaseGlobalMod + " in parsedDbUsers, so won't insert into database")
    
                for viewer in chattersViewers:
                    lowerCaseViewer = viewer.lower()
                    if lowerCaseViewer not in parsedDbUsers and lowerCaseViewer != cfg.NICK:
                        log(message="Adding user: " + lowerCaseViewer + " to users db", idNum=2)
                        addUser(lowerCaseViewer, "viewer")
                    else:
                        print("Found: " + lowerCaseViewer + " in parsedDbUsers, so won't insert into database")
    
        except Exception as e:
            log(message="Exception encountered while pulling users, " + str(e), idNum=6)
        sleep(60)

def chatRotatingMessages(twitchSocket):
    """
    Method to display a "helpful" message to the chat. Chats a predefined message from the database every preset amount of time
    twitchSocket -- The socket to send the messages over
    """
    while True:
        sleep(cfg.ROTATE_MSG_RATE)
        print("About to chat rotating messages")
        cursor, conn = databaseConnect()
        cursor.execute("SELECT max(id) FROM rotatingmessages;")
        maxId = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        selectedId = randint(1, maxId)
        
        cursor, conn = databaseConnect()
        SQL = "SELECT saying FROM rotatingmessages WHERE id = %s;"
        data = (selectedId,)
        cursor.execute(SQL, data)
        saying = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        chat(twitchSocket, str(saying))