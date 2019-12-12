from discord.ext import commands
import discord
import sqlite3
import re
import json
import stockpriceTDA
import time
import datetime
import asyncio
import sys
import os
import config
## bot connection info
client = commands.Bot(command_prefix="!") ## prefix for commands
token = config.discord_api #test bot
##token =  "NjQ0NjgyNjAzNTI5NzY0ODc0.Xc3m8A.0Tp19vSwj7GQB1kIIcKfSUcByqc" #real bot

## database stuff. Making connection and cursor
conn = sqlite3.connect("positions.db")

##conn = sqlite3.connect(':memory:') ## for fresh database on every run. Use this for testing
c = conn.cursor()

with open("admin.json") as f:
    admin = json.load(f)

'''
for testing without TDA api. You can set a int of your choice at whichever variable is used for TDA api
'''


''' Organized by Async and Non async functions. None async function starting here'''
'''
function for creating table. Checks if positions.db present and then checks if tables are present in db file.
If table not present creates a table. 
'''

def create_table():
    if os.path.isfile("positions.db"):
        query = c.execute(" SELECT name FROM  sqlite_master WHERE type = 'table' ").fetchall()
        print(query)
        if query:
            print("table exists skipping create_table")
        else:
            print("tables does not exist. create_table ran")
            c.execute("""CREATE TABLE positions(
                        user_id int, 
                        ticker text,
                        quantity integer,
                        total float,
                        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""")

            c.execute("""CREATE TABLE wage_cage(
                           user_id INT,
                           wage_cage INT  
                           )""")

            c.execute("""CREATE TABLE balance(
                           user_id INT, 
                           cash float
                           )""")
    else:
        print("no positions;.db")

'''when wage_cage is run updates wage_cage row of user to 0 and adds + 500 to their current cash in balance table'''

def wage_cage(user_id):
    with conn:
        c.execute(f"UPDATE wage_cage SET wage_cage = 0 WHERE user_id = {user_id}")
        conn.commit()
    with conn:
        current = c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}").fetchall()
        print(current)
        new = current[0][1] + 500
        c.execute(f"UPDATE balance SET cash = {new} WHERE user_id = {user_id}")

'''embed for returning information about user positions. It returns the ticker, quantity, the price they paid, portfolio total
current price of shares and PL. Does this by iterating tuples stored as a list in info and using TDA api to get current
price for all the stock tickers.  
'''

def embed_table(user_id):
    if type(user_id) == int:
        print(f"\n \nrunning emebd for user : {user_id}")
        info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERE user_id = {user_id}").fetchall()
        info2 = c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}").fetchall()
        print(info)
        if info:
            print("\n\niterating:")
            tickers = []
            quantity = []
            portfolio_value = 0
            for i in range(0, len(info)):
                print(info[i])
                tickers.append(info[i][1])
                quantity.append(info[i][2])
            tickers = ",".join(tickers)
            prices = stockpriceTDA.price_gets(tickers)
            print(f"tickers : {tickers}")
            print(f"quantity : {quantity}")
            print(f"price : {prices}")
            print(f"current balance : {info2[0][1]}")
            for i in range(0, len(quantity)):
                portfolio_value += round(float(quantity[i] * prices[i]), 2)
            print(f"new balance : {portfolio_value}")
            ticker = ""
            quantity = ""
            price = ""
            for i in range(0, len(info)):
                ticker += str(info[i][1]) + "\n"
                quantity += str(info[i][2]) + "\n"
                PL = round((prices[i] - info[i][3] / info[i][2]) / (info[i][3] / info[i][2]), 3) * 100
                price += "$" + str(round(info[i][3] / info[i][2], 2)) + "  |  " + "$" + str(
                    round(prices[i], 2)) + "  |  " + str(round(PL, 2)) + "%" + "\n"

            embed = discord.Embed(
                title=f"PORTFOLIO",
                description=f"Current Portfolio Value : {portfolio_value}",
                colour=discord.Colour.blue()
            )
            embed.set_footer(text='Used with live market data')
            embed.add_field(name="ticker", value=ticker, inline=True)
            embed.add_field(name="quantity", value=quantity, inline=True)
            embed.add_field(name="Average | Current | P/L %", value=price, inline=True)
            embed.add_field(name="P/L %", value="coming", inline=True)
            embed.add_field(name="Cash", value=f"{round(info2[0][1], 2)}", inline=True)
            return embed

