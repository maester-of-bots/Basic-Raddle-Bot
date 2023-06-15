from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import pytz
from datetime import *
import requests
from selenium.webdriver.firefox.service import Service
from dotenv import load_dotenv
import os

utc = pytz.UTC

class SpaceJesus:
    def __init__(self, subs):
        """Class for the SpaceJesus Raddle bot.
        So far, he can...
            Crawl Raddle for new comments / posts
            Make a comment on a post, given a URL and comment text
            Submit an image given an image URL and a title
        I'm just figuring out functions currently, he doesn't do anything automatically yet.
        Also not sure what to make him do.  Also not sure how to make him do things automatically, safely"""

        # Subs can be a single, or multiple chained with plus signs, same as Praw
        # Make a URLs dict to keep track of those pesky URLs
        self.urls = {
            'posts': f"https://raddle.me/f/{subs}/new",
            'submit': f'https://raddle.me/submit/{subs}',
            'comments': f'https://raddle.me/f/{subs}/comments',
            'login': "http://www.raddle.me/login"
        }

    def make_driver(self):

        # Setting up the webdriver arguments to keep it from being displayed at all
        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")

        # Where the webdriver file is located
        ff_driver = "drive\\geckodriver"

        # Create a webdriver service object
        driver_service = Service(ff_driver)

        # Create the Firefox webdriver with the service object and options
        driver = webdriver.Firefox(service=driver_service, options=opts)
        return driver

    def login(self):
        """Login to Raddle with Selenium / Firefox"""

        # Load in credentials
        load_dotenv()
        raddle_user = os.getenv('raddle_username')
        raddle_password = os.getenv('raddle_password')

        # Pull the Raddle login page
        self.driver.get(self.urls['login'])

        # Find the input box for your username and pop it in there
        elem = self.driver.find_element(By.ID, "login-username")
        elem.clear()
        elem.send_keys(raddle_user)

        # Find the input box for your password and pop it in there
        elem = self.driver.find_element(By.ID, "login-password")
        elem.clear()
        elem.send_keys(raddle_password)

        # Hit enter and wait until the title is correct
        elem.send_keys(Keys.RETURN)
        wait = WebDriverWait(self.driver, 30)
        wait.until(EC.title_is("Raddle"))


    def get_new_comments(self):
        """Get new comments for the chosen sub"""

        # Log in
        self.driver = self.make_driver()
        self.login()

        # Gets the New comments page
        self.driver.get(self.urls['comments'])

        # Gets all new comments
        new_comments = self.driver.find_elements(By.CLASS_NAME, 'comment__main')

        # Empty dict to hold comments dicts
        comments = []

        # Iterate through comments and stick them in a list.
        # Why, not sure yet, probably working up to a stream function.
        for comment in new_comments:

            # Get comments timestamp
            ts = comment.find_element(By.TAG_NAME, "time").get_attribute('datetime')

            # Get commenter
            poster = comment.find_element(By.CLASS_NAME, 'fg-inherit').get_attribute('href')

            # Get comments text
            title = comment.find_element(By.CLASS_NAME, 'comment__body').text

            # Get the comments URL
            url = comment.find_element(By.CLASS_NAME, 'comment__permalink').get_attribute('href')

            commentDict = {
                "timestamp": ts,
                "user": poster,
                "title": title,
                "url": url,
            }
            comments.append(commentDict)

        return comments

    def get_new_posts(self):
        """ Get a list of new posts from the sub we're watching """
        self.driver = self.make_driver()
        self.login()

        # Gets the New posts page
        self.driver.get(self.urls['posts'])

        # Gets all new posts
        new_posts = self.driver.find_elements(By.CLASS_NAME, 'submission__inner')

        # Empty dict to hold post dicts
        posts = []

        for post in new_posts:

            # Get submission timestamp
            ts = post.find_element(By.CLASS_NAME, 'submission__timestamp').get_attribute('datetime')

            # Get poster
            poster = post.find_element(By.CLASS_NAME, 'submission__submitter').get_attribute('href')

            # Get post title
            title = post.find_element(By.CLASS_NAME, 'submission__link').text

            # Get the post URL
            url = post.find_element(By.CLASS_NAME, 'submission__nav').find_element(By.CLASS_NAME, 'text-sm').get_attribute('href')

            post = {
                "timestamp": ts,
                "user": poster,
                "title": title,
                "url": url,
            }
            posts.append(post)

        return posts

    def make_comment_id(self, url):
        """Quick and Dirty way to craft an element ID for a post"""

        # Split the URL into sections
        split_strings = url.split("/")

        # This function can be used for comments or submissions, figure out which
        if "-/comment/" in url:
            comment_id = url.split('-/comment/')[1]
            text = f'reply_to_comment_{comment_id}_comment'

        else:
            post_id = split_strings[-2]
            text = f'reply_to_submission_{post_id}_comment'

        return text

    def post_comment(self, URL, comment):
        """Post a comment, given the webdriver object, the comment link, and the text to send"""

        self.driver = self.make_driver()
        self.login()

        # Fetch the URL we're given
        self.driver.get(URL)

        # Craft the ID we need to find the comment text box
        id_to_check = self.make_comment_id(URL)

        # Find the comment text box
        elem = self.driver.find_element(By.ID, id_to_check)

        # Type in our nifty-ass comment.
        try:
            elem.send_keys(comment)
        except:
            reply = self.driver.find_element(By.CLASS_NAME, 'comment__reply-link')
            reply.click()
            elem.send_keys(comment)

        # Find the submit button.  Surprisingly the only button with the "button" class on the page.
        elem = self.driver.find_element(By.CLASS_NAME, "button")

        # Click that bitch
        elem.click()

    def download_image(self, image_url):
        """Downloads an image from a URL so bot can post images from URLs people give it"""

        # Local dir.  Will fix.
        subdir = 'C:\!Git\TGS-RABOT-SpaceJesus\\pics\\'

        # Grab the ext
        ext = image_url.split(".")[-1]
        if "/" in ext:
            ext = ext.replace("/","")

        # Name it something random that will probably not be overwritten.  Will fix.
        name = str(datetime.now().microsecond) + "." + ext

        # Grab the image
        data = requests.get(image_url)

        # Make a new path
        newpath = subdir+name

        # Write the image
        with open(newpath,'wb') as image:
            image.write(data.content)

        return newpath


    def post_image(self, image_url, title):
        """Post an image to the sub.  Probably used for automating posts for some degree of traffic while we're small.
        Or something."""
        # Log in
        self.driver = self.make_driver()
        self.login()

        # Download the provided image and get it's location
        img_path = self.download_image(image_url)

        # Get the submit page
        self.driver.get(self.urls['submit'])

        # Click the "Image" button
        elem = self.driver.find_elements(By.CLASS_NAME, "discreet-tab")
        IMAGE = elem[1]
        IMAGE.click()

        # Find the browse button and send the file.  The path was really bitchy about this one, needs work.
        browse_button = self.driver.find_element(By.ID, "submission_image")
        browse_button.send_keys(img_path)

        # Find the title box and set it
        title_box = self.driver.find_element(By.ID, "submission_title")
        title_box.send_keys(title)

        # Find the submit button and click it
        submit_button = self.driver.find_element(By.CLASS_NAME, "button")
        submit_button.click()

    def stream(self, sub, content_type):
        self.urls['comments']



