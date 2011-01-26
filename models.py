from google.appengine.ext import db

class JobTitle(db.Model):
    title = db.StringProperty()
    timestamp = db.DateTimeProperty()