'''wipes the target user_id's positions table and reset cash to 10,0000 in balance table'''
def WIPE(user2):
    print(f"\n \n{datetime.datetime.now()}")
    user_id = user2
    c.execute(f"SELECT user_id, ticker FROM positions where user_id={user_id}")
    info = c.fetchall()
    c.execute(f"SELECT user_id FROM balance where user_id = {user_id}")
    info2 = c.fetchall()
    print(info)
    print(info2)
    if not info2:
        print("user not in database")
    else:
        with conn:
            c.execute(f"DELETE FROM positions WHERE user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"UPDATE balance SET cash = 10000 WHERE user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"DELETE FROM wage_cage WHERE user_id = {user_id}")
            conn.commit()

'''this function liquidates by iterating through all current positions. Closes out every stock at current price'''

def liquidated(user_id):
    print(f"\n\n{datetime.datetime.now()}\nliquidate ran by {user_id}")
    info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERE user_id = {user_id}").fetchall()
    print(info)
    info2 = c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}").fetchall()
    print(info2)
    if not info:
        print("user not in database")
    else:
        print("\n\niterating:")
        tickers = []
        quantity = []
        new_balance = info2[0][1]
        for i in range(0, len(info)):
            print(info[i])
            tickers.append(info[i][1])
            quantity.append(info[i][2])
        tickers = ",".join(tickers)
        prices = stockpriceTDA.price_gets(tickers)
        print(f"tickers : {tickers}")
        print(f"quantity : {quantity}")
        print(f"price : {prices}")
        print(f"current balance : {info2[0][1]}")
        for i in range(0, len(quantity)):
            new_balance += round(float(quantity[i] * prices[i]), 2)
        print(f"new balance : {new_balance}")
        with conn:
            c.execute(f"DELETE FROM positions WHERE user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"UPDATE balance SET cash = {new_balance} where user_id = {user_id}")
            conn.commit()


'''buy function stores parameters in entry to insert into database, only if ticker is not present with user_id. 
this is checked by if not info. Otherwise updates the positions table instead. '''

def buy(user_id, ticker, quantity, total):
    stamp = str(datetime.datetime.now())
    entry = (user_id, ticker, quantity, total, stamp)
    print(f"\n \n {stamp}" 
          f"\nentry: {entry}")
    info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERE ticker = '{ticker}' AND user_id = {user_id}").fetchall()
    info2 = c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}").fetchall()
    if not info:
        with conn:
            print(f"ticker not in portfolio: {info}. \nAdding {ticker} to DB")
            c.execute(f"INSERT INTO positions VALUES {entry}")
            conn.commit()
        print(f"{info2}")
        cash = info2[0][1]
        print(f"balance: {cash}")
        new_balance = cash - float(total)
        print(f"new balance : {new_balance}")
        with conn:
            c.execute(f"UPDATE balance SET cash = {new_balance} WHERE user_id = {user_id}") ## cash update for user
            conn.commit()
        c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERE user_id = {user_id}")
        print(c.fetchall())
    else:
        print(info2)
        cash = info2[0][1]
        print(f"balance: {cash}")
        new_balance = cash - float(total)
        print(f"new balance : {new_balance}")
        new_quantity = info[0][2] + quantity
        new_total = info[0][3] + total
        with conn:
            c.execute(f"UPDATE balance SET cash = {new_balance} WHERE user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"UPDATE positions SET quantity = {new_quantity}, total = {new_total}, time = '{stamp}' WHERE ticker = '{ticker}' AND user_id={user_id}")
            conn.commit()

'''sell function takes in user_id, ticker, quantity, total parameter to query / update / delete rows in database'''
def sell(user_id, ticker, quantity, total):
    stamp = str(datetime.datetime.now())
    entry = (user_id, ticker, quantity, total, stamp)
    print(f"\n\n{stamp}"
          f"entry: {entry}")
    info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERe ticker = '{ticker}' and user_id = {user_id}").fetchall()  ## storing SQL query as info
    info2 = c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}").fetchall()  ##storing SQL query as info
    if info:
        print(info2)
        new_balance = info2[0][1] + float(total)
        print(f"new balance : {new_balance}")
        new_quantity = info[0][2] - quantity
        new_total = info[0][3] - total
        with conn:
            c.execute(f"UPDATE balance SET cash = {new_balance} WHERE user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"UPDATE positions SET quantity = {new_quantity}, total = {new_total}, time = '{stamp}' WHERE ticker = '{ticker}' AND user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"DELETE FROM positions WHERE ticker = '{ticker}' AND quantity <= 0 AND user_id={user_id}")
            conn.commit()

