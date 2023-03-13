ILS V1.0.1

BT2102 Assignment 1 By Group 31

Last updated: 6pm, 31 Mar 2021

Setup & Opening Instructions:

1 Start MySQL Server

2 change password for your localhost in model: auth/auth_model.py and core/connect_sql.py

3 run model/database/Library.sql in MySQL

4 import the model/database/libbooks.json in MongoDB

5 Open terminal, cd <Location>/ils

6 Paste and run the following commands in Terminal (make sure pwd==ils)

First Time Users *Do that to init a demo borrow reserve allocation.
```console
pip install mysql.connector
pip install Flask
Pip install Flask_session
source venv/bin/activate
python initdb.py 
python start.py
```

From Second Time Onwards
```console
source venv/bin/activate
python start.py
```

7 Web browser should autostart the login page.

8 The ip address should be http://127.0.0.1:8080/

9 Thank you! The ER diagram and presentation slides are directly in the main ils folder.
