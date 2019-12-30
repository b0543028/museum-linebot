from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, PostbackEvent, LocationMessage, TemplateSendMessage, ConfirmTemplate,ButtonsTemplate,
    TextMessage, TextSendMessage,QuickReplyButton, QuickReply,LocationAction,CarouselColumn,CarouselTemplate,
    PostbackAction, PostbackTemplateAction, MessageAction,URITemplateAction, ImageSendMessage,
    ImageMessage, AudioMessage, BeaconEvent, FollowEvent, ConfirmTemplate

)
from liffpy import (
    LineFrontendFramework as LIFF,
    ErrorResponse
)

#以下為Google Firebase儲存資料所需要的套件
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

#以下為使用者使用Google提供的Firebase所需要的金鑰
cred = credentials.Certificate('FIREBASE_API_KEY')
firebase_admin.initialize_app(cred)

#宣告Firebase的客戶端Client
db = firestore.client()

# 導入googlemaps的套件
import googlemaps

# 導入Google Cloud Client的函示庫
import google.cloud

import datetime,pytz,random,os,tempfile,errno

# Dialogflow的API
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "DIALOG_API_KEY"
from math import *
# 宣告我們的時區
tz = pytz.timezone('Asia/Taipei')

#將m4a語音專程wav語音時專用
from pydub import AudioSegment
import soundfile

global beacon_id
beacon_id = 0

# 註冊googlemap的API的client
gmaps = googlemaps.Client(key='GOOGLE_MAP_API_KEY')

app = Flask(__name__)