'''close function sells all position in a specific ticker at current price'''

def close(user_id, ticker, quantity, total):
    stamp = str(datetime.datetime.now())
    entry = (user_id, ticker, quantity, total)
    print(f"\n \n{stamp}"
          f"\nentry: {entry}")
    info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERe ticker = '{ticker}' AND user_id = {user_id}").fetchall()  ## storing SQL query as info
    info2 = c.execute(f"SELECT user_id, cash FROM balance WHERe user_id = {user_id}").fetchall()
    if info:  ## if tuple not empty. use c and conn here
        print(info2)  ## print to check our query
        new_balance = info2[0][1] + float(total)
        print(f"new balance : {new_balance}")
        print(f"{info}")
        new_quantity = int(info[0][2]) - int(quantity)
        print(f"new quantity: {new_quantity}")
        new_total = info[0][3] - total
        print(f"new total: {new_total}")
        with conn:
            c.execute(f"UPDATE balance SET cash = {new_balance} WHERE user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"UPDATE positions SET quantity = {new_quantity}, total = {new_total}, time = '{stamp}' WHERE ticker = '{ticker}' and user_id = {user_id}")
            conn.commit()
        with conn:
            c.execute(f"DELETE FROM positions WHERE ticker = '{ticker}' AND quantity <= 0")
            conn.commit()

'''if you want to work in pandas. The code is here. Just uncommnet it'''
##def dataframe(userid, ticker: to_upper, quantity, total, ctx, command):
##    df = pd.DataFrame(columns=['userid', 'ticker', 'quantity', 'total', 'date'])
##    df = df.append({"userid": userid,
##                    "ticker": ticker,
##                    "quantity": quantity,
##                    "total": total}, ignore_index=True)
##    print("entering")
##    print(df)
##    positions = pd.read_csv("positions.csv")
##    positions = positions.append(df, ignore_index=True)
##    print("saving")
##    print(positions)
##    positions.to_csv("positions.csv", index=False


'''starting here are the async functions that takes in commands from users'''
@client.event
async def on_ready():
    print("thoughts on clown world")
    print(client.user.name)
    print(client.user.id)


'''!stock commands for buying, selling, closing, liquidating, and yoloing.
    We first check the ban_list because I do not have some kind of timeout feature programmed in yet
    you may need to ban certain people that spam the bot so your API doesn't get revoked from TDA.
    
    When the bot sees !stock, the rest of the message that the user gives is split by space and is stored in a list.
    We use this to get additional parameter from users like ticker name of stock and quantity they wish to buy or sell
    
    the bot also queries the balance table and positions table to make sure user have the correct amount to continue with 
    their actions such as buy and sell 
    
    All stock prices are retrieved using TDA developer API and it is stored in the variable price. 
    If you don't want to use TDA api, you can change whatever you prefer at price variable. '''

@client.command()
async def stock(ctx, *argument):
    user_id = ctx.message.author.id
    with open("banlist.json") as f:
        ban_list = json.load(f)
    if user_id not in ban_list:
        print(f"user_id: {user_id}")
        cash = c.execute(f"SELECT user_id, cash FROM balance WHERE user_id = {user_id}").fetchall()
        cash = cash[0][1]
        print(f"current cash: {cash}")
        if argument:
            print("argument present")
            print(f"argument: {argument[0]}")
            if argument[0] == "buy":
                print(f"\n \n {datetime.datetime.now()}"
                      f"running buy")
                ticker = argument[2].upper()
                quantity = int(argument[1])
                print(f"quantity: {quantity}")
                price = float(stockpriceTDA.price_get(ticker))
                total = price * quantity
                print(f"ticker: {ticker}")
                print(f"total: {total}")
                if total < cash and quantity > 0 and cash >=0:
                    buy(user_id, ticker, quantity, total)
                    embed = embed_table(user_id)
                    await ctx.send(f"<@{user_id}> buying {quantity} {ticker} @ ${round(price, 2)} for ${round(total, 2)}")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"<@{user_id}> illegal: \nCASH: ${cash} \nTOTAL: ${total}")
            elif argument[0] == "sell":
                print(f"\n \n"
                      f"\nrunning sell")
                ticker = argument[2].upper()
                quantity = int(argument[1])
                print(f"quantity: {quantity}")
                price = float(stockpriceTDA.price_get(ticker))
                total = price * quantity
                print(f"stock: {ticker}")

                shares = c.execute(f"SELECT quantity FROM positions WHERE ticker = '{ticker}' and user_id = {user_id}").fetchall()
                if shares:
                    print(shares)
                    shares = shares[0][0]
                    print(shares)
                    if quantity <= shares and quantity > 0:
                        sell(user_id, ticker, quantity, total)
                        embed = embed_table(user_id)
                        await ctx.send(f"<@{user_id}> selling {quantity} {ticker} @ price ${round(price, 2)} for ${round(total, 2)}")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(f"<@{user_id}>not enough {ticker} for that sell order")
                else:
                    await ctx.send(f"<@{user_id}>not enough {ticker} for that sell order")

            elif argument[0] == "close":
                print(f"\n \n {datetime.datetime.now()} "
                      f"\n running close ")
                ticker = argument[1].upper()
                print(f"ticker: {ticker}")
                user_id = ctx.message.author.id
                info = c.execute(f"SELECT quantity FROM positions WHERE user_id = {user_id} AND ticker = '{ticker}'").fetchall()
                print(info)
                if info:
                    quantity = info[0][0]
                    print(f"quantity: {quantity}")
                    price = float(stockpriceTDA.price_get(ticker))
                    total = price * quantity
                    print(f"stock: {ticker}")
                    if quantity > 0:
                        close(user_id, ticker, quantity, total)
                        embed = embed_table(user_id)
                        await ctx.send(f"<@{user_id}> closing all position of {ticker} @ ${round(price, 2)} for ${round(total, 2)}")
                        await ctx.send(embed=embed)
                else:
                    await ctx.send(f"<@{user_id}>you don't own any {ticker}")
            elif argument[0] == "yolo":

                print("\n \n running yolo")
                ticker = argument[1].upper()
                print(ticker)
                user_id = ctx.message.author.id
                cash = c.execute(f"SELECT cash FROM balance WHERE user_id = {user_id}").fetchall()
                cash = round(float(cash[0][0]), 2)
                print(cash)
                price = float(stockpriceTDA.price_get(ticker))
                quantity = cash//price
                print(f"quantity: {quantity}")
                total = price * quantity
                print(f"stock: {ticker}")
                print(f"total: {total}")
                if quantity > 0:
                    buy(user_id, ticker, quantity, total)
                    embed = embed_table(user_id)
                    await ctx.send(f"<@{user_id}> yoloing remaining ${round(cash, 2)} on {quantity} {ticker} @ ${round(price, 2)} for ${round(total, 2)}")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"<@{user_id}> nothing to yolo with ${round(cash, 2)}")
        else:
            await ctx.send(f"not proper command? <@{user_id}>")
    else:
        await ctx.send("fuck you dumb ass")

