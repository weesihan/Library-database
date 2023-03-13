from flask import Flask
from flask import redirect, request, render_template, jsonify, session, send_from_directory, url_for
from flask_session import Session
from functools import wraps
from model.auth import auth_model
from model.core import connect_sql, connect_mongo
import datetime
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
Session(app)


# Login Route Wrapper
def loginRequired(func):
    @wraps(func)
    def checkLogin(*args, **kwargs):
        user = session.get('username')
        # If cannot get user info from session
        if user is None or user == "":
            return redirect("/login/")
        return func(*args, **kwargs)

    return checkLogin


# User Route Wrapper
def userRequired(func):
    @wraps(func)
    def checkUser(*args, **kwargs):
        admin = session.get('admin')
        if admin == "True":
            return redirect('/admin/')
        return func(*args, **kwargs)

    return checkUser


# Admin Route Wrapper
def adminRequired(func):
    @wraps(func)
    def checkAdmin(*args, **kwargs):
        admin = session.get('admin')
        if admin is None or admin != "True":
            return "Forbidden! Not Authorized"
        return func(*args, **kwargs)

    return checkAdmin


# All users and admins enter site from here
@app.route('/')
def portal():
    return redirect('/login/')


# Private portal for developers only to see logs and error user status handling
@app.route('/root/', methods=('GET', 'POST'))
def root():
    if request.method == 'POST':
        if 'username' in session and session['username'] != "":
            session['username'] = ""
            return render_template('index.html', name="Please Login or Register",
                                   time=str(datetime.datetime.now().strftime("%B %d, %Y, %H:%M")))
        else:
            return jsonify({"code": 503, "message": "Not logged in"})

    if 'username' in session and session['username'] != "":
        return render_template('index.html', name=session['username'],
                               time=str(datetime.datetime.now().strftime("%B %d, %Y, %H:%M")))
    else:
        return render_template('index.html', name="Please Login or Register",
                               time=str(datetime.datetime.now().strftime("%B %d, %Y, %H:%M")))


# Auth Pages
@app.route('/login/', methods=('GET', 'POST'))
def login():
    auth = auth_model.Auth()
    granted = False
    if request.method == 'POST':
        login_username = request.form['username']
        login_password = request.form['password']

        if login_username is not None:
            val = auth.login_user(login_username, login_password)
            if val == 0:
                session['username'] = login_username
                session['password'] = login_password
                session['admin'] = "False"
                granted = True

        if not granted:
            return render_template('auth/login.html', error="Please check your username or password")

    if 'username' in session and session['username'] != "":
        id = auth_model.Auth().get_id_from_name_user(session['username'])
        session['userID'] = str(id)
        return redirect('/dashboard/')

    return render_template('auth/login.html')


# Auth Pages
@app.route('/adminlogin/', methods=('GET', 'POST'))
def admin_login():
    auth = auth_model.Auth()
    granted = False
    if request.method == 'POST':
        login_username = request.form['username']
        login_password = request.form['password']

        if login_username is not None:
            val = auth.login_admin(login_username, login_password)
            if val == 0:
                session['username'] = login_username
                session['password'] = login_password
                session['admin'] = "True"
                granted = True

        if not granted:
            return render_template('auth/admin_login.html', error="Please check your username or password")

    if 'username' in session and session['username'] != "":
        if 'admin' in session and session['admin'] == "True":
            id = auth_model.Auth().get_id_from_name_admin(session['username'])
            session['userID'] = str(id)
            return redirect('/admin/')

    return render_template('auth/admin_login.html')


