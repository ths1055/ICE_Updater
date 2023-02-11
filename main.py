'''
***Version 2***
Project : ICE_Updater
Developing Period : Feb. 06, 2023 ~ 
Author : Ji-Hun Noh
Date of last update: Jan. 30, 2023
Update List :
    - v1.0 : Jan. 30, 2023
        -- Crawl announcement & article in college page, send that information to telegram
    - v2.0 : 
        -- Filtering mechanism change
'''
import http.client
import json
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Callable
import os

class sendMSG:
    def __init__(self) -> None:
        self.TELEGRAM_API_HOST='api.telegram.org'
        self.TOKEN=os.environ['TOKEN']
        self.connection = http.client.HTTPSConnection(self.TELEGRAM_API_HOST)
        self.url=f'/bot{self.TOKEN}/sendMessage'
        self.headers={'content-type': 'application/json'}
    
    def set_param(self, id = os.environ['chat_id'], text='default'):
        param={
            'chat_id': id,
            'text' : text
        }
        return param
    
    def send_msg(self, param):
        self.connection.request('POST',self.url,json.dumps(param), self.headers)
        res=self.connection.getresponse()
        print(json.dumps(json.loads(res.read().decode()), indent=4))
        print('Response code : ', res.status)
        print('Message : ', res.msg)

    def close(self):
        self.connection.close()

'''
https://ice.yu.ac.kr/ice/board/notice.do-구조
b-top-box에 공지사항
'''

