from pymongo import MongoClient
from model.core import mongo_response_stream, connect_sql


class MongoCore:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        global collection
        db = client.local  # name of database is library
        collection = db.library  # collection 'books'

    # direct get methods
    def get_id(self, id):
        try:
            book = collection.find_one({"_id": id})  # book id is unique
            return self.to_stream(book)
        except:
            return None

    def get_isbn(self, isbn):
        if isbn == "None":
            return None
        else:
            try:
                book = collection.find_one({"isbn": isbn})  # book id is unique
                return self.to_stream(book)
            except:
                return None

    def isbn_to_id(self, isbn):
        if isbn == "None":
            return None
        else:
            try:
                book = collection.find_one({"isbn": str(isbn)})  # book id is unique
                return book.get('_id', None)
            except:
                return None

    def get_title(self, title):
        try:
            book = collection.find_one({"title": title})
            return True
        except:
            return False

    def create_book(self, ID, title, isbn, pageCount, publishedDate, url, longDesc, shortDesc, status, authors,
                    categories):
        if self.get_id(ID) is None:
            collection.insert_one(
                    {"_id": ID, "title": title, "isbn": isbn, "pageCount": pageCount, "publishedDate": publishedDate,
                     "thumbnailUrl": url, "longDescription": longDesc, "shortDescription": shortDesc,
                     "status": status, "authors": authors, "categories": categories})
            return 0
        return 1

    def simple_search(self, words):  # Input in List{str} format
        output = []
        idcheck = []
        for i in words:
            books = collection.find({"title": {"$regex": i, "$options": 'i'}})
            for j in books:
                if j["_id"] not in idcheck:
                    idcheck.append(j["_id"])
                    output.append(self.to_stream(j))
        output = sorted(output, key=lambda x: x.getid())
        return output

    def advanced_search(self, words, page_upper, page_lower, date_upper, date_lower, status_selected
                        , authors, categories):
        mid = []
        if words == "":  # No word input "" for filtering only
            input = collection.find()
            for i in input:
                mid.append(self.to_stream(i))
        else:
            mid = self.simple_search(words)

        output = []
        for k in mid:
            include = True
            if not k.page_cond(page_upper, page_lower):  # -1 set as default for no boundary
                include = False
            if not k.date_cond(date_upper, date_lower):  # -1 set as default for no boundary
                include = False
            if not k.author_cond(authors):  # "" set as default for no boundary
                include = False
            if not k.status_cond(status_selected):  # use checkboxes, 0 for no requirements
                include = False
            if not k.cat_cond(categories):  # "" set as default for no boundary
                include = False
            if include:
                output.append(k)
        return output

    def to_stream(self, book):
        id = book["_id"]
        title = book.get("title", "")
        isbn = book.get("isbn", "None")
        pageCount = book.get("pageCount", 0)
        publishedDate = book.get("publishedDate", "{'$date': '0000-00-00'}")
        if publishedDate == '':
            publishedDate = "{'$date': '0000-00-00'}"
        thumbnailUrl = book.get("thumbnailUrl", "")
        shortDescription = book.get("shortDescription", "")
        longDescription = book.get("longDescription", "")
        status = book.get("status", "")
        authors = book.get("authors", "[]")
        if authors == '':
            authors == "[]"
        categories = book.get("categories", "[]")
        if categories == '':
            categories == "[]"

        return mongo_response_stream.MongoReturnStream(id, title, isbn, pageCount, publishedDate, thumbnailUrl,
                                                       shortDescription,
                                                       longDescription, status, authors, categories)

    def mongo_sql_init(self):
        book = collection.find()
        sql = connect_sql.SqlCore()
        for i in book:
            sql.create_book(i["_id"], i["title"], i["isbn"])

    def mongo_search_return(self, listin):
        output = []
        s = connect_sql.SqlCore()
        for i in listin:
            authorlist = ', '.join(map(str, i.authors))
            val = s.get_book_availability(i.id)
            if val == (3 or 4):
                react = 3
            elif val == 2:
                react = 2
            elif val == 1:
                react = 1
            elif val == 0:
                react = 0
            book = {'id': i.id, 'title': i.title, 'imageurl': i.thumbnailUrl, 'authors': authorlist, 'status': react}
            output.append(book)
        return output