@app.route('/register/', methods=('GET', 'POST'))
def register():
    auth = auth_model.Auth()
    error = None

    if request.method == 'POST':
        new_username = request.form["username"]
        new_password = request.form["password"]

        if new_username is not None:

            if not new_username:
                error = 'Username from 6 to 12 characters is required.'
            elif not new_password:
                error = 'Password from 6 to 15 characters is required.'
            elif not auth.check_condition(new_username, 6, 12):
                error = 'Username needs to be from 6 to 12 characters'
            elif not auth.check_condition(new_password, 6, 15):
                error = 'Password needs to be from 6 to 15 characters'
            elif auth.check_exist_user(new_username):
                error = 'Username {} is already registered.'.format(new_username)

            if error is None:
                t = auth.reg_user(new_username, new_password)
                if t == 1:
                    error = 'Connection error'

        if error is None:
            return render_template('auth/login.html', success="Register success!")
        else:
            return render_template('auth/register.html', error=error)

    if 'username' in session and session['username'] != "":
        return redirect('/login/')

    return render_template('auth/register.html')


# Main session pages
@app.route('/dashboard/', methods=('GET', 'POST'))
@loginRequired
@userRequired
def dashboard():
    sql = connect_sql.SqlCore()

    borrowedIn = sql.get_user_borrowings(session['userID'])
    borrowedNo = len(borrowedIn)
    borrowedList = sql.format_returns_borrow(borrowedIn)

    reservedIn = sql.get_user_reservations(session['userID'])
    reservedNo = len(reservedIn)
    reservedList = sql.format_returns_reserve(reservedIn)

    current_fines = sql.get_current_fines(eval(session['userID']))
    solidated_fines = sql.get_solidated_fines(eval(session['userID']))
    total_fines = current_fines + solidated_fines

    if request.method == 'POST':  # Pending
        t = request.form.to_dict()
        if t.get('extend', None) is not None:
            book_extend = eval(request.form['extend'])
            sql.extend_borrow(eval(session['userID']), book_extend)

        elif t.get('return', None) is not None:
            book_return = eval(request.form['return'])
            sql.return_book(eval(session['userID']), book_return)

        elif t.get('cancel', None) is not None:
            book_cancel = eval(request.form['cancel'])
            sql.cancel_reservation(eval(session['userID']), book_cancel)

        elif t.get('pay', None) is not None:
            if t.get('card-holder') != "" and t.get('card-number') != "" \
                    and t.get('month') != "" and t.get('year') != "" \
                    and t.get('cvv') != "":
                v = sql.make_payment(eval(session['userID']), solidated_fines)
                if v == 0:
                    return render_template('dashboard.html', session=session, borrowedNo=borrowedNo,
                                           borrowedList=borrowedList, reservedNo=reservedNo, reservedList=reservedList,
                                           fines=current_fines, current_fines=current_fines, solidated_fines=0,
                                           success="Payment Success!")
            return render_template('dashboard.html', session=session, borrowedNo=borrowedNo,
                                   borrowedList=borrowedList, reservedNo=reservedNo, reservedList=reservedList,
                                   fines=total_fines, current_fines=current_fines, solidated_fines=solidated_fines,
                                   error="Payment failed!")

        return redirect('/dashboard/')

    return render_template('dashboard.html', session=session, borrowedNo=borrowedNo,
                           borrowedList=borrowedList, reservedNo=reservedNo, reservedList=reservedList,
                           fines=total_fines, current_fines=current_fines, solidated_fines=solidated_fines)


