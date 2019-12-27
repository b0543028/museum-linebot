# encoding: utf-8
# 爬蟲程式用於爬網頁上活動資訊

# 導入Firebase所需要的套件
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# 導入爬蟲所需要的程式
import requests
from bs4 import BeautifulSoup

# 將爬蟲需要的headers定義好先
request_headers = {'User-Agent': 'Mozilla/5.0'}

# 導入Google Cloud Client的函示庫
import google.cloud

import datetime,pytz
# 宣告我們的時區
tz = pytz.timezone('Asia/Taipei')

Month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# Firebase金鑰認證，驗證身分，只需要驗證一次就好了
cred = credentials.Certificate('museumbot-1dc63-firebase-adminsdk-7asae-60e7c50bae.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# 將文字的時間轉換成數字的
def Change_Time(String_Time):
	time_list = String_Time.split(' ')
	month = time_list[1]
	month = Month.index(month)+1
	day = time_list[2]
	year = time_list[-1]
	return (str(year)+'/'+str(month)+'/'+str(day))


# 先爬學習與活動/推廣活動
def Push_Activity():
	res = requests.get('http://www.lym.gov.tw/ch/education/activity/', headers=request_headers)
	soup = BeautifulSoup(res.text, 'lxml')
	table = soup.find_all('div','sna-item')
	if(len(table)>0):
		for each_table in table:
			url = each_table.find('a')
			if(url!=None):
				activity_date = each_table.find('div','date-text')
				if(activity_date!=None):
					url = url.get('href')
					activity_url = 'http://www.lym.gov.tw'+url

					activity_date = activity_date.text.split('時間')[1].strip()
					last_date_list = activity_date.split('~')[1].split('/') # 取得活動最後結束時間
					x = datetime.datetime.now(tz)  # 取得當下時間
					
					if(x.year<int(last_date_list[0].strip())):
						Push_2_Firebase(activity_url)

					elif(x.year==int(last_date_list[0].strip())):
						if(x.month<int(last_date_list[1].strip())):
							Push_2_Firebase(activity_url)

						elif(x.month==int(last_date_list[1].strip())):
							if(x.day<int(last_date_list[2].strip())):
								Push_2_Firebase(activity_url)
			else:
				print(' 找不到對應網址 ')
	else:
		print(' 學習與活動/推廣活動中沒有找到活動，請檢查 ')


# 利用URL去爬學習與活動/推廣活動的資訊並上傳Firebase
def Push_2_Firebase(activity_url):
	people = ''
	activity_shareUrl = ''
	activity_people = ''
	activity_fee = ''
	activity_time = ''
	activity_time2 = ''
	activity_place = ''

	res = requests.get(activity_url, headers=request_headers)
	soup = BeautifulSoup(res.text, 'lxml')
	activity_title = soup.find('div','snad-left-title')
	if(activity_title!=None):
		activity_title = '(推廣活動)'+activity_title.text.strip() # 活動名稱
		img_table = soup.find('div','snad-pic')
		if(img_table!=None):
			activity_imgUrl = img_table.find('img').get('src')
			activity_imgUrl = 'http://www.lym.gov.tw'+activity_imgUrl # 活動海報URL

			share_info = soup.find_all('div','share-link')
			for each_info in share_info:
				each_share_info = each_info.find_all('a')
				for e in each_share_info:
					if(e.get('title')=='加入google行事曆'):
						activity_shareUrl = e.get('href') # Google行事曆的預約功能
						print(activity_title,activity_shareUrl)
			
			info_table = soup.find('div','snad-left-info')
			info_list = info_table.find_all('div','date-01')
			for each_list in info_list:
				if(each_list.find('div','date-title').text.strip()=='適用對象'):
					people = each_list.text.replace('適用對象','').replace('\t','').replace('\n',' ').strip()
					
				if(each_list.find('div','date-title').text.strip()=='活動對象'):
					if(each_list.find('div','date-text').text.strip()!=''):
						people = each_list.find('div','date-text').text.strip()
					
				if(each_list.find('div','date-title').text.strip()=='活動費用'):
					activity_fee = each_list.find('div','date-text').text.strip() # 活動費用
					
				if(each_list.find('div','date-title').text.strip()=='活動地點'):
					activity_place = each_list.find('div','date-text').text.strip() # 活動地點
					
				if(each_list.find('div','date-title').text.strip()=='活動時間'):
					activity_time = each_list.find('div','date-text').text.strip()
					left_T = activity_time.split('~')[0].strip()
					right_T = activity_time.split('~')[1].strip()
					if('/' not in left_T):
						left_T = Change_Time(left_T)

					if('/' not in right_T):
						right_T = Change_Time(right_T)

					activity_time = left_T + '~' + right_T # 活動時間

				if(each_list.find('div','date-title').text.strip()=='報名時間'):
					activity_time2 = each_list.find('div','date-text txt-red').text.strip()
					left_T = activity_time2.split('~')[0].strip()
					right_T = activity_time2.split('~')[1].strip()
					if('/' not in left_T):
						left_T = Change_Time(left_T)

					if('/' not in right_T):
						right_T = Change_Time(right_T)

					activity_time2 = left_T + '~' + right_T # 報名時間

			activity_people = people # 使用或者活動對象
			# print(activity_people)


# 先爬展演資訊/主題展
def Topic_Activity():
	res = requests.get('http://www.lym.gov.tw/ch/exhibition/thematic-exhibition/', headers=request_headers)
	soup = BeautifulSoup(res.text, 'lxml')
	table = soup.find_all('div','sna-item')
	if(len(table)>0):
		for each_table in table:
			url = each_table.find('a')
			if(url!=None):
				activity_place = each_table.find('div','item-catetag cate-a').text
				activity_date = each_table.find('div','date-text')
				if(activity_date!=None):
					url = url.get('href')
					activity_url = 'http://www.lym.gov.tw'+url

					activity_date = activity_date.text.replace('\t','').replace('\n','').strip()
					last_date_list = activity_date.split('~')[1].split('.') # 取得活動最後結束時間
					x = datetime.datetime.now(tz)  # 取得當下時間
					
					if(x.year<int(last_date_list[0].strip())):
						Topic_2_Firebase(activity_url,activity_place,activity_date)

					elif(x.year==int(last_date_list[0].strip())):
						if(x.month<int(last_date_list[1].strip())):
							Topic_2_Firebase(activity_url,activity_place,activity_date)

						elif(x.month==int(last_date_list[1].strip())):
							if(x.day<int(last_date_list[2].strip())):
								Topic_2_Firebase(activity_url,activity_place,activity_date)
			else:
				print(' 找不到對應網址 ')
	else:
		print(' 展演資訊/主題展中沒有找到活動，請檢查 ')


# 利用URL去爬展演資訊/主題展的資訊並上傳Firebase
def Topic_2_Firebase(activity_url,activity_place,activity_date):
	res = requests.get(activity_url, headers=request_headers)
	soup = BeautifulSoup(res.text, 'lxml')
	activity_title = soup.find('div','snad-left-title')
	if(activity_title!=None):
		activity_title = '(主題展)'+activity_title.text.strip() # 活動名稱
		img_table = soup.find('div','snad-pic')
		if(img_table!=None):
			activity_imgUrl = img_table.find('img').get('src')
			activity_imgUrl = 'http://www.lym.gov.tw'+activity_imgUrl # 活動海報URL

			share_info = soup.find_all('div','share-link')
			for each_info in share_info:
				each_share_info = each_info.find_all('a')
				for e in each_share_info:
					if(e.get('title')=='加入google行事曆'):
						activity_shareUrl = e.get('href') # Google行事曆的預約功能
						print(activity_title,activity_shareUrl)
						


Push_Activity()
Topic_Activity()






