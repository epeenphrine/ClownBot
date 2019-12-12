from discord.ext import commands
import discord
import random
import requests
import shutil
import pandas as pd
import urllib
import sqlite3
import time
import datetime
import config


client = commands.Bot(command_prefix="!")

'''this script needs to be run separately for reward system. This script also checks if user is present in balance table
in positions.db'''


'''api stuff ... token and etc'''
token = config.discord_api  #test bot
##token = config.discord_api1 #real bot

'''SQLite3 stuff'''
## sqlite3 prereq
conn = sqlite3.connect('positions.db') ## for stori:"ng in storage
##conn = sqlite3.connect(':memory:') ## for fresh database on every run. test run
c = conn.cursor()

'''the check function checks if user_id is present in the balance table in positions.db. If not it adds a user_id 
and gives them a starting balance of 10000. If already present, updates the database and updates 
cash row by adding randomly generated cash. It also performs a check on wage_cage and inserts the user_id if not present
 in wage_cage table'''

def check(user_id, cash):
    c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}") #selecting user_id that matches user_id
    info = c.fetchall() ## storing SQL query as info
    info2 = c.execute(f"SELECT user_id, wage_cage FROM wage_cage WHERE user_id = {user_id}").fetchall()
    print(datetime.datetime.now())
    print(info, info2) ## print to check our query
    if not info: ## if list is empty
        print(f"User not in database. Adding {user_id} to DB")
        with conn:
            entry = (user_id, 10000)
            c.execute(f"INSERT INTO balance VALUES {entry}") ## adding a new entry with user_id, cash
            conn.commit()
            print("added to cash")
        with conn:
            entry = (user_id, 0)
            c.execute(f"INSERT INTO wage_cage VALUES {entry}")
            conn.commit()
            print("added to wage_cage")
    elif not info2:
        with conn:
            entry = (user_id, 0)
            c.execute(f"INSERT INTO wage_cage VALUES {entry}")
            conn.commit()
            print("added to wage_cage")
    else: ##if list not empty
        c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}")
        new_balance = info[0][1] + cash
        print(f"new balance : {new_balance}")
        with conn:
            c.execute(f"UPDATE balance SET  cash = {new_balance} WHERE user_id = {user_id}")
            conn.commit()
'''checks for any messages in the server. cash is the reward system and it grabs a random amount
from 1 - 10 for every message typed. Then it runs check function'''
@client.event
async def on_message(message):
    user_id = message.author.id ##getting user_id from the author of message
    if user_id != 645017226415702016 or user_id != 644682603529764874: ##makes sure userid is not bot
        cash = list(range(1,10)) ## a list with numbers 1-10
        cash = random.choice(cash) ## grabs a random number from the list containg number1-10
        time.sleep(1)
        return check(user_id, cash) ## starts function check enters parameters user_id, cash
    else:
        return


client.run(token)