@app.route('/search/', methods=['GET', 'POST'])
@loginRequired
def search():
    s = connect_sql.SqlCore()
    m = connect_mongo.MongoCore()

    if request.method == 'POST':  # Pending
        t = request.form.to_dict()

        if t.get('isbn_input', None) is not None:
            id = m.isbn_to_id(t['isbn_input'])
            print(id)
            return redirect(url_for('books', id=id))

        if t.get('simple_input', None) is not None:
            val = t['simple_input'].split()
            results = m.mongo_search_return(m.simple_search(val))
            return render_template('search.html', name=session['username'], results=results)

        if t.get('advanced_submit', None) is not None:
            if t.get('advanced_keyword', "") != "":
                advanced_keyword = t.get('advanced_keyword').split()
            else:
                advanced_keyword = ""

            if t.get('advanced_author', "") != "":
                advanced_author = t.get('advanced_keyword')
            else:
                advanced_author = ""

            if t.get('advanced_min_page', "") != "":
                advanced_min_page = int(t.get('advanced_min_page'))
            else:
                advanced_min_page = -1

            if t.get('advanced_max_page', "") != "":
                advanced_max_page = int(t.get('advanced_max_page'))
            else:
                advanced_max_page = -1

            if t.get('category', "---") != "---":
                cat = t.get('category')
            else:
                cat = []

            date_min = str(t.get('advanced_min_date', ""))
            date_max = str(t.get('advanced_max_date', ""))

            if t.get('published', False) is not False:
                if t.get('meap', False) is not False:
                    stat = 3
                else:
                    stat = 1
            elif t.get('meap', False) is not False:
                stat = 2
            else:
                stat = 0
        results = m.mongo_search_return(
            m.advanced_search(advanced_keyword, advanced_max_page, advanced_min_page, date_max, date_min, stat
                              , advanced_author, cat))
        return render_template('search.html', name=session['username'], results=results)

    return render_template('search.html', name=session['username'])


@app.route('/books/<id>/', methods=['GET', 'POST'])
@loginRequired
def books(id):
    s = connect_sql.SqlCore()
    m = connect_mongo.MongoCore()
    result = m.get_id(eval(id))
    duedate = s.get_borrow_due(id)

    if result is None:
        return redirect('/dashboard/')
    authors = ', '.join(map(str, result.authors))
    category = ', '.join(map(str, result.categories))
    date = result.date

    if str(date) == "0000-00-00":
        date = "Unknown"
    bookuserstatus = s.get_user_status(eval(session['userID']), id)

    if request.method == 'POST':
        t = request.form.to_dict()
        if t.get('borrow_action', None) is not None:
            v = s.borrow(eval(session['userID']), id)
            if v == 0:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=3, bookid=id, success="Book borrowed successfully!",
                                       duedate=duedate)
            else:
                if v == 2:
                    error = "Borrowing access denied due to unpaid fines."
                elif v == 3:
                    error = "Borrowing limit exceeded. Maximum four books."
                else:
                    error = "Unable to borrow book. Please try again."

                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus, bookid=id, error=error)

        elif t.get('reserve_action', None) is not None:
            v = s.reserve(eval(session['userID']), id)
            if v == 0:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=4, bookid=id, success="Book reserved successfully!",
                                       duedate=duedate)
            else:
                if v == 1:
                    error = "Reserving access denied due to unpaid fines."
                else:
                    error = "Unable to reserve book. Please try again."
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus, bookid=id, error=error, duedate=duedate)

        elif t.get('extend_action', None) is not None:
            v = s.extend_borrow(eval(session['userID']), eval(id))
            if v == 0:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus, bookid=id,
                                       success="Borrowing extended successfully!", duedate=duedate)

            else:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus, bookid=id,
                                       error="Not allowed to extend this borrowing!", duedate=duedate)

        elif t.get('return_action', None) is not None:
            bookuserstatus_update = 0
            if s.get_reserver(id) != 0:
                bookuserstatus_update = 1

            v = s.return_book(eval(session['userID']), id)

            if v == 0 or 2:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus_update, bookid=id,
                                       success="Returned book successfully!", duedate=duedate)

        elif t.get('cancel_action', None) is not None:
            v = s.cancel_reservation(eval(session['userID']), id)
            if v == 0:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=1, bookid=id,
                                       success="Cancelled reservation successfully!", duedate=duedate)

            else:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus, bookid=id,
                                       error="Error, please try again!", duedate=duedate)

        elif t.get('lock_action', None) is not None:
            v = s.lock(eval(id))
            if v == 0:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=5, bookid=id,
                                       success="Book locked successfully!", duedate=duedate)

            else:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus, bookid=id,
                                       error="Error, please try again!", duedate=duedate)

        elif t.get('unlock_action', None) is not None:
            v = s.unlock(eval(id))
            if v == 0:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=0, bookid=id,
                                       success="Book unlocked successfully!", duedate=duedate)

            else:
                return render_template('books.html', name=session['username'], title=result.title,
                                       shortinfo=result.shortDescription,
                                       imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn,
                                       pages=result.pageCount,
                                       date=date, longinfo=result.longDescription, status=result.status,
                                       category=category,
                                       bookuserstatus=bookuserstatus, bookid=id,
                                       error="Error, please try again!", duedate=duedate)

    return render_template('books.html', name=session['username'], title=result.title,
                           shortinfo=result.shortDescription,
                           imageurl=result.thumbnailUrl, authors=authors, isbn=result.isbn, pages=result.pageCount,
                           date=date, longinfo=result.longDescription, status=result.status, category=category,
                           bookuserstatus=bookuserstatus, bookid=id, duedate=duedate)


