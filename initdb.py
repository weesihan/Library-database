from model.auth import auth_model
from model.core import connect_mongo, connect_sql

# init User Admin accounts
auth_model.Auth().reg_admin("admin1", "123456")
auth_model.Auth().reg_admin("admin2", "000111")
auth_model.Auth().reg_admin("admin3", "012345")
auth_model.Auth().reg_user("testbot1", "999999")
auth_model.Auth().reg_user("testbot2", "456789")
auth_model.Auth().reg_user("testbot3", "233322")

print("--admin-- [--password--]")
print("admin1 [123456]")
print("admin2 [000111]")
print("admin3 [012345]")
print("--users-- [--password--]")
print("testbot1 [999999]")
print("testbot2 [456789]")
print("testbot3 [233322]")
print("DB for test session initialized")

# init SQL database by importing Mongo books
try:
    connect_mongo.MongoCore().mongo_sql_init()
except:
    pass

# init demo borrow reserve sessions
print("--books demo--")
t = connect_sql.SqlCore()
t.borrow(1, 1)
t.borrow(1, 2)
t.borrow(1, 3)
t.reserve(2, 1)
t.reserve(2, 2)
t.borrow(2, 4)
t.reserve(1, 4)
t.borrow(2, 5)
t.borrow(3, 6)
