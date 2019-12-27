#以下為Google Firebase儲存資料所需要的套件
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

#以下為使用者使用Google提供的Firebase所需要的金鑰
cred = credentials.Certificate('MuseumBot/museumbot-1dc63-firebase-adminsdk-7asae-60e7c50bae.json')
firebase_admin.initialize_app(cred)

# 導入Google Cloud Client的函示庫
import google.cloud

#宣告Firebase的客戶端Client
db = firestore.client()

with open('景點.txt', 'r') as f:
    for line in f.readlines():
    	line_list = line.split(',')
    	users_ref = db.collection("附近景點").document(line_list[0])
    	doc_User_action = {  
        	"主題分類": "%s " % (line_list[1].strip()),
        	"開放時間": "%s " % (line_list[2].strip()),
        	"景點費用": "%s " % (line_list[3].strip()),
           	"景點位置": "%s " % (line_list[4].strip()),
           	"景點介紹網址": "%s " % (line_list[5].strip()),
           	"圖片URL": "%s " % (line_list[6].strip())
    	}
    	try:
        	users_ref.update(doc_User_action)  # 若Firebase中已經存在該使用者的資訊
    	except google.cloud.exceptions.NotFound:
        	users_ref.set(doc_User_action)  # 若Firebase中還沒有該使用者的資訊