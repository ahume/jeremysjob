import urllib
import urllib2
import datetime
import logging
import tweepy
from BeautifulSoup import BeautifulSoup
import HTMLParser

from models import JobTitle

from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.api import mail

from settings import *

def checkjob():

    try:
        # Get the clearleft jobs page
        response = urlfetch.fetch(CLEARLEFT_URL, headers = {'Cache-Control' : 'max-age=240'}, deadline=10)
    except:
        sendEmailToAdmin("Failed retreiving page from clearleft.com.")
        return False
        
    try:
        doc = BeautifulSoup(response.content)
        jeremy_node = doc.findAll("li", {"class": "col hcard"})[2]
        role_node = jeremy_node.find("p", {"class": "meta"})
        h = HTMLParser.HTMLParser()
        role = h.unescape(role_node.contents[0])
        #role = "A test"
    except:
        logging.info("Failed parsing HTML on /is/ page.")
        sendEmailToAdmin("Failed parsing HTML on /is/ page.")
        return False
    
    if not matchesPreviousJobTitle(role):

        logging.info("There is a new job title")
    
        job = JobTitle()
        job.title = role
        job.timestamp = datetime.datetime.now()
        
        try:
            sendJobTitleToTwitter(role)
            
            # If sent to Twitter successfully, then save to db.
            job.put()
            sendEmailToAdmin("Jeremy's job title has been updated")
        except tweepy.TweepError, e:
            logging.info(e.reason)
            sendEmailToAdmin("Failed sending message to Twitter. It should try again in 2 minutes though, because we didn't save the new job title.")
        
def matchesPreviousJobTitle(new_job_title):
    q = db.Query(JobTitle)
    q.order("-timestamp")
    results = q.fetch(1)
    
    if len(results) > 0:
        old_job_title = results[0].title
        logging.info("Comparing old and new job titles: '" + old_job_title + "' & '" + new_job_title)
        
        return results[0].title == new_job_title
        
    return False
    
def sendJobTitleToTwitter(job_title):
    logging.info("Sending to Twitter")
    
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    bot = tweepy.API(auth)
    
    # bot.update_status("Hello - I've been given a not particularly shiny upgrade. Hope Jeremy tests me soon!")
    
    bot.update_status("Jeremy has a new job title: %s" % job_title)
    
def sendEmailToAdmin(message):
    mail.send_mail(
        sender="Jeremy's Job <andyhume@gmail.com>",
        to="andyhume+jeremysjob@gmail.com",
        subject="Message from Jeremy's Job app",
        body=message
    )