'''
***Version 2***
Project : ICE_Updater
Developing Period : Feb. 06, 2023 ~ Feb. 25, 2023
Author : Ji-Hun Noh
Date of last update: Feb. 25, 2023
Update List :
    - v1.0 : Jan. 30, 2023
        -- Crawl announcement & article in college page, send that information to telegram
    - v2.0 : 
        -- Data save and processing mechanism all rebuilt
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
        url=os.environ['yu_url']
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
            temp_list.append(data.select_one(f'#cms-content > div > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i}) > td:nth-child(4)').text)
            temp_list.append(data.find('a').text.replace('\n',''))
            temp_list.append(url+data.find('a')['href'])
            self.parsing_list_article.append(temp_list)

    def sheet_data_parsing(self) -> list:
        '''
        지정된 스프레드 시트의 모든 데이터를 불러옵니다
        '''
        announcement_data=self.sheet.get_all_values()

        self.set_sheet(self.article_sheet_url)
        artilce_data=self.sheet.get_all_values()

        self.set_sheet(os.environ['announcement_today_url'])
        anno_today_sheet_data=self.sheet.get_all_values()

        self.set_sheet(os.environ['type_trans_sheet_url'])
        type_trans_sheet_data = self.sheet.get_all_values()

        return announcement_data, artilce_data, anno_today_sheet_data, type_trans_sheet_data

    def data_pos_check(self, announcement_sheet_data, article_sheet_data) -> int:
        '''
        마지막으로 기록된 데이터의 위치를 확인하여
        새로 불러온 데이터의 위치를 리턴합니다
        ***2023.02.19 Error : announcement 데이터의 type이 차후에 trans됨에 따라 마지막 데이터의 날짜를 기준으로 데이터 slice 필요함***
        -> clear
        '''
        primary_data_anno=announcement_sheet_data[0]
        primary_data_article=article_sheet_data[0]
        try:
            primary_anno_data_pos=self.parsing_list_announcement.index(primary_data_anno)#갱신된 데이터(anno) 시작위치

        except ValueError:
            primary_anno_data_pos=None
        primary_article_data_pos=self.parsing_list_article.index(primary_data_article)#갱신된 데이터(article) 시작위치

        return primary_anno_data_pos, primary_article_data_pos

    def data_type_trans_check(self, announcement_today_sheet_data:list) -> list:
        '''
        Announcement에서 내려간 article을 판별하여
        list형태로 리턴합니다

        data_pos_check보다 선행되어야 하는 작업입니다
        '''
        type_trans_list=[]
        if self.parsing_list_announcement == announcement_today_sheet_data:
            return None

        else:
            for i, data in enumerate(announcement_today_sheet_data):#data in announcement_today_sheet_data
                if data not in self.parsing_list_announcement:
                    type_trans_list.append(data)
            
            return type_trans_list

    def date_calculation(self, primary_data_date:str) -> list:
        '''
        announcement의 글이 article로 type이 trans 된 경우 announcement에서는 식별이 되지 않기 때문에
        날짜를 기준으로 판별해 그 위치를 리턴합니다
        '''
        offset=[10000,100,1]
        primary_map_data=map(int,primary_data_date.split(sep='.'))
        primary_calc_data=0
        for p, primary_data in enumerate(primary_map_data):
            primary_calc_data+=primary_data*offset[p]

        for i, data in enumerate(self.parsing_list_announcement):
            map_data=map(int, data[0].split(sep='.'))
            for j, data in enumerate(map_data):
                #i값이 결국 해당 값 보다 더 많아지는 시점이니까 리턴해주면 됨
                if primary_calc_data>=data*offset[j]:
                    return i-1

        raise ValueError
                
    def data_filtering(self, primary_anno_data_pos:int, primary_article_data_pos:int, primary_anno_data_date:str) -> list:
        '''
        매개변수로 주어진 마지막으로 기록된 데이터의 위치로
        새로 추가된 데이터를 선별하여 list로 리턴합니다
        '''
        try:
            filtering_anno_data=self.parsing_list_announcement[:primary_anno_data_pos]

        except ValueError:
            primary_calc_anno_data_pos=self.date_calculation(primary_anno_data_date)
            filtering_anno_data=self.parsing_list_announcement[:primary_calc_anno_data_pos]
            
        filtering_article_data=self.parsing_list_article[:primary_article_data_pos]

        return filtering_anno_data, filtering_article_data

    def set_text_process(self, type_trans_list:list, filtering_anno_list:list, filtering_article_list:list) -> list:
        '''
        전송될 텍스트 데이터를 구성하고 리스트로 반환합니다.
        '''
        text_list=[]
        try:
            for trans_type in type_trans_list:
                text=self.set_send_text('Type trans', 'Announcement -> Article', trans_type)
                text_list.append(text)

        except TypeError:
            pass

        try:
            for anno_data in filtering_anno_list:
                text=self.set_send_text('Normal', 'Announcement', anno_data)
                text_list.append(text)

        except TypeError:
            pass

        try:
            for article_data in reversed(filtering_article_list):
                text=self.set_send_text('Normal', 'Article', article_data)
                text_list.append(text)

        except TypeError:
            pass
        
        return text_list

    def msg_send_process(self, text_list) -> None:
        for text in text_list:
            param=self.set_param(text=text)
            self.send_msg(param)

    def data_saving(self, anno_data_list:list, article_data_list:list, type_trans_list:list) -> None:
        try:
            self.set_sheet(self.announcement_sheet_url)
            self.sheet.insert_rows(anno_data_list)

        except TypeError:
            print('New announcement data is not founded')
            pass

        try:
            self.set_sheet(self.article_sheet_url)
            self.sheet.insert_rows(article_data_list)

        except TypeError:
            print('New Article data is not founded')
            pass
        
        #anno_today -> not occur exception
        self.set_sheet('https://docs.google.com/spreadsheets/d/16zlzptzXkF19d6w4mZVdYYNsfXnvPSuZhiKXTISIJUI')
        self.sheet.clear()
        self.sheet.insert_rows(self.parsing_list_announcement)

        try:
            self.set_sheet('https://docs.google.com/spreadsheets/d/1qsIrrD2Uu-hQRt33at9Drzm47Mv1i3D71XWlx_6c82M')
            self.sheet.insert_rows(type_trans_list)

        except TypeError:
            print('New type trans data is not founded')
            pass

    def set_send_text(self, data_status:str , type:str, data_list:list) -> str:
        if data_status == 'Type trans':
            text=f'''Data status : {data_status}
Type : {type}

Date : {data_list[0]}

Title : {data_list[1]}

Url : {data_list[2]}
            '''
        else:   
            text=f'''Data status : {data_status}
Type : {type}

Date : {data_list[0]}

Title : {data_list[1]}

Url : {data_list[2]}
        '''
        return text

    def routine(self):
        self.parser()
        announcement_data, article_data, anno_today_sheet_data, type_trans_sheet_data = self.sheet_data_parsing()
        type_trans_list = self.data_type_trans_check(anno_today_sheet_data)
        anno_pos, article_pos = self.data_pos_check(announcement_data, article_data)
        filtering_anno_data, filtering_article_data = self.data_filtering(anno_pos, article_pos, announcement_data[0][0])
        text_data=self.set_text_process(type_trans_list, filtering_anno_data, filtering_article_data)
        print(len(text_data))
        if len(text_data) != 0:
            self.msg_send_process(text_data)
            self.close()
            self.data_saving(filtering_anno_data, filtering_article_data, type_trans_list)

def main():
    dp=dataProcess()
    dp.routine()

if __name__ == "__main__":
    main()