@app.route('/settings/', methods=['GET', 'POST'])
@loginRequired
def settings():
    a = auth_model.Auth()

    if request.method == 'POST':  # Pending
        t = request.form.to_dict()

        error = ""
        if t.get('current_password', None) is None or t.get('new_password', None) is None or t.get(
                'second_new_password', None) is None:
            error = "Please fill in password!"
        elif t.get('new_password') != t.get('second_new_password', None):
            error = "New password does not match!"
        elif t.get('current_password') != session['password']:
            error = "Current password does not match!"
        elif a.check_condition(t.get('new_password'), 6, 15) is False:
            error = 'Password needs to be from 6 to 15 characters'

        if error != "":
            return render_template('settings.html', error=error)

        if session['admin'] == "True":
            v = a.update_pwd_admin(session['username'], t.get('new_password'))
        else:
            v = a.update_pwd_user(session['username'], t.get('new_password'))

        if v == 0:
            session['password'] = t.get('new_password')
            return render_template('settings.html', success="Successfully changed password!")
        else:
            return render_template('settings.html', error="Error, please try again!")

    return render_template('settings.html')


@app.route('/admin/', methods=['GET', 'POST'])
@adminRequired
def admin():
    s = connect_sql.SqlCore()
    m = connect_mongo.MongoCore()
    a = auth_model.Auth()

    # All Borrowings List
    allBorrowedIn = s.get_all_borrowings()
    allBorrowedList = s.format_returns_borrow(allBorrowedIn)

    # All Reservation List
    allReservedIn = s.get_all_reserves()
    allReservedList = s.format_returns_reserve(allReservedIn)

    # All users with fines list
    allUserWithFines = s.get_all_fines()

    # addBook
    allLockedBooks = s.format_return_locked(s.get_all_locked())

    error = None

    if request.method == 'POST':
        t = request.form.to_dict()

        if t.get('extend_admin', None) is not None:
            s.extend_borrow(t['extend_user'], eval(t['extend_admin']))

        elif t.get('return_admin', None) is not None:
            s.return_book(t['return_user'], t['return_admin'])

        elif t.get('cancel_admin', None) is not None:
            s.cancel_reservation(t['cancel_user'], t['cancel_admin'])

        elif t.get('pay_admin', None) is not None:
            s.make_payment(t['pay_user'], t['pay_admin'])

        elif t.get('unlock_admin', None) is not None:
            v = s.unlock(eval(t.get('unlock_admin')))

        return redirect('/admin/')

    if 'admin' in session and session['admin'] == "True":
        return render_template('admin.html', name=session['username'], allBorrowedList=allBorrowedList,
                               allReservedList=allReservedList, allUserWithFines=allUserWithFines,
                               allLockedBooks=allLockedBooks)
    else:
        return "Forbidden! Not Authorized"


