import mysql.connector
from datetime import date
from model.core import connect_mongo


class SqlCore:
    def __init__(self):
        global db
        global cursor

        db = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="Wshsj2628",
            auth_plugin='mysql_native_password',
            database="Library"
        )

        cursor = db.cursor()

    # New books
    def create_book(self, id, title, isbn):
        try:
            cursor.execute("INSERT INTO Library.Book (bookID, title, ISBN) VALUES({}, '{}', '{}');".format(id, title, isbn))
            db.commit()
        except:
            db.rollback()
            return 1
        return 0

    # 0 - success 1 - error

    # Availability, Borrow, Reserve, Lock Book Status
    def get_book_availability(self, book):  # input is bookID ###
        if self.is_borrowed(book) == 1:
            if self.is_reserved(book) == 1:
                return 2
            else:
                return 1
        elif self.is_locked(book) == 1:
            return 3
        return 0

    # 0 - free 1 - borrowed 2 - borrowed & reserved 3 - locked

    def is_locked(self, book):
        try:
            cursor.execute("SELECT status FROM Library.Book WHERE bookID = {}".format(book))
            result = cursor.fetchall()
            if len(result) != 0:
                if result[0][0] == 1:
                    return 1
        except:
            return 0
        return 0

    # 0 - false 1 - true

    def is_borrowed(self, book):
        try:
            cursor.execute("SELECT * FROM Library.Borrow WHERE bookID = {}".format(book))
            result = cursor.fetchall()
            if len(result) != 0:
                return 1
        except:
            return 0
        return 0

    # 0 - false 1 - true

    def is_reserved(self, book):
        try:
            cursor.execute("SELECT * FROM Library.Reserve WHERE bookID = {}".format(book))
            result = cursor.fetchall()
            if len(result) != 0:
                return 1
        except:
            return 0
        return 0

    # 0 - false 1 - true

    # Book Lock Management
    def lock(self, book):
        if self.get_book_availability(book) == 0:
            try:
                cursor.execute("UPDATE Library.Book SET status = 1 WHERE bookID = {}".format(book))
                db.commit()
            except:
                db.rollback()
                return 1
            return 0
        return 1

    # 0 - success 1 - error

    def unlock(self, book):
        if self.get_book_availability(book) == 3:
            try:
                cursor.execute("UPDATE Library.Book SET status = 0 WHERE bookID = {}".format(book))
                db.commit()
            except:
                db.rollback()
                return 1
            return 0
        return 1

    # 0 - success 1 - error

    # Borrow Book Management
    def borrow(self, user, book):  # input is userID and bookID
        if self.get_current_fines(user) > 0 or self.get_solidated_fines(user) > 0:
            print("User has overdue. Borrowing access denied")
            return 2
        if self.count_borrow(user) >= 4:
            print("User borrow limit exceeded")
            return 3

        if self.get_book_availability(book) == 0:
            try:
                cursor.execute(
                    "INSERT INTO Library.Borrow values({}, {}, CURDATE(), ADDDATE(CURDATE(), INTERVAL 4 WEEK))".format(
                        user, book))
                db.commit()
                print("user {} successfully borrows book {}".format(user, book))
                return 0
            except:
                print("Unable to borrow book")
                return 1
        print("Unable to borrow book")
        return 1

    # 0 - success 1 - error 2 - has overdue/fines 3 - max borrow exceeded

    def extend_borrow(self, user, book):  # four-week extension given no reservation by other users
        if self.get_current_fines(user) > 0 or self.get_solidated_fines(user) > 0:
            print("User has overdue. Borrowing access denied")
            return 1
        availability = self.get_book_availability(book)
        current_due_date = self.get_due_date(book)
        if availability == 1 and 0 <= (current_due_date.date() - date.today()).days <= 14:
            try:
                cursor.execute(
                    "UPDATE Library.Borrow SET dueDate = DATE_ADD(dueDate, INTERVAL 4 WEEK) WHERE bookID = {} AND borrowUserID = {}".
                        format(book, user))
                db.commit()
            except:
                return 1
            return 0
        else:
            return 1

    # 0 - success 1 - error

    def return_book(self, user, book):  # this function also makes sure that reserveUser borrows the book
        try:
            self.process_fines(user, book)
            cursor.execute("DELETE FROM Library.Borrow WHERE borrowUserID = {} AND bookID = {}".format(user, book))
            db.commit()
        except:
            db.rollback()
            return 1
        print("user {} returned book {}".format(user, book))
        try:
            cursor.execute("SELECT reserveUserID from Library.Reserve WHERE bookID = {}".format(book))
            reserveUser = cursor.fetchall()[0][0]
            if reserveUser is not None:
                self.cancel_reservation(reserveUser, book)
                self.borrow(reserveUser, book)
        except:
            return 2
        return 0

    # 0 - success 1 - return book error 2 - borrow again error

    # Reserve Book Functionality
    def reserve(self, user, book):  # cannot reserve book if the book is free
        if self.get_current_fines(user) > 0 or self.get_solidated_fines(user) > 0:
            print("User has overdue fines. Reserving access denied")
            return 1
        availability = self.get_book_availability(book)

        if availability == 1:
            try:
                cursor.execute("SELECT borrowUserID FROM Library.Borrow WHERE bookID = {}".format(book))
                result = cursor.fetchall()
                if result[0][0] == user:
                    print("Cannot reserve a book that you borrowed")
                    return 3
                cursor.execute("INSERT INTO Library.Reserve values({}, {}, CURDATE())".format(user, book))
                db.commit()
            except:
                db.rollback()
                return 2
            print("user {} reserves book {}".format(user, book))
            return 0
        else:
            return 2

    # 0 - success 1 - overdue blocked 2 - db error 3 - borrower try reserve

    def cancel_reservation(self, user, book):  # cancel reservation at any time
        try:
            cursor.execute(
                "DELETE FROM Library.Reserve WHERE reserveUserID = {} AND bookID = {}".format(
                    user, book))
            db.commit()
        except:
            db.rollback()
            return 1
        print("User {}'s reservation for book {} cancelled".format(user, book))
        return 0

    # 0 - success 1 - error

    # Entire view management for users
    def get_user_bookings(self, user):
        result = []
        result.extend(self.get_user_borrowings(user))
        result.extend(self.get_user_reservations(user))
        return result

    def get_user_borrowings(self, user):
        cursor.execute("SELECT * FROM Library.Borrow WHERE (borrowUserID = {})".format(user))
        borrowings = cursor.fetchall()
        return borrowings

    def get_user_reservations(self, user):
        cursor.execute("SELECT * FROM Library.Reserve WHERE (reserveUserID = {})".format(user))
        reservations = cursor.fetchall()
        return reservations

    def count_borrow(self, user):
        return len(self.get_user_borrowings(user))

    def count_reserve(self, user):
        return len(self.get_user_reservations(user))

    # admin all view
    def get_all_borrowings(self):  ##return all borrings in the form
        cursor.execute("SELECT * FROM Library.Borrow")
        result = cursor.fetchall()
        return result

    def get_all_reserves(self):
        cursor.execute("SELECT * FROM Library.Reserve")
        result = cursor.fetchall()
        return result

    def get_all_overdues(self):
        cursor.execute("SELECT * FROM Library.Borrow WHERE dueDate < CURDATE()")
        result = cursor.fetchall()
        return result

    def get_all_locked(self):
        cursor.execute("SELECT * FROM Library.Book WHERE status = 1")
        result = cursor.fetchall()
        return result

    # Due date, fine control
    def get_due_date(self, book):
        try:
            cursor.execute("SELECT bookID FROM Library.Borrow")
            result = list(map(lambda x: x[0], cursor.fetchall()))
            if book not in result:
                return None
            cursor.execute("SELECT dueDate FROM Library.Borrow WHERE {} = bookID".format(book))
            date = cursor.fetchall()[0][0]
            return date
        except:
            return None

        # return format: date / None

    # Current fines calculation
    def get_current_fines(self, user):
        output = 0
        try:
            cursor.execute("SELECT dueDate FROM Library.Borrow WHERE borrowUserID = {} AND dueDate < CURDATE()".format(user))
            result = cursor.fetchall()
            for i in result:
                val = (date.today() - i[0].date()).days
                output = output + val
            return output
        except:
            return output

    def process_fines(self, user, book):
        val = self.calculate_fines(user, book)
        if val != 0:
            self.update_solidated_fines(user, val)

    def calculate_fines(self, user, book):
        try:
            cursor.execute("SELECT dueDate FROM Library.Borrow WHERE borrowUserID = {} AND bookID = {}".format(user, book))
            result = cursor.fetchall()
            fines = (date.today() - result[0][0].date()).days
            if fines > 0:
                return fines
            else:
                return 0
        except:
            return 0


    def get_solidated_fines(self, user):
        try:
            cursor.execute("SELECT amount FROM Library.Fine WHERE userID = {}".format(user))
            currfines = cursor.fetchall()
        except:
            return 0
        if len(currfines) == 0:
            return 0;
        return currfines[0][0]

    def update_solidated_fines(self, user, amount):
        current = self.get_solidated_fines(user)
        updated = current + amount
        try:
            cursor.execute("UPDATE Library.Fine SET amount = {} WHERE userID = {}".format(updated, user))
            db.commit()
        except:
            db.rollback()
            return 1
        return 0

    def make_payment(self, user, amount):
        try:
            cursor.execute("INSERT INTO Library.Payment (`userID`, `amount`, `datetime`) VALUES ({}, {}, CURDATE())".format(user, amount))
            db.commit()
            cursor.execute("UPDATE Library.Fine SET amount = 0 WHERE userID = {}".format(user))
            db.commit()
        except:
            return 1
        return 0

    def get_user_overdue(self, user):  # returns list of books that are past due date i.e. dueDate < CURDATE()
        try:
            cursor.execute("SELECT * FROM Library.Borrow WHERE dueDate < CURDATE() AND borrowUserID = {}".format(user))
            result = cursor.fetchall()
            return result
        except:
            return None

    def get_borrower(self, book):  # return 0 for no borrower return id for borrower
        cursor.execute("SELECT borrowUserID FROM Library.Borrow WHERE bookID = {}".format(book))
        result = cursor.fetchall()
        if len(result) == 0:
            return 0
        if result[0][0] == None:
            return 0
        return result[0][0]

    def get_borrow_due(self, book):  # return 0 for no borrower return id for borrower
        try:
            cursor.execute("SELECT dueDate FROM Library.Borrow WHERE bookID = {}".format(book))
            result = cursor.fetchall()
            if len(result) == 0:
                return None
            if result[0][0] == None:
                return None
            return result[0][0].date()
        except:
            return None

    def get_reserver(self, book):  # return 0 if no reserver, return id for reserver
        cursor.execute("SELECT reserveUserID FROM Library.Reserve WHERE bookID = {}".format(book))
        result = cursor.fetchall()
        if len(result) == 0:
            return 0
        if result[0][0] == None:
            return 0
        return result[0][0]

    def get_user_status(self, user, book):
        if self.get_book_availability(book) == 3:
            return 5
        else:
            i = self.get_borrower(book)
            if i == 0:
                return 0
            elif i == user:
                return 3
            else:
                j = self.get_reserver(book)
                if j == 0:
                    return 1
                elif j == user:
                    return 4
                else:
                    return 2

    def get_all_books(self):  # return a list of unique book ids in the database
        cursor.execute("SELECT bookID FROM Library.Book")
        books = cursor.fetchall()
        if len(books) == 0:
            return "No book in library"
        output = []
        for i in books:
            output.append(i[0])
        return output

    def get_all_fines(self):
        cursor.execute("SELECT userID FROM Library.User")
        users = cursor.fetchall()
        output = []
        for i in users:
            curr = self.get_current_fines(i[0])
            solid = self.get_solidated_fines(i[0])
            if curr > 0 or solid > 0:
                output.append({'id': i[0], 'curr': curr, 'solid': solid})
        return output

    def format_returns_borrow(self, input):
        output = []
        for i in input:
            response = {'id': i[1], 'user': i[0], 'due': i[3].date(), 'title': connect_mongo.MongoCore().get_id(i[1]).title}
            output.append(response)
        return output

    def format_returns_reserve(self, input):
        output = []
        for i in input:
            response = {'id': i[1], 'user': i[0], 'title': connect_mongo.MongoCore().get_id(i[1]).title, 'due': self.get_borrow_due(i[1])}
            output.append(response)
        return output

    def format_return_locked(self, input):
        output = []
        for i in input:
            response = {'id': i[0], 'title': i[1]}
            output.append(response)
        return output
