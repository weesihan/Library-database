import mysql.connector
import hashlib


class Auth:
    def __init__(self):
        global auth_db
        global auth_cursor

        auth_db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="Wshsj2628",
            auth_plugin='mysql_native_password',
            database="Library"
        )

        auth_cursor = auth_db.cursor()

    # main methods
    def reg_user(self, new_user, new_password):
        try:
            auth_cursor.execute("INSERT INTO Library.User (userName, userPassword) VALUES (%s, %s);",
                                (new_user, self.encrypt_pwd(new_password)))
            auth_db.commit()
        except:
            auth_db.rollback()
            return 1

        try:
            auth_cursor.execute("SELECT userID FROM Library.User WHERE userName = \"" + new_user + "\"")
            a = auth_cursor.fetchall()
            if len(a) == 0:
                return 1
            userid = a[0][0]
            auth_cursor.execute("INSERT INTO Library.fine VALUES (0, {});".format(userid))
            auth_db.commit()
        except:
            auth_db.rollback()
            return 1
        return 0

    def reg_admin(self, new_admin, new_password):
        try:
            auth_cursor.execute("INSERT INTO Library.Admin (adminUsername, adminPassword) VALUES (%s, %s);",
                                (new_admin, self.encrypt_pwd(new_password)))
            auth_db.commit()
        except:
            auth_db.rollback()
            return 1
        return 0

    def login_user(self, login_username, login_password):
        input_login_query = "SELECT userPassword FROM Library.User WHERE userName = \"" + login_username + "\""

        try:
            auth_cursor.execute(input_login_query)
        except:
            auth_db.rollback()

        result = auth_cursor.fetchall()

        if len(result) != 0:
            if result[0][0] == self.encrypt_pwd(login_password):
                return 0
        return 1

    def login_admin(self, login_username, login_password):
        input_login_query = "SELECT adminPassword FROM Library.Admin WHERE adminUsername = \"" + login_username + "\""

        try:
            auth_cursor.execute(input_login_query)
        except:
            auth_db.rollback()

        result = auth_cursor.fetchall()

        if len(result) != 0:
            if result[0][0] == self.encrypt_pwd(login_password):
                return 0
        return 1

    def update_pwd_user(self, user, new_pwd):
        try:
            input_update_cmd = "UPDATE Library.User SET userPassword = \"" + self.encrypt_pwd(new_pwd) \
                               + "\" WHERE userName = \"" + user + "\""
            auth_cursor.execute(input_update_cmd)
            auth_db.commit()
        except:
            auth_db.rollback()
            return 1
        return 0

    def update_pwd_admin(self, user, new_pwd):
        try:
            input_update_cmd = "UPDATE Library.Admin SET adminPassword = \"" + self.encrypt_pwd(new_pwd) \
                               + "\" WHERE adminUsername = \"" + user + "\""
            auth_cursor.execute(input_update_cmd)
            auth_db.commit()
        except:
            auth_db.rollback()
            return 1
        return 0

    # supporting methods
    def check_exist_user(self, reg_input):
        input_reg_query = "SELECT userID FROM Library.User WHERE userName = \"" + reg_input + "\""
        auth_cursor.execute(input_reg_query)
        check_result = auth_cursor.fetchall()
        if len(check_result) != 0:
            return True
        else:
            return False

    def check_exist_admin(self, reg_input):
        input_reg_query = "SELECT adminID FROM Library.Admin WHERE adminUsername = \"" + reg_input + "\""
        auth_cursor.execute(input_reg_query)
        check_result = auth_cursor.fetchall()
        if len(check_result) != 0:
            return True
        else:
            return False

    def check_condition(self, pwd, min_length, max_length):
        return min_length <= len(pwd) <= max_length

    def encrypt_pwd(self, input_pwd):
        return hashlib.sha256(input_pwd.encode('utf-8')).hexdigest()

    def get_id_from_name_user(self, name):
        input_reg_query = "SELECT userID FROM Library.User WHERE userName = \"" + name + "\""
        auth_cursor.execute(input_reg_query)
        check_result = auth_cursor.fetchall()
        if len(check_result) != 0:
            return check_result[0][0]

    def get_name_from_id_user(self, id):
        input_reg_query = "SELECT userName FROM Library.User WHERE userID = \"" + id + "\""
        auth_cursor.execute(input_reg_query)
        check_result = auth_cursor.fetchall()
        if len(check_result) != 0:
            return check_result[0][0]

    def get_id_from_name_admin(self, name):
        input_reg_query = "SELECT adminID FROM Library.Admin WHERE adminUsername = \"" + name + "\""
        auth_cursor.execute(input_reg_query)
        check_result = auth_cursor.fetchall()
        if len(check_result) != 0:
            return check_result[0][0]

    def get_name_from_id_admin(self, id):
        input_reg_query = "SELECT adminUsername FROM Library.Admin WHERE adminID = \"" + id + "\""
        auth_cursor.execute(input_reg_query)
        check_result = auth_cursor.fetchall()
        if len(check_result) != 0:
            return check_result[0][0]