line_bot_api = LineBotApi('CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('LINE_CHANNEL_SECRET')
liff_api = LIFF('CHANNEL_ACCESS_TOKEN')

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
Yilan_list = ['羅東','礁溪','宜蘭']

#創造一個tmp的路徑來下載圖片或者語音#
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

#****m4a轉wav 16 bits****#
def m4a_to_wav(filename):
    src = filename
    dst = filename.replace('.m4a','.wav')
    sound = AudioSegment.from_file(src)
    sound.export(dst, format="wav")
    data, samplerate = soundfile.read(dst)
    soundfile.write(dst, data, samplerate, subtype='PCM_16')
    return dst

#****使用者不知道可以問什麼的時候的攻略****#
def get_help(user_token):
    Text = '您好！我是蘭博導覽小助手'+\
    '\n你可以尋問我以下問題：'+\
    '\n「票價及注意事項」'+\
    '\n・入館需要注意什麼？\n・博物館的票價資訊\n・如何租借語音導覽？\n・如何租借輪椅車？\n・蘭陽博物館的開館時間...\n'+\
    '\n「導覽資訊」'+\
    '\n・蘭陽博物館在哪裡？\n・在蘭陽博物館可以看什麼？...\n'+\
    '\n「活動消息」'+\
    '\n・博物館最近有什麼活動？...\n'+\
    '\n「美食資訊」'+\
    '\n・附近有什麼吃的？...\n'+\
    '\n「附近景點」'+\
    '\n・博物館附近有哪些景點？...\n'+\
    '\n「交通資訊」'+\
    '\n・宜蘭到博物館怎麼走？\n・台北如何到蘭博？...\n\n祝你有個美好的一天。'
    line_bot_api.push_message(user_token,TextSendMessage(text=Text))

#****利用dialogflow判斷文字intent****#
def detect_intent_texts(project_id, session_id, text, language_code):

    from dialogflow_v2 import SessionsClient,types
    session_client = SessionsClient()

    session = session_client.session_path(project_id, session_id)
    #print('Session path: {}\n'.format(session))

    
    text_input = types.TextInput(
        text=text, language_code=language_code)

    query_input = types.QueryInput(text=text_input)

    response = session_client.detect_intent(
        session=session, query_input=query_input)

    return(response.query_result.query_text,response.query_result.intent.display_name,response.query_result.fulfillment_text)

#****利用dialogflow判斷語音intent****#
def detect_intent_audio(project_id, session_id, audio_file_path,language_code):
    
    import dialogflow_v2 as dialogflow

    session_client = dialogflow.SessionsClient()

    # Note: hard coding audio_encoding and sample_rate_hertz for simplicity.
    audio_encoding = dialogflow.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16
    sample_rate_hertz = 16000

    session = session_client.session_path(project_id, session_id)
    #print('Session path: {}\n'.format(session))

    with open(audio_file_path, 'rb') as audio_file:
        input_audio = audio_file.read()

    audio_config = dialogflow.types.InputAudioConfig(
        audio_encoding=audio_encoding, language_code=language_code,
        sample_rate_hertz=sample_rate_hertz)
    query_input = dialogflow.types.QueryInput(audio_config=audio_config)

    response = session_client.detect_intent(
        session=session, query_input=query_input,
        input_audio=input_audio)

    return(response.query_result.query_text,response.query_result.intent.display_name,response.query_result.fulfillment_text)

#****firebase_realtime網址****#
from firebase import firebase
firebase = firebase.FirebaseApplication('FIREBASE_REALTIME_URL', None)

#****判斷intent之後的動作****#
def intent_action(content,intent,respond,event):  
        #****若有將資料加入FIREBASE，可取消註解程式碼159~182****#
        """
        if(intent=='address'): # 問蘭陽博物館地址
           Text = firebase.get('/LanyangMuseum/Address', 'address') + '\n聯絡電話為' + firebase.get('/LanyangMuseum/Address', 'phone')
           line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=Text))
        elif(intent=='content'): # 問蘭陽博物館的內容
            Text = firebase.get('/LanyangMuseum', 'Content')
            Text = Text.replace('#','\n')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=Text))
        elif(intent=='notce'): # 問入館須知
            Text = firebase.get('/LanyangMuseum', 'Notce')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=Text))
        elif(intent=='opentime'): # 問開館時間
            Text = firebase.get('/LanyangMuseum', 'Opentime')
            Text = Text.replace('#','\n')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=Text))
        """
        
        if(intent=='address'): # 問蘭陽博物館地址
            respond = respond.replace(',','\n')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=respond))
        elif(intent=='content'): # 問蘭陽博物館的內容
            respond = respond.replace('#','\n')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=respond))
        elif(intent=='notce'): # 問入關須知
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=respond))
        elif(intent=='opentime'): # 問開館時間
            respond = respond.replace('#','\n')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=respond))
        elif(intent=='facility'): # 詢問基礎設施如輪椅 娃娃車 語音導覽 停車場
            if('輪椅' in respond or '娃娃車' in respond):
                Text = '娃娃車及輪椅可以免費借用，並需抵押有照片之有效證件(如:身份證、健保卡…)\n下午4點過後尚可租借，但必需於下午5點休館前歸還。\n以上物品若損壞遺失須照原價賠償。'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            elif('導覽' in respond):
                Text = '個人語音導覽機及子母機租用，需抵押有照片之有效證件(如:身份證、健保卡…)\n語音導覽機提供華語、英語、日語三種服務。\n費用為：語導機華語50元/台、語導機英日文100元/台，下午五點前歸還\n租用子母機時，每台20元，請前三天電話聯繫確認。'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            elif('停車' in respond):
                Text = '1.本館旁有臨時停車處可供下車，但遊覽車請停放至烏石港遊客中心停車場。(臨時下車處是不准停車)\n2.本館旁有收費停車場可供小客車停車(153個車位含4個身障車位)，也有機車停車格100以上(含腳踏車停車格)，是外包收費停車場，門票無法折抵'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
        elif(intent=='unable'): # 詢問無障礙設施
            if('電梯' in content): # 無障礙電梯
                Text = '1.一樓大廳有無障礙電梯 :可通往2樓國際會議廳、2樓序展互動劇場 。\n2.常設展無障礙電梯:位於「時光廊」的電梯可通往常設展廳\n4F「山之層」\n3F「平原層」\n2F「海之層」 '
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            elif('廁所' in content or '洗手間' in content): # 無障礙廁所
                Text = '本館各處廁所都設置有無障礙廁所，例如\n1F－服務大廳旁\n2F－常設展海層展區旁\n3F－常設展平原層展區旁。\n無障礙廁所內亦設有聽障人士災害警示鈴。'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            elif('坡道' in content or '道路' in content): # 無障礙坡道
                Text = '無障礙停車格旁的無障礙坡道將引導行動不便的民眾抵達服務大廳外側入口處。'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            elif('停車' in content): # 無障礙停車格
                Text = '本館於靠台二省道（青雲路三段）側，設有2格無障礙停車格，供行動不便的參訪民眾使用。'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            elif('服務' in content): # 無障礙服務鈴
                Text = '本館正門入口服務大廳的東、西兩側都設有服務鈴，行動不便的民眾若需要協助入館，按下鈴後，會有專人迅速提供服務。'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            else:
                Text = '對不起，親\n機器人聽不太懂您的意思，能否換一種說法再問一次'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
        elif(intent=='food'): # 詢問食物
            if(respond==''):
                text_message = TextSendMessage(text='請選擇您想要了解的食物資訊的類型',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F%E6%B4%BB%E5%8B%95.png?alt=media&token=c2778ae4-68d7-41e7-8dca-f5622f431066',
                                               action=MessageAction(label="館內美食", text="獲得館內美食資訊")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F%E9%A3%9F%E7%89%A9.png?alt=media&token=3cfe7bbc-0c91-4501-b055-758775f0fb38',
                                               action=MessageAction(label="附近美食", text="獲得附近美食資訊"))
                                       ]))
                line_bot_api.push_message(event.source.user_id, text_message)
            else:
                food_nearby(event.source.user_id,respond)
        elif(intent=='price'): # 詢問價格
            respond = respond.replace('#','\n')
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=respond))
        elif(intent=='traffic'): # 詢問交通  
            if(len(respond.split('#'))>1):      
                if(respond.split('#')[0]=='頭城火車站' and respond.split('#')[1]=='蘭陽博物館'):
                    Text = '(頭城火車站出發)\n在頭城火車站左斜方頭城農會旁搭乘\n頭城免費接駁公車 (平假日)\n國光 綠18 付費公車 (平假日)\n噶瑪蘭 131 付費公車 (平日)\n\n(頭城青雲路上出發)\n國光 1766 付費公車 (平日)\n國光 紅1 付費公車 (假日)'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=Text))
                elif(respond.split('#')[0] in Yilan_list and respond.split('#')[1]=='蘭陽博物館'):
                    Text = '台鐵火車搭至頭城站下車,接公車到蘭博\n國光1766付費公車 (平日)\n國光 紅1 付費公車 (假日)'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=Text))
                elif(respond.split('#')[0] == '台北' and respond.split('#')[1]=='蘭陽博物館'):
                    Text = '國光 1877 直達烏石港,蘭博站可下車 付費公車\n首都客運或噶瑪蘭客運或國光客運，搭至礁溪轉運站，再轉搭公車到蘭博\n搭台鐵火車至頭城站,接公車到蘭博'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=Text))
                elif(respond.split('#')[0] == '國道' and respond.split('#')[1]=='蘭陽博物館'):
                    Text = '請下頭城交流道之後右轉一直走大約10-15分鐘就會到本館(GPS系統定位蘭陽博物館)'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=Text))  
                elif(respond.split('#')[0] == '蘭陽博物館' and respond.split('#')[1]=='台北'):
                    Text = '至烏石港轉運站搭乘國光 1877 直達南港圓山轉運站\n至頭城火車站搭台鐵到台北\n至礁溪轉運站搭國道客運到台北'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=Text))  
                elif(respond.split('#')[0] == '蘭陽博物館' and respond.split('#')[1]=='頭城火車站'):
                    Text = '至烏石港轉運站搭乘\n國光 綠18 付費公車 (平假日)\n噶瑪蘭 131 付費公車 (平日)\n國光1766付費公車 (平日)\n國光 紅1 付費公車 (假日)'
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=Text))  
            else:
                text_message = TextSendMessage(text='請選擇您慾搭乘的交通工具',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F55283.png?alt=media&token=32a65293-8131-4396-a982-59dc09ad7f41',
                                               action=LocationAction(label="自駕", text="獲得自駕的交通資訊")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F61798-200.png?alt=media&token=329e2a72-65de-4d65-aab9-1d3069ea8ce6',
                                               action=MessageAction(label="公車", text="獲得公車的交通資訊"))
                                       ]))
                line_bot_api.push_message(event.source.user_id, text_message)
        elif(intent=='sightseeing'): # 詢問景點
            if(respond=='金車城堡館'):
                Text = '台二線北上的方向直行約五分鐘，會在右手邊看到一件黃色建築物，為外澳遊客中心，對面的接天宮牌樓進去往上即可'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))  
            elif(respond=='傳統藝術中心'):
                Text = '請搭公車至羅東轉運站，再轉乘傳藝線公車可達 (搭車族群)\n沿台二線往南行，至154.5 K處目的地在右邊 (自行開車)'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            elif(respond=='金車噶瑪蘭酒莊'):
                Text = '請先沿著台二線往礁溪方向走接台九線，走到宜蘭之後，往員山的台七線走，您就會看到路標'
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=Text))
            else:
                sightseeing_nearby(event.source.user_id)
        elif(intent=='activity'): # 問蘭陽博物館的活動
            getActivity(event.source.user_id)
        elif(intent=='help'): # 問我能問什麼
            get_help(event.source.user_id)
        elif(intent=='guide'): # 問導覽部分
            if beacon_id == "floor1": # 在一樓
                if(respond=='兒童區'):
                    message = ImageSendMessage(
                        original_content_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E5%85%92%E7%AB%A5.png?alt=media&token=b09bec05-551d-4358-9122-1b1bf6ebc38b',
                        preview_image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E5%85%92%E7%AB%A5.png?alt=media&token=b09bec05-551d-4358-9122-1b1bf6ebc38b'
                    )
                    line_bot_api.reply_message(event.reply_token, message)
                elif(respond=='哺乳區'):
                    message = ImageSendMessage(
                        original_content_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E5%93%BA%E4%B9%B3.png?alt=media&token=4f0fe5d2-65e2-4947-9cd1-3622db172e08',
                        preview_image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E5%93%BA%E4%B9%B3.png?alt=media&token=4f0fe5d2-65e2-4947-9cd1-3622db172e08'
                    )
                    line_bot_api.reply_message(event.reply_token, message)
                elif(respond=='廁所'):
                    message = ImageSendMessage(
                        original_content_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E5%BB%81%E6%89%80.png?alt=media&token=6552253b-258e-4166-b232-0bd19230b074',
                        preview_image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E5%BB%81%E6%89%80.png?alt=media&token=6552253b-258e-4166-b232-0bd19230b074'
                    )
                    line_bot_api.reply_message(event.reply_token, message)
                elif(respond=='餐廳'):
                    message = ImageSendMessage(
                        original_content_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E9%A4%90%E5%BB%B3.png?alt=media&token=a651c9c9-9db8-47b7-927d-f96ea5ed3c1a',
                        preview_image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%B8%80%E6%A8%93%E9%A4%90%E5%BB%B3.png?alt=media&token=a651c9c9-9db8-47b7-927d-f96ea5ed3c1a'
                    )
                    line_bot_api.reply_message(event.reply_token, message)
            elif beacon_id == "floor2": # 二樓
                if(respond=='廁所'):
                    message = ImageSendMessage(
                        original_content_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%BA%8C%E6%A8%93%E5%BB%81%E6%89%80.png?alt=media&token=8414ef27-0365-4b52-b171-7612a71ba1eb',
                        preview_image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/%E5%B0%8E%E8%A6%BD%E5%95%8F%E8%B7%AF%2F%E4%BA%8C%E6%A8%93%E5%BB%81%E6%89%80.png?alt=media&token=8414ef27-0365-4b52-b171-7612a71ba1eb'
                    )
            else:
                Text = '您尚未開啟藍芽導覽，請先開啟'
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=Text))

