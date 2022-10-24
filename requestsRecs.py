import requests
import random
import json
import time

from math import sin
from time import sleep
#Locales
from pymongo_get_database import get_database


urlRecs = "https://api.gotinder.com/v2/recs/core?locale=es-ES"

headersRecs = json.load(open('./headers/recs.json'));
headersLike = json.load(open('./headers/like.json'));
headersPass = json.load(open('./headers/pass.json'));

def getRecs():
  responseRecs = requests.get(urlRecs, headers=headersRecs)
  print("Status Code", responseRecs.status_code)

  if( responseRecs.status_code != 200 ):
    raise Exception("Error getRecs codigo: " + responseRecs.status_code)

  print("JSON responseRecs ", responseRecs.json())
  return responseRecs.json()


def chooseAPhotoIdRandomly(photos):
  lenPhotos = len(photos);
  print("Numero de fotos: " + str(lenPhotos));
  randomPhoto = random.randint(0, lenPhotos-1);
  print("Numero de foto elegido: " + str(randomPhoto));
  return(photos[randomPhoto]["id"])



###Empezamos

start = time.time()

dbname = get_database()
collection_users = dbname["users"]
collection_requests = dbname["requests"]
collection_responses = dbname["responses"]
collection_swipes = dbname["swipes"]

finalSwipe = {}

recsJson = json.load(open('./ejmploRecs.json'))

bannedWordsForShortBio=["instagram", "onlyfans","ig ","of ","ig:","of:","@","sigueme"]
bannedWords=["trans ", "tranny ","tv ","transexual","⚧️","🏳️‍⚧️"]
#recsJson = getRecs() #TODO

processedProfiles = 0;
while len(recsJson["data"]["results"]) > 0 :
  for singleResult in recsJson["data"]["results"]:
    user = singleResult["user"]

    print(user["name"])
    
    cursor = collection_users.find_one({"user._id":user["_id"]})
    print(cursor)
    if(cursor):
      print("USUARIO REPETIDO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
      print("pausado....")
      input()
      continue;

    finalSwipe["_id"] = user["_id"]
    
    collection_users.insert_one(singleResult)

    reasonIPass=""

    if(len(user["bio"])==0):
      reasonIPass += "No bio "
    elif(len(user["bio"])<15 and any(ele in user["bio"].lower() for ele in bannedWordsForShortBio)):
      reasonIPass += "Just looking for Followers "
    elif(any(ele in user["bio"].lower() for ele in bannedWords)):
      reasonIPass += "Not interested because of Bio "

    if(singleResult["distance_mi"]>10):
      reasonIPass += "Too Far "

    if(reasonIPass==""):
      urlLike = "https://api.gotinder.com/like/"+ user["_id"] +"?locale=es-ES"
      idPhotoChoosen=chooseAPhotoIdRandomly(user["photos"]);
      bodyLike = {
          "s_number": singleResult["s_number"],
          "liked_content_id": idPhotoChoosen,
          "liked_content_type": "photo"
      };

      collection_requests.insert_one({"_id":user["_id"], "request" : {"url":urlLike, "data":json.dumps(bodyLike), "headers":headersLike}})
      responseLike = requests.post(urlLike, data=json.dumps(bodyLike), headers=headersLike)

      if( responseLike.status_code != 200 ):
        raise Exception("Error responseLike codigo: " + responseLike.status_code)

      collection_responses.insert_one({"_id":user["_id"], "response" : responseLike.json()})

      finalSwipe["like"] = True

    else:
      urlPass = "https://api.gotinder.com/pass/" + user["_id"] + "?locale=es-ES&s_number=" + str(singleResult["s_number"])
      idPhotoChoosen=chooseAPhotoIdRandomly(user["photos"]);

      collection_requests.insert_one({"_id":user["_id"], "request" : {"url":urlPass, "headers":headersPass}})
      responsePass = requests.get(urlPass, headers=headersPass)

      if( responsePass.status_code != 200 ):
        raise Exception("Error responsePass codigo: " + responsePass.status_code)

      collection_responses.insert_one({"_id":user["_id"], "response" : responsePass.json()})
      
      finalSwipe["like"] = False
      finalSwipe["reasonIPass"] = reasonIPass

    
    collection_swipes.insert_one(finalSwipe)
    print("Me gusta: " +  ("Si" if reasonIPass=="" else "No"))


    processedProfiles +=1
    #tiempoEspera = round(random.uniform(0, 0.4), 3);
    tiempoEspera = round(random.uniform(2.5, 4), 3); #TODO
    print("Se continua en: " + str(tiempoEspera))
    sleep(tiempoEspera)


  if(processedProfiles >=100):
    break;
  recsJson = getRecs() #TODO
  
  #End While
  
print("Total de perfiles procesados: " + str(processedProfiles))