'''!liquidate will close all positions in the positions table of the user_id
and sends a youtube video link. Starts liquidated function'''

@client.command()
async def liquidate(ctx):
    user_id = ctx.message.author.id
    info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERE user_id={user_id}").fetchall()
    if info:
        await ctx.send(f"<@{user_id}>\nhttps://www.youtube.com/watch?v=61Q6wWu5ziY \nBOGDONOFF ... DOMP EET")
        return liquidated(user_id)
    else:
        await ctx.send(f"<@{user_id}> nothing to domp ")

'''!positions will send embed table to user to give show their current positions'''
@client.command()
async def positions(ctx, *argument):
    user_id = ctx.message.author.id
    with open("banlist.json") as f:
        ban_list = json.load(f)
    if user_id not in ban_list:
        if argument:
            print(f"\n \n {datetime.datetime.now()}"
                  f"running !positions")
            print(argument)
            user = argument[0]
            user2 = re.findall(r"\d+", user)
            user2 = "".join(user2)
            print(user2)
            user2 = int(user2)
            if type(user2) == int:
                info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERE user_id = {user2}").fetchall()
                print(info)
                print(user)
                if info:
                    embed = embed_table(user2)
                    await ctx.send(f"<@{user2}> has : ")
                    await ctx.send(embed=embed)
                    print(f"\n\n{datetime.datetime.now()}\npositions ran")
                else:
                    await ctx.send(f"{user} has no positions")
        else:
            user_id = ctx.message.author.id
            info = c.execute(f"SELECT user_id, ticker, quantity, total FROM positions WHERE user_id = {user_id}").fetchall()
            if info:
                embed = embed_table(user_id)
                await ctx.send(f"<@{user_id}> you have : ")
                await ctx.send(embed=embed)
                print(f"\n\n{datetime.datetime.now()}\npositions ran")
            else:
                await ctx.send(f"<@{user_id}> has no positions")
    else:
        await ctx.send("fuck you dumb ass")