#****計算兩點之間距離****#
def calcDistance(Lat_A, Lng_A, Lat_B, Lng_B):
    EARTH_RADIUS = 6378.137;#赤道半径(单位km)  
    radLat1 = radians(Lat_A)
    radLat2 = radians(Lat_B)
    a=radLat1-radLat2
    b=radians(Lng_A)-radians(Lng_B)
 
    s = 2 * asin(sqrt(pow(sin(a/2),2)+cos(radLat1)*cos(radLat2)*pow(sin(b/2),2)));  
    s = s * EARTH_RADIUS;  
    #s = Math.round(s * 10000d) / 10000d;  
    return s; 

#****取得館內活動資訊給使用者****#
def getActivity(user_token):
    activity_list = []
    users_ref = db.collection('館內互動資訊')
    docs = users_ref.get()
    for doc in docs:
        if len(activity_list) == 10:
            break
        else:
            if('主題展' in str(doc.id)):
                carouselcolumn = CarouselColumn(
                    thumbnail_image_url=doc.to_dict()['活動海報'],  # 活動的圖片
                    title='主題展：%s' % (doc.id.replace('(主題展)','')),  # 電影的名字
                    text='活動地點:'+doc.to_dict()['活動地點'].strip() +'\n'+ doc.to_dict()['活動時間'].strip(),
                    actions=[
                        URITemplateAction(
                            label='查看詳細資訊',
                            uri=str(doc.to_dict()['活動網頁'])
                        ),
                        PostbackTemplateAction(
                            label='預約活動提醒',
                            data='預約活動：'+doc.id.replace('(主題展)','')
                        ),
                        URITemplateAction(
                            label='加入Gogle行事曆',
                            uri=str(doc.to_dict()['活動預約'])
                        )
                    ]
                )
                activity_list.append(carouselcolumn)
            elif('推廣活動' in str(doc.id)):
                carouselcolumn = CarouselColumn(
                    thumbnail_image_url=doc.to_dict()['活動海報'],  # 活動的圖片
                    title='推廣活動：%s' % (doc.id.replace('(推廣活動)','')),  # 電影的名字
                    text='活動地點:'+doc.to_dict()['活動地點'].strip() +'\n'+ doc.to_dict()['活動時間'].strip(),
                    actions=[
                        URITemplateAction(
                            label='查看詳細資訊',
                            uri=str(doc.to_dict()['活動網頁'])
                        ),
                        PostbackTemplateAction(
                            label='預約活動提醒',
                            data='預約活動：'+doc.id.replace('(推廣活動)','')
                        ),
                        URITemplateAction(
                            label='加入Gogle行事曆',
                            uri=str(doc.to_dict()['活動預約'])
                        )
                    ]
                )
                activity_list.append(carouselcolumn)
            elif('音樂' in str(doc.id)):
                carouselcolumn = CarouselColumn(
                    thumbnail_image_url=doc.to_dict()['活動海報'],  # 活動的圖片
                    title=doc.id.replace('(音樂)',''),  # 電影的名字
                    text='活動費用:'+doc.to_dict()['活動費用'].strip() +'\n'+ doc.to_dict()['活動時間'].strip(),
                    actions=[
                        URITemplateAction(
                            label='查看詳細資訊',
                            uri=str(doc.to_dict()['活動網頁'])
                        ),
                        PostbackTemplateAction(
                            label='預約活動提醒',
                            data='預約活動：'+doc.id.replace('(音樂)','')
                        ),
                        URITemplateAction(
                            label='加入Gogle行事曆',
                            uri=str(doc.to_dict()['活動預約'])
                        )
                    ]
                )
                activity_list.append(carouselcolumn)

    Carousel_template = CarouselTemplate(
        columns=activity_list,
        image_aspect_ratio="rectangle",  # 圖片形狀，一共兩個參數。square指圖片1:1，rectangle指圖片1.5:1
        image_size="contain"  # 圖片size大小設定，一共兩個參數。cover指圖片充滿畫面，contain指縮小圖片塞到畫面
    )
    line_bot_api.push_message(
        user_token,
        TemplateSendMessage(alt_text="為您找到了館內的活動資訊", template=Carousel_template)  
    )

