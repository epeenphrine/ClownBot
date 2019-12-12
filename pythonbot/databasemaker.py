import sqlite3


## creating table

def create_positions():
    conn = sqlite3.connect('positions.db')  ## for storing in storage
    c = conn.cursor()
    c.execute("""CREATE TABLE positions (
                   user_id int,
                   ticker text,
                   quantity integer,
                   total float,
                   time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )""")

def create_cash():
    conn = sqlite3.connect('cash.db')  ## for fresh database on every run
    c = conn.cursor()
    c.execute("""CREATE TABLE balance(
                user_id int,
                cash float
                )""")

def create_smite():
    conn = sqlite3.connect('smite.db')  ## for fresh database on every run
    c = conn.cursor()
    c.execute("""CREATE TABLE smite(
                user_id int,
                status int    
                )""")

def create_portoflio():
    conn = sqlite3.connect("portfolio.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE (
                user_id int, 
                ticker text,
                quantity integer, 
                price_paid float, 
                average price float
                       
                )""")

def create_performance():
    conn = sqlite3.connect("performance.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE performance(
                user_id int,
                realized_pl float            
                """)
def alter_Table():
    conn = sqlite3.connect("positions.db")
    c = conn.cursor()
    c.execute("""ALTER TABLE POSITIONS ADD COLUMN time timestamp""")

def create_wage_cage():
    conn = sqlite3.connect("positions.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE wage_cage(
                user_id INT,
                wage_cage INT  
                )""")
    c.execute("""CREATE TABLE balance(
                user_id INT, 
                cash float
                """)
create_wage_cage()