'''!wagecage first checks if wage_cage row value == 1 and starts the wage_cage function if true.
    Else sends message and picture'''

@client.command()
async def wagecage(ctx):
    print(f"\n\n{datetime.datetime.now()}\nrunning wage cage")
    user_id = ctx.message.author.id

    query = c.execute(f"SELECT user_id, wage_cage FROM wage_cage WHERE user_id == {user_id}").fetchall()
    print(f"query : {query[0][1]}")
    print(type(query[0][1]))
    if query[0][1] == 1:
        wage_cage(user_id)
        await ctx.send(f"<@{user_id}> good job wagie here's your $500")
    else:
        local_file = 'local_image.jpg'
        with open('image0.jpg', 'rb') as fp:
            await ctx.send(f"<@{user_id}> what are you doing?!\nget back to your cagie wagie!")
            await ctx.send(file=discord.File(fp, 'wage_cuck.jpg'))

'''this function runs infinitely every 5 second to update the wage_cage table.
    When time hits between 4:59:50 to 5:00:00. the wage_cage database should be updated
    to allow users to collect daily !wagecage reward'''

async def wagecagetimer():
    while True:
        ##sys.stdout.flush()  ##flush for troubleshooting
        time_now = datetime.datetime.now().time()
        time_reset = datetime.datetime.strptime("05:00:00", "%H:%M:%S").time()
        time_reset2 = datetime.datetime.strptime("04:59:50", "%H:%M:%S").time()
        if time_now > time_reset2 and time_now < time_reset:
            with conn:
                c.execute(f"UPDATE wage_cage SET wage_cage = 1")
                conn.commit()
            await asyncio.sleep(5)
        else:
            await asyncio.sleep(5)

