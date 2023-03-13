


class MongoReturnStream:
    def __init__(self, id, title, isbn, pageCount, publishedDate, thumbnailUrl,
                 shortDescription, longDescription, status, authors, categories):
        self.id = id
        self.title = title
        self.isbn = isbn
        self.pageCount = pageCount
        self.date = eval(publishedDate)['$date'][0:10]
        self.thumbnailUrl = thumbnailUrl
        self.shortDescription = shortDescription
        self.longDescription = longDescription
        self.status = status
        self.authors = eval(authors)
        self.categories = eval(categories)

    def print_brief(self):
        print("{")
        print(self.id)
        print(self.title)
        print("}")

    def getid(self):
        return self.id

    def print_all(self):
        print("{")
        print(self.id)
        print("title: " + self.title)
        print("isbn: " + self.isbn)
        print(self.pageCount)
        print("date: " + self.date)
        print("url: " + self.thumbnailUrl)
        print("short info: " + self.shortDescription)
        print("long info: " + self.longDescription)
        print("status: " + self.status)
        print(self.authors)
        print(self.categories)
        print("}")

    def page_cond(self, upper, lower):
        if upper == -1:
            if lower == -1:
                return True
            else:
                return lower <= self.pageCount
        else:
            if lower == -1:
                return self.pageCount <= upper
            else:
                return lower <= self.pageCount <= upper

    def date_cond(self, upper, lower):  # format as "yyyy-mm-dd"
        if upper == "":
            if lower == "":
                return True
            else:
                if self.date is None:
                    return False
                else:
                    return lower <= self.date
        else:
            if self.date is None:
                return False
            else:
                if lower == "":
                    return self.date <= upper
                else:
                    return lower <= self.date <= upper

    def author_cond(self, author):
        if author == "":
            return True
        else:
            cond = False
            for i in self.authors:
                if i.lower() == author.lower():
                    cond = True
            return cond

    def status_cond(self, status):  # None -> 0 "PUBLISH"-> 1 "MEAP" -> 2 ALL -> 3
        if status == 1:
            return self.status == "PUBLISH"
        elif status == 2:
            return self.status == "MEAP"
        elif status == 3:
            return self.status == "PUBLISH" or self.status == "MEAP"
        else:
            return False

    def cat_cond(self, category): # Category as list
        if category == []:
            return True
        else:
            cond = False
            for i in self.categories:
                if category == i:
                    cond = True
            return cond