#****取得館內美食資訊給使用者****#
def get_food_indoor(user_token):
    food_list = []
    users_ref = db.collection('館內食物')
    docs = users_ref.get()
    for doc in docs:
        carouselcolumn = CarouselColumn(
                    thumbnail_image_url=doc.to_dict()['餐廳圖片'],  # 餐廳圖片
                    title='餐廳名稱：%s' % (doc.id),  # 餐廳的名字
                    text='營業時間:'+doc.to_dict()['營業時間'].strip() +'\n'+ '聯絡電話:'+doc.to_dict()['聯絡電話'].strip(),
                    actions=[
                        PostbackTemplateAction(
                            label='獲取餐廳位置',
                            data='餐廳位置'+doc.to_dict()['餐廳位址']
                        )
                    ]
        )
        food_list.append(carouselcolumn)
    Carousel_template = CarouselTemplate(
        columns=food_list,
        image_aspect_ratio="rectangle",  # 圖片形狀，一共兩個參數。square指圖片1:1，rectangle指圖片1.5:1
        image_size="contain"  # 圖片size大小設定，一共兩個參數。cover指圖片充滿畫面，contain指縮小圖片塞到畫面
    )
    line_bot_api.push_message(
        user_token,
        TemplateSendMessage(alt_text="為您找到了館內的食物資訊", template=Carousel_template)  
    )

