from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from deep_translator import GoogleTranslator
from deep_translator.exceptions import NotValidLength
import scrubadub
import requests
import json
import base64
import random
from time import sleep
import random
from datetime import datetime
from options import user, pw
from options import hashtagLinks as optionsLink
import csv

# for text anonymization
import re

firstNames = set(open("namesDatabase/first_names.all.txt").read().split())
lastNames = set(open("namesDatabase/last_names.all.txt").read().split())


class InstaScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("https://instagram.com")
        self.usernameDict = {}

    def anonymizeText(self, text):
        lst_text = text.split()
        for i in range(len(lst_text)):
            if (
                re.sub(r"[^\w\s]", "", lst_text[i].lower()) in firstNames
                or re.sub(r"[^\w\s]", "", lst_text[i].lower()) in lastNames
            ):
                lst_text[i] = "{{NAME}}"
            if lst_text[i].startswith("@"):
                lst_text[i] = "@{{USERNAME}}"
            if lst_text[i].startswith("https://") or lst_text[i].startswith("http://"):
                lst_text[i] = "{{LINK}}"
        joined = " ".join(lst_text)
        return joined

    def logIn(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@name="username"]'))
        )
        self.driver.find_element_by_xpath('//input[@name="username"]').send_keys(user)
        self.driver.find_element_by_xpath('//input[@name="password"]').send_keys(pw)
        self.driver.find_element_by_xpath('//button[@type="submit"]').click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sqdOP.yWX7d.y3zKF"))
        )
        self.driver.find_element_by_class_name("sqdOP.yWX7d.y3zKF").click()
        sleep(2)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "aOOlW.HoLwm"))
        )
        self.driver.find_element_by_class_name("aOOlW.HoLwm").click()

    def getPhotoInfo(self, url, hashtag, postID=0, comments=False):
        self.driver.get(url)
        print("getting photo ", postID, " information...")
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ltEKP"))
            )
        except TimeoutException:
            empty_obj = {
                "postID": "",
                "caption": "",
                "hashtag": "",
                "src": "",
                "username": "",
                "link": "",
                "userBio": "",
                "postLikes": "",
                "totalPosts": "",
                "totalFollowers": "",
                "totalFollowing": "",
                "engagement": "",
                "influencer": "",
                "followersCaptions": [],
            }
            return empty_obj
        sleep(6)
        contentFrame = self.driver.find_element_by_class_name("ltEKP")
        src = ""
        try:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "FFVAD"))
                )
            except TimeoutException:
                pass
            src = contentFrame.find_element_by_class_name("FFVAD").get_attribute(
                "src"
            )  # photo
        except NoSuchElementException:
            src = contentFrame.find_element_by_class_name("tWeCl").get_attribute(
                "src"
            )  # video
        username = self.driver.find_element_by_class_name(
            "sqdOP.yWX7d._8A5w5.ZIAjV"
        ).text
        encodedUsername = self.getID(username)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "C4VMK"))
        )

        caption = caption = self.driver.find_element_by_class_name("C4VMK span").text
        try:
            captionTranslated = GoogleTranslator(source="auto", target="en").translate(
                caption
            )
        except NotValidLength:
            captionTranslated = caption
        caption = self.anonymizeText(captionTranslated)
        # captionScrubadub = scrubadub.clean(captionTranslated)
        # predictions = self.getImageRecognition(url)
        try:
            postLikes = (
                (self.driver.find_element_by_class_name("Nm9Fw").text).split()
            )[0]
        except NoSuchElementException:
            try:
                sleep(2)
                self.driver.find_element_by_class_name("vcOH2").click()
                sleep(1)
                postLikes = (
                    (self.driver.find_element_by_class_name("vJRqr").text).split()
                )[0]
            except NoSuchElementException:
                postLikes = "0"
        postLikes = self.processStringNumber(postLikes)
        totalPosts, totalFollowers, totalFollowing = self.getProfileInfo(username)
        engagement = 1
        if totalFollowers != 0:
            engagement = ((totalPosts + postLikes) * totalFollowing) / (
                totalFollowers ** 2
            )
        userBio = self.getBioInstagram()
        influencer = False
        if engagement <= 0.2:
            influencer = True
        followersCaptions = []
        if comments == True:
            if influencer == True:
                if username in self.usernameDict:
                    followersCaptions = self.usernameDict[username]
                else:
                    randomFollowers = self.getLastNFollowers(username, 50)
                    print("getting followers instagram bio...")
                    for follower in randomFollowers:
                        sleep(random.randint(3, 5))
                        followersCaptions.append(self.getBioInstagram(follower))
                    self.usernameDict[username] = followersCaptions
        obj = {
            "postID": postID,
            "caption": caption,
            "hashtag": hashtag,
            "src": src,
            "username": username,
            "link": url,
            "userBio": userBio,
            "postLikes": postLikes,
            "totalPosts": totalPosts,
            "totalFollowers": totalFollowers,
            "totalFollowing": totalFollowing,
            "engagement": engagement,
            "influencer": influencer,
            "followersCaptions": followersCaptions,
        }

        return obj

    def processStringNumber(self, numString):
        num = numString
        num = num.replace(".", "")
        if "," in num:
            num = num.replace(",", "")
            num = num.replace("mm", "00000")
            num = num.replace("k", "00")
        else:
            num = num.replace("mm", "000000")
            num = num.replace("k", "000")
        return int(num)

    def getProfileInfo(self, username):
        self.driver.get("https://instagram.com/{}/".format(username))
        print("getting profile information...")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a/span',
                )
            )
        )
        totalPosts = (
            (
                self.driver.find_element_by_xpath(
                    '//*[@id="react-root"]/section/main/div/header/section/ul/li[1]/a/span'
                ).text
            ).split()
        )[0]
        totalFollowers = self.driver.find_element_by_xpath(
            '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a/span'
        ).get_attribute("title")
        if totalFollowers == "":
            totalFollowers = (
                (
                    self.driver.find_element_by_xpath(
                        '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a/span'
                    ).text
                ).split()
            )[0]
        totalFollowing = (
            (
                self.driver.find_element_by_xpath(
                    '//*[@id="react-root"]/section/main/div/header/section/ul/li[3]/a/span'
                ).text
            ).split()
        )[0]
        totalPosts = self.processStringNumber(totalPosts)
        totalFollowers = self.processStringNumber(totalFollowers)
        totalFollowing = self.processStringNumber(totalFollowing)
        return (totalPosts, totalFollowers, totalFollowing)

    def getLinksFromExplora(self, hashtag, total):
        print("getting ", total, "photos")
        self.driver.get("https://instagram.com/explore/tags/{}/".format(hashtag))
        allElements = []
        allLinks = set()
        while len(allLinks) < total:
            allElements = self.driver.find_elements_by_class_name("v1Nh3.kIKUG._bz0w")
            for item in allElements:
                allLinks.add(item.find_element_by_tag_name("a").get_attribute("href"))
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            sleep(3)
            print("length: " + str(len(allLinks)))

        totalLinks = list(allLinks)
        del totalLinks[total:]
        print("final final length: " + str(len(totalLinks)))
        return totalLinks

    def getHastagPhotos(self, hashtag, total, offset=0):
        start = datetime.now()
        # linkList = self.getLinksFromExplora(hashtag, total)
        linkList = optionsLink

        print("start time: ", start)
        fileName = (
            "data_" + hashtag + "_" + start.strftime("%Y-%m-%d_%H.%M.%S") + ".csv"
        )
        f = open(fileName, "w")
        headers = [
            "postID",
            "caption",
            "hashtag",
            "src",
            "username",
            "link",
            "userBio",
            "postLikes",
            "totalPosts",
            "totalFollowers",
            "totalFollowing",
            "engagement",
            "influencer",
            "followersCaptions",
        ]
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for i in range(len(linkList)):
            sleep(random.randint(3, 5))
            row = self.getPhotoInfo(linkList[i], hashtag, offset + i)
            writer.writerow(row)

        f.close()
        finish = datetime.now()
        print("finish time: ", finish)
        print("total time: ", finish - start)

    def getID(self, message):
        message_bytes = message.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode("ascii")
        return base64_message

    def getUsername(self, base64_message):
        base64_bytes = base64_message.encode("ascii")
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode("ascii")
        return message

    def getAllHashtags(self, hashtags, total):
        for item in hashtags:
            self.getHastagPhotos(item, total)

    def getImageRecognition(self, url):
        urlCooch = "https://api.chooch.ai/predict/image?url=https://s3.amazonaws.com/choochdashboard/base_site/ronaldo_suit.jpg&apikey=346g5717-1sd3-35h6-9104-b8h5c819dn19"
        response = requests.post(urlCooch)
        responseJSON = json.loads(response.content)
        predictionList = []
        for prediction in responseJSON["predictions"]:
            predictionList.append(prediction["class_title"])
        return predictionList

    def getLastNFollowers(self, username, N):
        print("getting ", N, " followers...")
        self.driver.get("https://instagram.com/{}/".format(username))
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//a[contains(@href,"/followers")]')
                )
            )
            self.driver.find_element_by_xpath(
                '//a[contains(@href,"/followers")]'
            ).click()
            sleep(random.randint(3, 5))
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "isgrP"))
            )
            scroll_box = self.driver.find_element_by_class_name("isgrP")
            # scroll_box = self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[2]')
            WebDriverWait(scroll_box, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "PZuss"))
            )
            lastHeight, height = 0, 1
            allUsernames = set()
            allElements = []
            while len(allUsernames) < N:
                sleep(4)
                followersLinks = scroll_box.find_elements_by_tag_name("a")
                for item in followersLinks:
                    if item.text != "":
                        allUsernames.add(item.text)
                self.driver.execute_script(
                    """
                    arguments[0].scrollTo(0, arguments[0].scrollHeight);
                    return arguments[0].scrollHeight;
                    """,
                    scroll_box,
                )
            followers = list(allUsernames)
            del followers[N:]
            print("returning ", len(followers), " follwers")
        except TimeoutException:
            print("private account")
            followers = []
        return followers

    def getRandomNFollowers(self, username, N):
        print("getting all followers...")
        self.driver.get("https://instagram.com/{}/".format(username))
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//a[contains(@href,"/followers")]')
            )
        )
        self.driver.find_element_by_xpath('//a[contains(@href,"/followers")]').click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "isgrP"))
        )
        scroll_box = self.driver.find_element_by_class_name("isgrP")
        # scroll_box = self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[2]')
        lastHeight, height = 0, 1
        while lastHeight != height:
            lastHeight = height
            sleep(4)
            height = self.driver.execute_script(
                """
                arguments[0].scrollTo(0, arguments[0].scrollHeight);
                return arguments[0].scrollHeight;
                """,
                scroll_box,
            )
            # print('last height: ', lastHeight, ' current height: ', height)
        print("getting a tag...")
        followersLinks = scroll_box.find_elements_by_tag_name("a")
        print("getting usernames...")
        followers = []
        for item in followersLinks:
            if item.text != "":
                followers.append(item.text)
        print("getting ", N, " random followers from ", len(followers), " followers...")
        return random.sample(followers, N if N < len(followers) else len(followers))

    def getBioInstagram(self, username=""):
        if username != "":
            self.driver.get("https://instagram.com/{}/".format(username))
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="react-root"]/section/main/div/header/section/div[2]/span',
                    )
                )
            )
            bio = self.driver.find_element_by_xpath(
                '//*[@id="react-root"]/section/main/div/header/section/div[2]/span'
            ).text
            try:
                bioTranslated = GoogleTranslator(source="auto", target="en").translate(
                    bio
                )
            except NotValidLength:  # if it is just an emoji, it will raise not valid length
                bioTranslated = bio
            bio = self.anonymizeText(bioTranslated)
        except TimeoutException:
            bio = ""
        return bio

    def getBioPicuki(self, username=""):
        if username != "":
            self.driver.get("https://www.picuki.com/profile/{}/".format(username))
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "profile-description"))
            )
            bio = self.driver.find_element_by_class_name("profile-description").text
            bio = GoogleTranslator(source="auto", target="en").translate(bio)
            bio = self.anonymizeText(bio)
        except TimeoutException:
            bio = ""
        return bio

    def getBioAPI(self, username):
        url = "https://www.instagram.com/{}/?__a=1".format(username)
        print(url)
        response = requests.get(url)
        print("HOLA")
        print(response)
        if response:
            responseJSON = json.loads(response.content)
            bio = responseJSON["graphql"]["user"]["biography"]
            if len(bio) != 0:
                bio = GoogleTranslator(source="auto", target="en").translate(bio)
                bio = self.anonymizeText(bio)
        else:
            bio = "EMTPTY RESPONSE"
        return bio


hashtags = ["fitspain", "realfooding", "realfood"]
bot = InstaScraper()
# bot.getHastagPhotos("fitspain", 5)
# bot.getAllHashtags(hashtags, 5)
# print(bot.getPhotoInfo("https://www.instagram.com/p/CF7s1ghDV3X/", "fitspain"))
# print(bot.getPhotoInfo("https://www.instagram.com/p/CF-ZH-mIlHn/", "fitspain")) # video case
# bot.driver.close()
