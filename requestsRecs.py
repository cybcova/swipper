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

def tiempoTransacurrido(start):
  print("Tiempo Transcurrido: ")
  print(time.time() - start)



###Empezamos

start = time.time()

dbname = get_database()
collection_users = dbname["users"]
collection_requests = dbname["requests"]
collection_responses = dbname["responses"]

recsJson = json.load(open('./ejmploRecs.json'))
#recsJson = getRecs() #TODO

processedProfiles = 0;
while len(recsJson["data"]["results"]) > 0 :
  for singleResult in recsJson["data"]["results"]:
    user = singleResult["user"]
    
    cursor = collection_users.find_one({"_id":user["_id"]})
    print(cursor)
    if(cursor):
      print("USUARIO REPETIDO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
      print("pausado....")
      nombre = input()
      continue;
    
    collection_users.insert_one(user)

    print(user["name"])

    iLike = True

    if(len(user["bio"])==0):
      iLike=False
    else:
      if(len(user["bio"])<15):
        iLike=False

    if(iLike):
      urlLike = "https://api.gotinder.com/like/"+ user["_id"] +"?locale=es-ES"
      idPhotoChoosen=chooseAPhotoIdRandomly(user["photos"]);
      bodyLike = {
          "s_number": singleResult["s_number"],
          "liked_content_id": idPhotoChoosen,
          "liked_content_type": "photo"
      };

      collection_requests.insert_one({"_id":user["_id"], "request" : {"url":urlLike, "data":json.dumps(bodyLike), "headers":headersLike}})
      responseLike = requests.post(urlLike, data=json.dumps(bodyLike), headers=headersLike)
      print("Status Code", responseLike.status_code)
      tiempoTransacurrido(start)

      if( responseLike.status_code != 200 ):
        raise Exception("Error responseLike codigo: " + responseLike.status_code)

      collection_responses.insert_one({"_id":user["_id"], "response" : responseLike.json()})
      print("JSON responseLike ", responseLike.json())

    else:
      urlPass = "https://api.gotinder.com/pass/" + user["_id"] + "?locale=es-ES&s_number=" + str(singleResult["s_number"])
      idPhotoChoosen=chooseAPhotoIdRandomly(user["photos"]);

      collection_requests.insert_one({"_id":user["_id"], "request" : {"url":urlPass, "headers":headersPass}})
      responsePass = requests.get(urlPass, headers=headersPass)
      print("Status Code", responsePass.status_code)
      tiempoTransacurrido(start)

      if( responsePass.status_code != 200 ):
        raise Exception("Error responsePass codigo: " + responsePass.status_code)

      collection_responses.insert_one({"_id":user["_id"], "response" : responsePass.json()})
      print("JSON responsePass ", responsePass.json())

    print("Me gusta: " +  ("Si" if iLike else "No"))

    processedProfiles +=1
    if(processedProfiles >=500):
      print("Total de perfiles procesados: " +  str(processedProfiles))
      exit()
    #tiempoEspera = round(random.uniform(0, 0.4), 3);
    tiempoEspera = round(random.uniform(2.5, 4), 3); #TODO
    print("Se continua en: " + str(tiempoEspera))
    sleep(tiempoEspera)

  recsJson = getRecs() #TODO
  
  #End While
  
print("Total de perfiles procesados: " + str(processedProfiles))