#****取得蘭陽博物館附近美食資訊給使用者****#
def food_nearby(user_token,food_type):
    # 第一次搜尋周圍20個餐廳
    nearby_search = gmaps.places_nearby(
        location=(24.8687221,121.8303194),
        keyword=food_type,
        language='zh-TW',
        rank_by='distance'
    )
    food_list = []

    for result in nearby_search['results']:
        if len(food_list) >= 5:
            break
        else:
            if 'geometry' in result:
                if 'location' in result['geometry']:
                    lat = result['geometry']['location']['lat']
                    lon = result['geometry']['location']['lng']
                else:
                    continue
            else:
                continue

            distance = round(calcDistance(24.8687221,121.8303194,lat,lon),2)

            if 'place_id' in result:
                place_id = result['place_id']
            else:
                continue

            if 'name' in result:
                place_name = result['name']
            else:
                continue

            if 'rating' in result:
                place_rating = result['rating']
            else:
                continue

            if 'vicinity' in result:
                place_location = result['vicinity']
            else:
                continue

            # 按照上面得到的place id搜尋place的更具體的資訊
            place_detail = gmaps.place(
                place_id=place_id,
                language='zh-TW'
            )

            if 'formatted_phone_number' in place_detail['result']:
                place_phone = place_detail['result']['formatted_phone_number'].replace(' ', '-')
            else:
                place_phone = '缺少聯絡電話'

            if 'opening_hours' in place_detail['result']:
                if 'weekday_text' in place_detail['result']['opening_hours']:
                    x = datetime.datetime.now(tz)  #取得當下時間
                    num = int(str(x.date().isoweekday())) #取得當下禮拜幾
                    time = int(str(x.hour)) #取得當下禮拜幾
                    if ',' in place_detail['result']['opening_hours']['weekday_text'][num-1][5:]:
                        hour_detail = place_detail['result']['opening_hours']['weekday_text'][num - 1][5:].split(',')
                        # print(hour_detail[0][-5:-3])
                        if time > int(hour_detail[0][-5:-3]):
                            place_openTime = hour_detail[1]
                        else:
                            place_openTime = hour_detail[0]
                    else:
                        place_openTime = place_detail['result']['opening_hours']['weekday_text'][num-1][5:]
                else:
                    place_openTime = '缺少營業時間'
            else:
                place_openTime = '缺少營業時間'

            if(len(place_name)>13):
                Text = "距離蘭博:"+str(distance)+'公里'+"\n推薦指數:" + str(place_rating) + "\n" + "聯絡電話：" + str(place_phone)+ "\n" +'營業時間：'+place_openTime
            else:
                Text = "距離蘭博:"+str(distance)+'公里'+"\n推薦指數:" + str(place_rating) + "\n" + "聯絡電話：" + str(place_phone)+ "\n" +'營業時間：'+place_openTime
            carouselcolumn = CarouselColumn(
                title=place_name,
                imageAspectRatio='square',
                text=Text,  
                actions=[
                    URITemplateAction(
                        label='導航去這吃',
                        uri='https://www.google.com/maps/dir/?api=1&destination=' + place_name.replace(" ","%2C")
                    )
                ]
            )
            food_list.append(carouselcolumn)

    if len(food_list) != 0:
        Carousel_template = CarouselTemplate(
            columns=food_list,
            image_aspect_ratio="square",  # 圖片形狀，一共兩個參數。square指圖片1:1，rectangle指圖片1.5:1
            image_size="contain"  # 圖片size大小設定，一共兩個參數。cover指圖片充滿畫面，contain指縮小圖片塞到畫面
        )
        line_bot_api.push_message(
            user_token,
            TemplateSendMessage(alt_text="為您找到了附近的"+food_type+'店', template=Carousel_template)  # 將餐廳的圖片等資訊傳送給使用者
        )
    else:
        line_bot_api.push_message(
            user_token,
            TextSendMessage('對不起，附近沒有您想要搜索的餐廳')
        )