@app.route('/create/', methods=['GET', 'POST'])
@adminRequired
def create():
    s = connect_sql.SqlCore()
    m = connect_mongo.MongoCore()
    a = auth_model.Auth()

    if request.method == 'POST':  # Pending
        t = request.form.to_dict()

        if t.get('admin_name', None) is not None and t.get('admin_password', None) is not None:
            name = t.get('admin_name', None)
            pwd = t.get('admin_password', None)
            if name is None:
                error = "Admin name is required!"

            elif pwd is None:
                error = "Please input admin account password!"

            elif not a.check_condition(name, 6, 12):
                error = 'Admin name needs to be from 6 to 12 characters'

            elif not a.check_condition(pwd, 6, 15):
                error = 'Password needs to be from 6 to 15 characters'

            elif a.check_exist_admin(name):
                error = 'Admin name {} is already registered.'.format(name)

            else:
                val = a.reg_admin(name, pwd)
                if val == 0:
                    success = "Admin account {} successfully created!".format(name)
                    return render_template('create.html', success=success)
                else:
                    error = 'Please try again!'

            return render_template('create.html', error=error)

        elif t.get('id', None) is not None:
            if t.get('title', None) is None and t.get('status', None) is None and t.get('isbn', None) is not None:
                error = "Please fill in at least book title, ISBN and status!"

            elif t.get('status') != "PUBLISH" and t.get('status') != "MEAP":
                error = "Status needs to be PUBLISH or MEAP!"

            else:
                new_book_id = eval(t.get('id'))
                new_book_title = t.get('title')
                new_book_isbn = t.get('isbn')
                new_book_status = t.get('status')
                val_a = t.get('authors')
                if val_a == "":
                    new_book_authors = "[]"
                else:
                    val_c = []
                    val_b = val_a.split(",+")
                    for i in val_b:
                        val_d = ""
                        val_e = i.split("+")
                        for j in val_e:
                            val_d += j
                            val_d += " "
                        val_c.append(val_d)
                    new_book_authors = str(val_c)

                if t.get('pageCount', "") == "":
                    new_book_pages = 0
                else:
                    new_book_pages = int(t.get('pageCount'))
                    
                val_f = t.get('publishedDate', "")
                if val_f == "":
                    new_book_date = ""
                else:
                    new_book_date = "{'$date': '" + val_f + "T00:00:00.000-0700'}"

                new_book_url = t.get('thumbnailUrl', "")
                new_book_short = t.get('shortDescription', "")
                new_book_long = t.get('longDescription', "")
                val_g = t.get('categories', "")

                if val_g == "":
                    new_book_categories = "[]"
                else:
                    new_book_categories = str(val_g.split(",+"))

                t = m.create_book(new_book_id, new_book_title, new_book_isbn, new_book_pages, new_book_date,
                                  new_book_url,
                                  new_book_long, new_book_short, new_book_status, new_book_authors, new_book_categories)

                if t == 0:
                    v = s.create_book(new_book_id, new_book_title, new_book_isbn)
                    if v == 0:
                        direct = '/books/' + str(new_book_id) + '/'
                        return redirect(direct)
                    else:
                        error = "Server Error!"
                else:
                    error = "Server Error!"

            return render_template('create.html', error=error)

    return render_template('create.html')


# Logout redirect page
@app.route('/logout/')
@loginRequired
def logout():
    session['username'] = ""
    session['userID'] = ""
    session['password'] = ""
    session['admin'] = "False"
    return redirect('/login/')


# Forced Refresh page for operations
@app.route('/refresh/')
@loginRequired
def refresh():
    return redirect('/dashboard/')


@app.route('/favicon.ico')
def favicon_ico():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


# 404 Not Found redirect to dashboard / login page
@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return redirect('/dashboard/')


# To start the server and the application at http://127.0.0.1:8080/
def start():
    app.run(host='127.0.0.1', port=8080, debug=True)
