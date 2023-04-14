from app import makeconnection
from blockchain import Block, Blockchain

#custom exceptions for transaction errors
class InvalidTransactionException(Exception): pass
class InsufficientFundsException(Exception): pass

#what a mssql table looks like. Simplifies access to the database 'crypto'
class Table():
    def __init__(self, table_name, *args):
        self.table = table_name
        self.columns = "(%s)" %",".join(args)
        self.columnsList = args

        #if table does not already exist, create it.
        if isnewtable(table_name):
            create_data = ""
            for column in self.columnsList:
                create_data += "%s varchar(1000)," %column

            conn = makeconnection()
            cur = conn.cursor() #create the table
            cur.execute("CREATE TABLE %s(%s)" %(self.table, create_data[:len(create_data)-1]))
            conn.commit()
            cur.close()

    #get all the values from the table
    def getall(self):
        cur = makeconnection().cursor()
        result = cur.execute("SELECT * FROM %s" %self.table)
        data = cur.fetchall(); return data

    #get one value from the table based on a column's data
    #EXAMPLE using blockchain: ...getone("hash","00003f73gh93...")
    def getone(self, search, value):

        data = {}; cur = makeconnection().cursor()
        result = cur.execute("SELECT * FROM "+str(self.table)+ " WHERE "+ str(search)+ " = " + "'"+str(value)+ "'")
        data = cur.fetchone()
        cur.close(); return data

    #delete a value from the table based on column's data
    def deleteone(self, search, value):
        conn = makeconnection()
        cur =conn.cursor()
        cur.execute("DELETE from %s where %s = \"%s\"" %(self.table, search, value))
        conn.commit(); cur.close()

    #delete all values from the table.
    def deleteall(self):
        self.drop() #remove table and recreate
        self.__init__(self.table, *self.columnsList)

    #remove table from mssql
    def drop(self):
        conn = makeconnection()
        cur = conn.cursor()
        cur.execute("DROP TABLE %s" %self.table)
        conn.commit()
        cur.close()

    #insert values into the table
    def insert(self, *args):
        data = []
        for arg in args: #convert data into string mssql format
            data.append("'"+str(arg)+"'")

        data = ",".join(data)
        data = "(" + data +")"
        #print(data)
        conn = makeconnection()
        table_name = self.table
        #print(str(self.columns))
        cur = conn.cursor()
        cur.execute("INSERT INTO "+ table_name +str(self.columns)+" VALUES" + data)
        conn.commit()
        cur.close()

#execute mssql code from python
def sql_raw(execution):
    conn = makeconnection()
    cur = conn.cursor()
    
    cur.execute(execution)
    conn.commit()
    cur.close()

#check if table already exists
def isnewtable(tableName):

    cur = makeconnection().cursor()

    try: #attempt to get data from table
        result = cur.execute("SELECT * from %s" %tableName)
        cur.close()
    except:
        return True
    else:
        return False

#check if user already exists
def isnewuser(username):
    #access the users table and get all values from column "username"
    users = Table("users", "name", "email", "username", "password")
    data = users.getall()
    usernames = [user.get('username') for user in data]

    return False if username in usernames else True

#send money from one user to another
def send_money(sender, recipient, amount,text=None):
    #verify that the amount is an integer or floating value
    try: amount = float(amount)
    except ValueError:
        raise InvalidTransactionException("Invalid Transaction.")

    #verify that the user has enough money to send (exception if it is the BANK)
    if amount > get_balance(sender) and sender != "BANK" and sender!="MINING" :
        raise InsufficientFundsException("Insufficient Funds.")

    #verify that the user is not sending money to themselves or amount is less than or 0
    elif sender == recipient or amount <= 0.00:
        raise InvalidTransactionException("Invalid Transaction.")

    #verify that the recipient exists
    else:
        if sender!="MINING":
            if isnewuser(recipient):
                raise InvalidTransactionException("User Does Not Exist.")

    #update the blockchain and sync to mssql
    blockchain = get_blockchain()
    number = len(blockchain.chain) + 1
    data = "%s-->%s-->%s-->%s" %(sender, recipient, amount,text)
    blockchain.mine(Block(number, data=data))
    sync_blockchain(blockchain)

#get the balance of a user
def get_balance(username):
    balance = 0.00
    blockchain = get_blockchain()

    #loop through the blockchain and update balance
    for block in blockchain.chain:
        data = block.data.split("-->")
        if username == data[0]:
            balance -= float(data[2])
        elif username == data[1]:
            balance += float(data[2])
    return balance

#get the blockchain from mssql and convert to Blockchain object
def get_blockchain():
    blockchain = Blockchain()
    blockchain_sql = Table("blockchain", "number", "hash", "previous", "data", "nonce")
    for b in blockchain_sql.getall():
        blockchain.add(Block(int(b.get('number')), b.get('previous'), b.get('data'), int(b.get('nonce'))))
    return blockchain


#update blockchain in mssql table
def sync_blockchain(blockchain):
    blockchain_sql = Table("blockchain", "number", "hash", "previous", "data", "nonce")
    blockchain_sql.deleteall()

    for block in blockchain.chain:
        blockchain_sql.insert(str(block.number), block.hash(), block.previous_hash, block.data, block.nonce)