#****取得蘭陽博物館附近景點資訊給使用者****#
def sightseeing_nearby(user_token):
    place_name = [] #景點名稱

    users_ref = db.collection("附近景點")
    docs = users_ref.get()
    for doc in docs:
        place_name.append(doc.id)

    line_bot_api.push_message(
        user_token, TextSendMessage('正在為您搜尋蘭陽博物館附近景點資訊，請稍等片刻...')
    )

    place_name_R = []
    movie_num_random = random.sample(range(0, len(place_name)), 5)
    for num in movie_num_random:
        place_name_R.append(place_name[num])

    # 宣告儲存橫向捲軸的list
    column_list = []
    for lis in range(0, len(place_name_R)):
        users_ref = db.collection("附近景點").document("%s" % (place_name_R[lis]))
        doc = users_ref.get()

        lat = doc.to_dict()['景點位置'].split(' ')[0]
        lon = doc.to_dict()['景點位置'].split(' ')[1]
        distance = round(calcDistance(24.8687221,121.8303194,float(lat),float(lon)),2)

        carouselcolumn = CarouselColumn(
            thumbnail_image_url=doc.to_dict()['圖片URL'].strip(),
            title=place_name_R[lis]+'(距離蘭博'+str(distance)+'公里)',
            text='主題分類:'+doc.to_dict()['主題分類'] + '\n' + '開放時間:' + doc.to_dict()['開放時間'],
            actions=[
                URITemplateAction(
                    label='詳細資訊',
                    uri=doc.to_dict()['景點介紹網址'].strip()
                ),
                URITemplateAction(
                    label='導航去這裡玩',
                    uri='https://www.google.com/maps/dir/?api=1&destination=' + place_name_R[lis].replace(" ","%2C")
                )
            ]
        )
        column_list.append(carouselcolumn)

    Carousel_template = CarouselTemplate(
        columns=column_list,
        image_aspect_ratio="square",  # 圖片形狀，一共兩個參數。square指圖片1:1，rectangle指圖片1.5:1
        image_size="contain"  # 圖片size大小設定，一共兩個參數。cover指圖片充滿畫面，contain指縮小圖片塞到畫面
    )
    line_bot_api.push_message(user_token, TemplateSendMessage(alt_text="為您推薦附近景點",
                                                              template=Carousel_template))

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

#*****使用者加入LineBot時候*****#
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id #取得使用者的user_id
    get_help(user_id)