class dataProcess(sendMSG):
    def __init__(self) -> None:
        super().__init__()
        self.scope={
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
        }
        self.json_key=os.environ['json_key_name']
        self.announcement_sheet_url=os.environ['announcement_sheet_url']
        self.article_sheet_url=os.environ['article_sheet_url']
        self.credentials=ServiceAccountCredentials.from_json_keyfile_name(self.json_key, self.scope)
        self.gc=gspread.authorize(self.credentials)
        self.parsing_list_announcement=[]#0:date, 1:title
        self.parsing_list_article=[]
        self.sheet=self.open_sheet()

    def open_sheet(self) -> Callable:
        doc=self.gc.open_by_url(self.announcement_sheet_url)
        sheet=doc.worksheet('시트1')
        #print(sheet.acell('A1').value)
        #sheet.insert_row(['322','555'])
        return sheet
    
    def set_sheet(self, url:str) -> None:
        doc=self.gc.open_by_url(url)
        sheet=doc.worksheet('시트1')
        self.sheet=sheet

    def parser(self) -> None:
        url='https://ice.yu.ac.kr/ice/board/notice.do'#환경변수
        data=requests.get(url)
        bs=BeautifulSoup(data.text,'html.parser')

        data_announcement=bs.find_all('tr',attrs={'class':'b-top-box'})#공지
        data_article=bs.find_all('tr',attrs={'class':''})#일반글
        
        del data_article[0]#0번에 목차 딸려옴
        #print(d)
        for i,data in enumerate(data_announcement):
            temp_list=[]
            temp_list.append(data.select_one(f'#cms-content > div > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i+1}) > td:nth-child(4)').text)
            temp_list.append(data.find('a').text.replace('\n',''))
            temp_list.append(url+data.find('a')['href'])
            self.parsing_list_announcement.append(temp_list)
        self.parsing_list_announcement.sort(key=lambda x:x[0], reverse=True)
        
        for i, data in enumerate(data_article,len(self.parsing_list_announcement)+1):
            temp_list=[]
            print(i)
            temp_list.append(data.select_one(f'#cms-content > div > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i}) > td:nth-child(4)').text)
            temp_list.append(data.find('a').text.replace('\n',''))
            temp_list.append(url+data.find('a')['href'])
            self.parsing_list_article.append(temp_list)

    def data_filtering(self) -> int:
        '''
        case1: same data with last save data
        case2: diffrent data with last save data
        
        renew_data_count case
        0: announcement, article are None
        1: article new data founded
        10: announcemnet new data founded
        11: both new data founded
        '''
        renew_data_count=0
        announcement_data_pos=0
        article_data_pos=0

        announcement_last_data=self.sheet.row_values(1)#announcement
        if announcement_last_data[0] == self.parsing_list_announcement[0][0] and announcement_last_data[1] == self.parsing_list_announcement[0][1]:
            print('Crawl data is same to Saved data : announcement')
            renew_data_count+=0

        else:
            print('New data founded : announcement')
            renew_data_count+=10
            announcement_data_pos=self.data_pos_check(data_list=self.parsing_list_announcement, last_data=announcement_last_data)

        self.set_sheet(self.article_sheet_url)
        article_last_data=self.sheet.row_values(1)#article
        if article_last_data[0] == self.parsing_list_article[0][0] and article_last_data[1] == self.parsing_list_article[0][1]:
            print('Crawl data is same to Saved data : article')
            renew_data_count+=0

        else:
            print('New data founded : article')
            renew_data_count+=1
            article_data_pos = self.data_pos_check(data_list=self.parsing_list_article, last_data=article_last_data)
        
        self.set_sheet(self.announcement_sheet_url)

        return renew_data_count, announcement_data_pos, article_data_pos, announcement_last_data, article_last_data

    def data_verification(self, renew_data_count:int, announcement_pos:int, article_pos:int, announcement_last_data:list, article_last_data:list) -> str:
        if renew_data_count == 10:
            if self.data_check_sum(self.parsing_list_announcement, announcement_last_data, announcement_pos):
                text_announcement=[]
                for i in range(announcement_pos, -1, -1):
                    self.data_saving(self.parsing_list_announcement[i])
                    text_announcement_temp=self.set_send_text(type='Announcement', data_list=self.parsing_list_announcement[i])
                    text_announcement.append(text_announcement_temp)
                text_article=None
            else:
                print('Data checksum failed')

            return text_announcement, text_article
        
        elif renew_data_count == 1:
            if self.data_check_sum(self.parsing_list_announcement, announcement_last_data, announcement_pos):
                text_article=[]
                self.set_sheet(self.article_sheet_url)
                for i in range(article_pos, -1, -1):
                    self.data_saving(self.parsing_list_article[i])
                    text_article_temp=self.set_send_text(type='Article', data_list=self.parsing_list_article[i])
                    text_article.append(text_article_temp)
                text_announcement=None
                self.set_sheet(self.announcement_sheet_url)
            else:
                print('Data checksum failed')

            return text_announcement, text_article
        
        elif renew_data_count == 11:
            if self.data_check_sum(self.parsing_list_announcement, announcement_last_data, announcement_pos):
                text_announcement=[]; text_article=[]
                for i in range(announcement_pos, -1, -1):
                    self.data_saving(self.parsing_list_announcement[i])
                    text_announcement_temp=self.set_send_text(type='Announcement', data_list=self.parsing_list_announcement[i])
                    text_announcement.append(text_announcement_temp)
                self.set_sheet(self.article_sheet_url)
                for i in range(article_pos, -1, -1):
                    self.data_saving(self.parsing_list_article[i])
                    text_article_temp=self.set_send_text(type='Article', data_list=self.parsing_list_article[i])
                    text_article.append(text_article_temp)
                self.set_sheet(self.announcement_sheet_url)
            
            else:
                print('Data checksum failed')

            return text_announcement, text_article

        '''
        if renew_data_count == 10:
            self.data_saving(self.parsing_list_announcement[0])
            text_announcement=self.set_send_text(type='Announcement', data_list=self.parsing_list_announcement[0])
            text_article=None
            return text_announcement, text_article

        elif renew_data_count == 1:
            self.set_sheet(self.article_sheet_url)
            self.data_saving(self.parsing_list_article[0])
            self.set_sheet(self.announcement_sheet_url)
            text_article=self.set_send_text(type='Article', data_list=self.parsing_list_article[0])
            text_announcement=None
            return text_announcement, text_article

        elif renew_data_count == 11:
            self.data_saving(self.parsing_list_announcement[0])
            text_announcement=self.set_send_text(type='Announcement', data_list=self.parsing_list_announcement[0])
            self.set_sheet(self.article_sheet_url)
            self.data_saving(self.parsing_list_article[0])
            text_article=self.set_send_text(type='Article', data_list=self.parsing_list_article[0])
            self.set_sheet(self.announcement_sheet_url)
            return text_announcement, text_article
        '''
        
    def data_pos_check(self, data_list:list, last_data:list):
        return data_list.index(last_data)

    def data_check_sum(self, data_list:list, last_data:list, data_pos:int):
        print()
        #return 0 or 1

    def msg_send_process(self, text_announcement:list, text_article:list):#리스트 형식 읽어서 msg sending 할 수 있게 modify해야함
        if text_announcement != None and text_article != None:
            param_anno=self.set_param(text=text_announcement)
            param_arti=self.set_param(text=text_article)
            self.send_msg(param_anno)
            self.send_msg(param_arti)

        elif text_announcement != None and text_article == None:
            param_anno=self.set_param(text=text_announcement)
            self.send_msg(param_anno)

        elif text_announcement == None and text_article != None:
            param_arti=self.set_param(text=text_article)
            self.send_msg(param_arti)

    def data_saving(self, data:list) -> None:
        self.sheet.insert_row(data)

    def set_send_text(self, type:str, data_list:list) -> str:
        text=f'''Type : {type}

Date : {data_list[0]}

Title : {data_list[1]}

Url : {data_list[2]}
        '''
        return text

    def routine(self):
        self.parser()
        count, announcement_pos, article_pos, announcement_last_data, article_last_data=self.data_filtering()
        if count != 0:
            text_announcement, text_article=self.data_verification(count, announcement_pos, article_pos, announcement_last_data, article_last_data)
            self.msg_send_process(text_announcement, text_article)
            self.close()
        else:
            print('New data is not founded')

def main(event, context):
    dp=dataProcess()
    dp.routine()