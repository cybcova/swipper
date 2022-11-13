from ctypes.wintypes import PINT
import logging  
import requests
import random
import json
import re 
import os

from time import sleep
from datetime import datetime

#Locales
from pymongo_get_database import get_database

dbname = get_database()

if not os.path.exists('./logs'):
  os.makedirs('./logs')

logging.basicConfig(filename= "./logs/" + re.sub("\D", "", str(datetime.today())[:19]) + ".log", 
					format='%(asctime)s %(message)s', 
					filemode='w')
logger=logging.getLogger() 
logger.setLevel(logging.INFO)

def printNlog(str):
  print(str)
  logger.info(str) 

def getRecs():
  urlRecs = "https://api.gotinder.com/v2/recs/core?locale=es-ES"
  responseRecs = requests.get(urlRecs, headers=headersRecs)
  if( responseRecs.status_code != 200 ): raise Exception("Error getRecs: " + str(responseRecs))
  return responseRecs.json()

def chooseAPhotoIdRandomly(photos):
  lenPhotos = len(photos)
  randomPhoto = random.randint(0, lenPhotos-1)
  return(photos[randomPhoto]["id"])

def likePassRequest(url, headersJson, body, oldUser):
  if(oldUser):
      dbname["requests"].delete_one({"_id": user["_id"]})
      dbname["responses"].delete_one({"_id": user["_id"]})

  dbname["requests"].insert_one({"_id":user["_id"], "request" : {"url":url, "data":json.dumps(body), "headers":headersJson}})
  response = requests.post(url, data=json.dumps(body), headers=headersJson) if body else requests.get(url, headers=headersJson)
  if( response.status_code != 200 ): raise Exception("Error response codigo: " + response.status_code)
  dbname["responses"].insert_one({"_id":user["_id"], "response" : response.json()})
  return response

###Empezamos

headersRecs = json.load(open('./headers/recs.json'));
headersLike = json.load(open('./headers/like.json'));
headersPass = json.load(open('./headers/pass.json'));

bannedPatternsForShortBio="\W?(instagram)\W|\W?(onlyfans)\W|\W?(ig)\W|\W?(of)\W|\W?(sigueme)\W|\W?(follow me)\W|\W?(@)\w+"
bannedPatterns="\W?(sd)\W|\W?(sb)\W|\W?(tv)\W|\W?(trans)\W|\W?(tranny)\W|\W?(travesti)\W|\W?(transexual)\W|(⚧️)|(🏳️‍⚧️)"

recsJson = getRecs() #TODO
#recsJson = json.load(open('./ejmploRecs.json'))

if "results" not in recsJson["data"]: raise Exception("No girls around")

processedProfiles = 0
totalLikes = 0
totalpasses = 0
while len(recsJson["data"]["results"]) > 0 :
  for singleResult in recsJson["data"]["results"]:
    
    user = singleResult["user"]
    printNlog("\n*:._.:*~*:._.:* " + user["name"] + " *:._.:*~*:._.:*\n")
    printNlog("id: " + user["_id"])
    printNlog("bio: " + (user["bio"][:27] + "...") if len(user["bio"])>=30 else user["bio"])
    printNlog("distance: " + str(singleResult["distance_mi"] * 1.60934) + " km")
    
    oldUser = dbname["users"].find_one({"user._id":user["_id"]})
    if(oldUser):
      printNlog("USUARIO REPETIDO!")
      printNlog("pausado....")
      #input()
    else:
      dbname["users"].insert_one(singleResult)
    
    finalSwipe = {}
    finalSwipe["_id"] = user["_id"]

    reasonIPass=""

    if(len(user["bio"])==0): 
      reasonIPass += "No bio "
    elif(len(user["bio"])<15 and re.search(bannedPatternsForShortBio, user["bio"].lower())):
      reasonIPass += "Just looking for Followers "
    elif(re.search(bannedPatterns, user["bio"].lower())):
      reasonIPass += "Not interested because of Bio "

    if(singleResult["distance_mi"]>9):
      reasonIPass += "Too Far "

    finalSwipe["like"] = True if reasonIPass=="" else False

    if(reasonIPass==""):
      urlLike = "https://api.gotinder.com/like/"+ user["_id"] +"?locale=es-ES"
      idPhotoChoosen=chooseAPhotoIdRandomly(user["photos"]);
      bodyLike = {
          "s_number": singleResult["s_number"],
          "liked_content_id": idPhotoChoosen,
          "liked_content_type": "photo"
      }
      response = likePassRequest(urlLike, headersLike, bodyLike, oldUser)
      match = response.json()["match"];
      finalSwipe["match"] = match
      if match : printNlog("It was a Match!!")
      totalLikes += 1

    else:
      urlPass = "https://api.gotinder.com/pass/" + user["_id"] + "?locale=es-ES&s_number=" + str(singleResult["s_number"])
      likePassRequest(urlPass, headersPass, None, oldUser)
      finalSwipe["reasonIPass"] = reasonIPass
      totalpasses += 1

    printNlog("Did I like: " +  ("Yes" if reasonIPass=="" else "No"))
    if reasonIPass!="": printNlog("Reason :" + reasonIPass)

    finalSwipe["registration_date"] = datetime.today()
    
    if(oldUser):
      dbname["swipes"].delete_one({"_id": user["_id"]})
      
    dbname["swipes"].insert_one(finalSwipe)

    processedProfiles +=1

    #Let's wait some time so tinder doesn't think im a bot
    breakTime = round(random.uniform(2.5, 7), 3); #TODO
    printNlog("Swipes: " + str(totalLikes) + " likes " + str(totalpasses) + " passes " + str(processedProfiles) + " profiles swipped in total")
    printNlog("Continue in: " + str(breakTime))
    sleep(breakTime)
  
  if(processedProfiles >=550):
    printNlog("\nEnough profiles processed")
    break

  recsJson = getRecs() #TODO
  if("results" not in recsJson["data"]):
    printNlog("\nNot more Girls around")
    break
  #End While
  
printNlog("Count of processed profiles: " + str(processedProfiles))