#*****當使用者發送文字訊息的時候*****#
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    if(event.message.text=='搜尋交通方式'):
        text_message = TextSendMessage(text='請選擇您慾搭乘的交通工具',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F55283.png?alt=media&token=32a65293-8131-4396-a982-59dc09ad7f41',
                                               action=LocationAction(label="自駕", text="獲得自駕的交通資訊")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F61798-200.png?alt=media&token=329e2a72-65de-4d65-aab9-1d3069ea8ce6',
                                               action=MessageAction(label="公車", text="獲得公車的交通資訊"))
                                       ]))
        line_bot_api.push_message(event.source.user_id, text_message)
    elif(event.message.text=='獲得公車的交通資訊'):
        text_message = TextSendMessage(text='請選擇您慾搭乘的交通工具',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F61798-200.png?alt=media&token=329e2a72-65de-4d65-aab9-1d3069ea8ce6',
                                               action=MessageAction(label="前往蘭陽博物館", text="獲得前往蘭陽博物館的公車資訊")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F61798-200.png?alt=media&token=329e2a72-65de-4d65-aab9-1d3069ea8ce6',
                                               action=MessageAction(label="離開蘭陽博物館", text="獲得離開蘭陽博物館的公車資訊"))
                                       ]))
        line_bot_api.push_message(event.source.user_id, text_message)
    elif(event.message.text=='獲得前往蘭陽博物館的公車資訊'):
        Confirm_template = TemplateSendMessage(
            alt_text='請選擇欲搭乘的公車',
            template=ButtonsTemplate(
                text='  請選擇您欲搭乘的公車：\n【131】礁溪火車站─外澳\n【1766】南方澳─頭城\n【1877(國光)】圓山─宜蘭\n【紅1(週末)】外澳─羅東',
                actions=[                              
                    URITemplateAction(
                        label='131路公車時刻',
                        uri='line://app/1584153419-v9QoR87p'
                    ),
                    URITemplateAction(
                        label='1766路公車時刻',
                        uri='line://app/1584153419-mRleBY1O'
                    ),
                    URITemplateAction(
                        label='1877路公車時刻',
                        uri='line://app/1584153419-pOrN8X9P'
                    ),
                    URITemplateAction(
                        label='紅1路公車時刻',
                        uri='line://app/1584153419-xmyYW27j'
                    )
                ]
            )
        )
        line_bot_api.push_message(event.source.user_id, Confirm_template)    
    elif(event.message.text=='獲得離開蘭陽博物館的公車資訊'):
        Confirm_template = TemplateSendMessage(
            alt_text='請選擇欲搭乘的公車',
            template=ButtonsTemplate(
                text='  請選擇您欲搭乘的公車：\n【131】外澳─礁溪火車站\n【1766】頭城─南方澳\n【1877(國光)】宜蘭─圓山\n【紅1(週末)】羅東─外澳',
                actions=[                              
                    URITemplateAction(
                        label='131路公車時刻',
                        uri='line://app/1584153419-rZpjYm2A'
                    ),
                    URITemplateAction(
                        label='1766路公車時刻',
                        uri='line://app/1584153419-DbmPn7Vx'
                    ),
                    URITemplateAction(
                        label='1877路公車時刻',
                        uri='line://app/1584153419-Y2RW8zyj'
                    ),
                    URITemplateAction(
                        label='紅1路公車時刻',
                        uri='line://app/1584153419-pnBd4Wk0'
                    )
                ]
            )
        )
        line_bot_api.push_message(event.source.user_id, Confirm_template)   
        
    #以下為詢問附近景點的時候#
    elif(event.message.text=='搜尋附近景點'):
        sightseeing_nearby(event.source.user_id)
       
    #以下為詢問館內導覽的時候#
    elif(event.message.text=='館內導覽資訊'):
        text_message = TextSendMessage(text='請選擇您想要了解的導覽資訊',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F%E6%B4%BB%E5%8B%95.png?alt=media&token=c2778ae4-68d7-41e7-8dca-f5622f431066',
                                               action=MessageAction(label="館內活動", text="獲得館內活動")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F%E9%A3%9F%E7%89%A9.png?alt=media&token=3cfe7bbc-0c91-4501-b055-758775f0fb38',
                                               action=MessageAction(label="食物資訊", text="獲得食物資訊")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F%E5%B0%8E%E8%A6%BD.png?alt=media&token=cc00a4d9-e9df-4c0b-9383-36d3d79dfe83',
                                               action=PostbackAction(label="導覽資訊", data="獲得導覽資訊"))
                                       ]))
        line_bot_api.push_message(event.source.user_id, text_message)
    
    #以下為館內活動的時候#
    elif(event.message.text=='獲得館內活動'):
        getActivity(event.source.user_id)

    #以下為詢問食物的時候#
    elif(event.message.text=='獲得食物資訊'):
        text_message = TextSendMessage(text='請選擇您想要了解的食物資訊的類型',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F%E6%B4%BB%E5%8B%95.png?alt=media&token=c2778ae4-68d7-41e7-8dca-f5622f431066',
                                               action=MessageAction(label="館內美食", text="獲得館內美食資訊")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/museumbot-1dc63.appspot.com/o/quickreply%20button%2F%E9%A3%9F%E7%89%A9.png?alt=media&token=3cfe7bbc-0c91-4501-b055-758775f0fb38',
                                               action=MessageAction(label="附近美食", text="獲得附近美食資訊"))
                                       ]))
        line_bot_api.push_message(event.source.user_id, text_message)
    elif(event.message.text=='獲得館內美食資訊'):
        get_food_indoor(event.source.user_id)
    elif(event.message.text=='獲得附近美食資訊'):
        text_message = TextSendMessage(text='請選擇您想吃的食物的種類',
                                       quick_reply=QuickReply(items=[
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2F256-256-e1759fadf312da0295e99a13475f9e1e.png?alt=media&token=a8dc7113-5408-4a26-b3ad-c5e266a38053',
                                               action=PostbackAction(label="早午餐", data="我想去吃早午餐")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Fc1dc8bbb201d6f3dcdd2c716ae66d838.jpg?alt=media&token=6bfce381-effc-45c9-8315-917e89c5fb67',
                                               action=PostbackAction(label="海鮮", data="我想去吃海鮮")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Fsteak-575806_1280.png?alt=media&token=5933042d-39eb-40d1-a6af-ac676de67b67',
                                               action=PostbackAction(label="牛排", data="我想去吃牛排")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Fhotpot.png?alt=media&token=77b03169-8c66-4af6-b22d-1753114c3fcc',
                                               action=PostbackAction(label="火鍋", data="我想去吃火鍋")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Fluwei.png?alt=media&token=1a5044a0-59c4-4435-b6d9-3c4c542cb266',
                                               action=PostbackAction(label="滷味", data="我想去吃滷味")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Fvegan.png?alt=media&token=a145f802-64ba-4b3b-a70e-214fa2c9d1e7',
                                               action=PostbackAction(label="素食", data="我想去吃素食")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Ftiebanshao.png?alt=media&token=5471795d-cac8-47e1-88cb-56820f8c2225',
                                               action=PostbackAction(label="鐵板燒", data="我想去吃鐵板燒")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2F1406172770-1907711858_n.png?alt=media&token=573fb6e3-e4ad-45eb-abc7-a53f80158a0d',
                                               action=PostbackAction(label="吃到飽", data="我想去吃吃到飽")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Fcafe.jpg?alt=media&token=964423d8-fa14-465c-9adf-2ac3e40795bf',
                                               action=PostbackAction(label="咖啡館", data="我想去吃咖啡館")),
                                           QuickReplyButton(
                                               image_url='https://firebasestorage.googleapis.com/v0/b/niubot-40109.appspot.com/o/QuickReply%20Logo%2Fsalmon-716430_1920.jpg?alt=media&token=2813180a-d8c2-46f7-9cb1-89bc1d30bba2',
                                               action=PostbackAction(label="日本料理", data="我想去吃日本料理"))
                                       ]))
        line_bot_api.push_message(event.source.user_id, text_message)
    else:
        content, intent, respond = detect_intent_texts('museumbot-1dc63','1234',event.message.text,'zh-TW')
        print(intent,respond)
        intent_action(content,intent,respond,event)
        
