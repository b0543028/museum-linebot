# MuseumBot博物館導覽Line聊天機器人
本專案設計了一個博物館導覽Line聊天機器人。這個專案主要分成五個部分：
* **<h3>第一部分為Dialogflow部分</h3>**
  * 這部分使用了Google Dialogflow的服務，使用前先至[Dialogflow的網站](https://dialogflow.com/)註冊並創建一個新的項目。  
  * 而*Dialogflow*中的*MuseumBot_Dialogflow.zip*是將我利用蘭陽博物館網站上的QA集訓練的intent以及entities打包下來，如果要使用的話需要到剛剛創建的項目的設定中找到**Export and Import**，並選擇**IMPORT FROM ZIP**將剛剛的zip導入(如圖1)。
  * 在*MuseumBot*檔案中的*museum.py*程式裡面需要輸入dialogflow的API金鑰(**DIALOG_API_KEY**)，同樣是在創建項目的設定中的**General**中找到(如圖2)，點選**Service Account**會連結到Google Cloud Platform，這邊可以建立dialogflow的API金鑰。
  * 有什麼疑問可以參考[Dialogflow的說明文件](https://dialogflow.com/docs/getting-started)。
    
  ![image](https://github.com/ArrowHuang/LineBot-MuseumBot/blob/master/Screenshot/Dialogflow2.png)    
  <p align="center">圖1</p>   
  
  ![image](https://github.com/ArrowHuang/LineBot-MuseumBot/blob/master/Screenshot/Dialogflow1.png)    
  <p align="center">圖2</p>   
  
* **<h3>第二部分為建置LineBot</h3>**  
  * 這部分使用了Line聊天機器人的服務，使用前先至[Line Developer的網站](https://developers.line.biz/en/)註冊並創建一個新的項目。
  * 在*MuseumBot*檔案中的*museum.py*程式裡面需要輸入**CHANNEL_ACCESS_TOKEN**以及**CHANNEL_SECRET**，可以在剛剛創建的項目中找到(如圖3圖4)。
  
  ![image](https://github.com/ArrowHuang/LineBot-MuseumBot/blob/master/Screenshot/LineBot1.png)    
  <p align="center">圖3</p>   
  
  ![image](https://github.com/ArrowHuang/LineBot-MuseumBot/blob/master/Screenshot/LineBot2.png)    
  <p align="center">圖4</p>   
  
  * 需更改程式碼的地方 
    - **27** : FIREBASE_API_KEY
    - **42** : DIALOG_API_KEY
    - **55** : GOOGLE_MAP_API_KEY
    - **59** : **61** : CHANNEL_ACCESS_TOKEN
    - **60** : LINE_CHANNEL_SECRET
    - **154** : FIREBASE_REALTIME_URL
      
  * 將程式碼上傳到Heroku中(以下為macOS為例子示範如何將程式上傳)  
    
    **1.到官網上下載Heroku**  
    https://devcenter.heroku.com/articles/getting-started-with-python#set-up  
      
    **2.註冊並登錄Heroku的帳號**  
      
    **3.打開Terminal終端機並輸入以下程式來登錄Heroku**  
    heroku login  
      
    **4.在heroku創建一個app並將Buildpacks設定為python(我們這邊要上傳的是py檔案)**  
    heroku create food-assistant --buildpack heroku/python  
    其中create後面放app專案的名字，例如food-assistant就是一個專案的名字
      
    **5.在Heroku中找到對應的app的專案**  
    heroku git:remote -a food-assistant  
    其中-a之後的就是app專案的名稱，其中food-assistant就是專案的名稱  
      
    **6.將路徑設定到我們的檔案**  
    cd /Users/apple/Desktop/LineBot-MuseumBot
      
    **7.創建requirements.txt紀錄的我們python中用到哪些套件用於告訴Heroku需要用到哪些套件**  
    pip freeze > requirements.txt  
      
    **8.創建Profile告訴heroku**  
    pip install gunicorn  
    echo "web: gunicorn linebot:app" > Procfile  
      
    **9.將檔案上傳至git**   
    git add .  
    git commit -m "這裡加上註解"  
    git push origin master  
      
  * 找到Heroku中settings的網址並將它放到Line Developer中的Webhook URL中(如圖5圖6)。      
  * 有什麼疑問可以參考[Line Developer的說明文件](https://developers.line.biz/en/docs/)。

  ![image](https://github.com/ArrowHuang/LineBot-MuseumBot/blob/master/Screenshot/LineBot1.png)    
  <p align="center">圖5</p>   
  
  ![image](https://github.com/ArrowHuang/LineBot-MuseumBot/blob/master/Screenshot/LineBot2.png)    
  <p align="center">圖6</p>   
  
* **<h3>第三部分為Firebase服務</h3>**    
  * 這部分使用了Google Firebase的服務，使用前先至[Firebase的網站](https://firebase.google.com/)註冊並創建一個新的項目。 
  * 創建完新的項目之後到*設定/使用者權限/服務帳戶*中產生新的私密金鑰(如圖7)，並在*MuseumBot*檔案中的*museum.py*程式裡面輸入**FIREBASE_API_KEY**。
  * 利用Firebase製作一個資料讀取與儲存的功能。
  * 將**MuseumBot/firebase_realtime.json**這份資料匯入Firebase_realtime中
  * 有什麼疑問可以參考[Firebase的說明文件](https://firebase.google.com/docs)  
     
  ![image](https://github.com/ArrowHuang/LineBot-MuseumBot/blob/master/Screenshot/Firebase.png)    
  <p align="center">圖7</p>   
     
* **<h3>第四部分為Django並放在heroku免費雲端服務上面</h3>**  
  * 這部分我們利用Django假設網站並結合爬蟲程式到[勁好行的網站](http://e-landbus.tw/eLandBus/RouteQuery.aspx)爬取即時公車資訊。    
  * 我們將程式打包好放在*Realtime Bus Info*檔案中的*django_web_file.7z*中。   
  * 使用者可以按照*Django架設網站並上傳Heroku教學.pdf*將Django放在Heroku上面。

* **<h3>第五部分為ASP.NET MVC網站修改聊天機器人設定</h3>**
  * 這部份我們利用ASP.NET MVC架構架設一個網站，若聊天機器人中資訊錯誤，或錯誤資訊須回報時，可以利用本網站通報
  * 開啟MuseumLineBot.sln即可開啟專案(需安裝Visual Studio 2017 並且安裝.NET相關套件)
  * 專案開啟後，請至管理Nuget套件將套件裝上(如圖8)
  * 修改**Controllers/HomeControllers.cs**中 16行的 firebase_url
  * 後台修改與聊天機器人關聯的部分請參考**MuseumBot/museum.py**中的158行
  * 上傳json後的firebase realtime圖，上傳的檔案位於**MuseumBot/firebase_realtime.json**(如圖9)
  * 系統架構(如圖10)
  
  ![image](https://github.com/b0543028/Museum-Linebot/blob/master/Screenshot/github_file.png)    
  <p align="center">圖8</p>
  
  ![image](https://github.com/b0543028/Museum-Linebot/blob/master/Screenshot/firebase_realtime.jpg)    
  <p align="center">圖9</p>
  
  ![image](https://github.com/b0543028/museum-linebot/blob/master/Screenshot/%E7%B3%BB%E7%B5%B1%E6%9E%B6%E6%A7%8B.jpg)    
  <p align="center">圖10</p> 