'''!cash query balance table to return the amount of cash user have'''
@client.command()
async def cash(ctx):
    user_id = ctx.message.author.id
    with open("banlist.json") as f:
        ban_list = json.load(f)
    if user_id not in ban_list:
        print("\n \n running !cash")
        c.execute(f"SELECT user_id, cash FROM balance where user_id = {user_id} GROUP BY user_id")
        cash = c.fetchall()
        cash = cash[0][1]
        print(f"cash: {round(cash, 2)}")
        await ctx.send(f"your cash balance is: {round(cash, 2)}")
    else:
        await ctx.send(f"fuck you dumb ass")

'''returns embed for store .... not finished yet coming soon'''

@client.command()
async def store(ctx, *argument):
    user_id = ctx.message.author.id
    store1 = ["slaves", "strippers", "yacht", "mansion", "lambo"]
    price = [1000, 120, 1000000, 2000000, 500000]
    if argument:
        print(argument)
    else:
        print(f"\n\ndisplaying store")
        print("\n\niterating:")
        stores = ""
        prices = ""
        for i in range(0, len(store1)):
            stores += str(store1[i]) + "\n"
            prices += str(price[i]) + "\n"
        embed = discord.Embed(
            title=f"STORE",
            description=f"stuff",
            colour=discord.Colour.blue()
        )
        embed.add_field(name="items", value=stores, inline=True)
        embed.add_field(name="prices", value=prices, inline=True)
        await ctx.send(embed=embed)
        print(f"\n\n{datetime.datetime.now()}\npositions ran")




'''smite prevente targeted user from using stock commands and other commands'''
@client.command()
async def smite(ctx, *argument):
    user_id = ctx.message.author.id
    with open("banlist.json") as f:
        ban_list = json.load(f)
    if argument and user_id in admin:
        print("\n \n !smite ran ")
        print(argument)
        user = argument[0]
        user2 = re.findall(r"\d+", user)
        user2 = "".join(user2)
        print(user2)
        user2 = int(user2)
        if type(user2) == int and user2 not in ban_list:
            await ctx.send("adding to banlist")
            ban_list.append(user2)
            with open("banlist.json", "w") as f:
                json.dump(ban_list, f)
            print(ban_list)
        else:
            await ctx.send("user already in banlist")
    else:
        ctx.send("fuck you dumb ass")

'''wipe command. Wipe users if there is an issue. Makes sure something in argument and that user_id in admin'''
@client.command()
async def wipe(ctx, *argument):
    user_id = ctx.message.author.id
    if argument and user_id in admin:
        print("\n \n !wipe ran")
        print(argument)
        user = argument[0]
        user2 = re.findall(r"\d+", user)
        user2 = "".join(user2)
        print(user2)
        user2 = int(user2)
        if type(user2) == int:
            await ctx.send(f"wiping <@{user2}>")
            return WIPE(user2)


'''embed testing'''
@client.command()  ### EMBED TESTING
async def displayembeds(ctx):
    embed = discord.Embed(
        title= "POSITIONS",
        description = "This is your portfolio",
        colour = discord.Colour.blue()
    )
    embed.set_footer(text='this is a footer')
    embed.add_field(name='field name', value='field value', inline=False)
    embed.add_field(name='field name', value='field value', inline=True)
    embed.add_field(name='field name', value='field value', inline=True)

    await ctx.send(embed=embed)

'''iterates through database to iterate all users positions then gives speficic user positions'''

@client.command()
async def queryuser(ctx, *argument):
    user_id = ctx.message.author.id
    if argument:
        if user_id == 142160963368517632:
            print(f"\n\n{datetime.datetime.now()}\nrunning query")
            c.execute(f"SELECT * FROM positions")
            everything = c.fetchall()
            print("every users:")
            for i in range(0, len(everything)):
                print(everything[i])

            print("\n\n")
            print(f"specific users: {argument}")
            for i in range(0, len(argument)):
                c.execute(f"SELECT * FROM positions WHERE user_id = {int(argument[i])}")
                print(c.fetchall())


            print("query ended")
        else:
            print("query error")
    else:
        print("no argument")

create_table()
client.loop.create_task(wagecagetimer())
client.run(token)