#*****當使用者發送位置訊息的時候*****#
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    user_id = event.source.user_id
    #獲得經緯度
    lan = event.message.latitude
    lon = event.message.longitude
    Confirm_template = TemplateSendMessage(
        alt_text='請選擇起始地與目的地',
        template=ButtonsTemplate(
            title='請選擇起始地與目的地',
            text='請選擇蘭陽博物館作為您的起始地或目的地?\n或者重新輸入您現在的位置',
            actions=[                              
                URITemplateAction(
                    label='起始地',
                    uri='https://www.google.com/maps/dir/?api=1&origin=宜蘭博物館'+'&destination='+str(lan)+','+str(lon)
                ),
                URITemplateAction(
                    label='目的地',
                    uri='https://www.google.com/maps/dir/?api=1&origin='+str(lan)+','+str(lon)+'&destination=宜蘭博物館'
                ),
                URITemplateAction(
                    label='重新定位',
                    uri='line://nv/location'
                )
            ]
        )
    )
    line_bot_api.reply_message(event.reply_token,Confirm_template)

#*****當使用者發送語音或者圖片資訊的時候*****#
@handler.add(MessageEvent, message=(ImageMessage,AudioMessage))
def handle_message(event):
    
    #判斷是來自不同格式的文件
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, delete=False) as tf:  #將檔案放到在static/tmp中
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name
        
        #*****把static/tmp中的圖片替換掉*****#
        tf_list = tempfile_path.split('/')
        tempfile_path_change = ''
        for i in range(0,len(tf_list)-1):
            tempfile_path_change = tempfile_path_change+tf_list[i]+'/'
        tempfile_path_change += event.source.user_id

    dist_path = tempfile_path_change + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path) #把static/tmp中同一個user id的圖片替換掉

    if isinstance(event.message, AudioMessage):
        filename = m4a_to_wav('static/tmp/'+dist_name) #將m4a轉變成wav檔案
        content, intent, respond = detect_intent_audio('museumbot-1dc63','1234',filename,'zh-TW') #利用語音檔案判斷使用者的intent與entity
        print(intent,respond)
        intent_action(content,intent,respond,event)
        #if(intent=='address'):

    #print(os.path.join('static', 'tmp', dist_name))
    # line_bot_api.reply_message(
    #     event.reply_token, [
    #         TextSendMessage(text='Save content.'),
    #         TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
    #     ])

#*****當使用者發送postback的時候不會出現在文字中*****#
@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    if '餐廳位置' in event.postback.data:
        message = ImageSendMessage(
            original_content_url=event.postback.data.replace('餐廳位置',''),
            preview_image_url=event.postback.data.replace('餐廳位置','')
        )
        line_bot_api.reply_message(event.reply_token, message)
    elif '我想去吃' in event.postback.data:
        food_nearby(user_id,event.postback.data.replace('我想去吃',''))
    elif event.postback.data == '獲得導覽資訊':
        Confirm_template = TemplateSendMessage(
            alt_text='是否開啟藍芽與Line Beacon',
            template=ConfirmTemplate(
                title='是否開啟藍芽與Line Beacon',
                text='若要使用導覽功能則必須開啟藍芽與Line Beacon,是否同意？\n若點選同意,則請再「隱私設定」中的「提供使用者資料」中開啟Line Beacon',
                actions=[                              
                    URITemplateAction(
                        label='我同意',
                        uri='line://nv/settings/privacy'
                    ),
                    PostbackTemplateAction(
                        label='我不同意',
                        data='我不同意開啟藍芽'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token,Confirm_template)
    elif event.postback.data == '我不同意開啟藍芽':
        Text = '如果之後想要開啟，請再點選導覽按鈕'
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=Text))
    elif '預約活動：' in event.postback.data:
        Text = '已為您預約'+event.postback.data.replace('預約活動：','')
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=Text))

#*****當使用者使用Beacon的時候*****#
@handler.add(BeaconEvent)
def handle_beacon_event(event):
    global beacon_id
    if event.beacon.hwid == "012cb18b82":#一樓入口的基本介紹
        beacon_id = "floor1"
        if event.beacon.type == "enter":#若不判斷enter，當你離開一樓時，Beacon會在送一次
            msg = "歡迎來到蘭陽博物館\n右前方是售票處及服務台\n若需如廁，請往右走於轉角處的後方\n若攜帶兒童前來，右邊有兒童探索區\n若您覺得想先用餐，餐廳在您的左邊\n祝你有個愉快的體驗!\n蘭陽博物館敬上"
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=msg))
    
    elif event.beacon.hwid == "012cb80a3c":#二樓入口的基本介紹
        beacon_id = "floor2"
        if event.beacon.type == "enter":#若不判斷enter，當你離開一樓時，Beacon會在送一次
            msg = "歡迎您來到二樓的海之層\n首先印入眼簾的是海洋劇場\n後面有一艘本館最大展品-南風壹號\n兩側還會有掉艚仔、月桃編大索、燒玉式內燃機、鯷鯨等展品\n廁所則是在一旁出口的右手邊"
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=msg))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)