from bs4 import BeautifulSoup
import asyncio
import aiohttp

class YUParser:
    async def parser(self, type:str, URL_target:str):
        if type == 'anno':
            PARSE_value = await self._PARSER_announcement(URL_target)
            print(f'type:{type}, url:{URL_target}')
            return PARSE_value

        elif type == 'article':
            PARSE_value = await self._PARSER_article(URL_target)
            print(f'type:{type}, url:{URL_target}')
            return PARSE_value
        
        elif type == 'yu_news':
            PARSE_value = await self._PARSER_YuNEWS(URL_target)
            print(f'type:{type}, url:{URL_target}')
            return PARSE_value
        
        elif type == 'SwEdu':
            PARSE_value = await self._PARSER_SwEdu(URL_target)
            print(f'type:{type}, url:{URL_target}')
            return PARSE_value
        
        else:
            raise ValueError
    
    async def request(self, url: str):
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
               text = await resp.read()
        return text

    async def _PARSER_article(self, url) -> list:
        DATA_result = []
        html = await self.request(url)
        DATA_raw = BeautifulSoup(html, 'html.parser')
        await asyncio.sleep(1)

        try: #count announcement_article
            offset = len(DATA_raw.find_all('tr',attrs={'class':'b-top-box'}))
        except:
            offset = 0
        
        DATA_article = (DATA_raw.find_all('tr'))

        for i in range(offset + 1): # 1 -> Del to 1st data type list
            del DATA_article[0]

        for i, data in enumerate(DATA_article):
            temp_list=[]
            temp_list.append(data.find('span', attrs={'class':'b-date'}).text.split()[0])#date
            temp_list.append(data.find('a').text.replace('\n',''))#title
            temp_list.append(url+data.find('a')['href'])#url
            DATA_result.append(temp_list)
            #print(temp_list)
        return DATA_result
    
    async def _PARSER_announcement(self, url) -> list:
        DATA_result = []
        html = await self.request(url)
        DATA_raw = BeautifulSoup(html, 'html.parser')
        await asyncio.sleep(1)
        DATA_announcement=DATA_raw.find_all('tr',attrs={'class':'b-top-box'})

        for i,data in enumerate(DATA_announcement):
            temp_list=[]
            data.select_one(f'#cms-content > div > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i + 1}) > td:nth-child(4)')#data select
            temp_list.append(data.find('span', attrs={'class':'b-date'}).text.split()[0])#date
            temp_list.append(data.find('a').text.replace('\n',''))#title
            temp_list.append(url+data.find('a')['href'])#url
            DATA_result.append(temp_list)
        DATA_result.sort(key=lambda x:x[0], reverse=True)
        return DATA_result

    async def _PARSER_YuNEWS(self, url) -> list:
        DATA_result = []
        html = await self.request(url)
        DATA_raw = BeautifulSoup(html, 'html.parser')
        await asyncio.sleep(1)
        DATA_article = DATA_raw.find_all('tr')
        #print(DATA_article[1])
        del DATA_article[0] #0번 원소에 목차 포함됨
        
        for i, data in enumerate(DATA_article):
            temp_list=[]
            try:
                temp_list.append(data.select_one(f'#cms-content > div > div > div > div.bn-list-common01.type01.bn-common > table > tbody > tr:nth-child({i+1}) > td:nth-child(4)').text)
                temp_list.append(data.find('a').text.replace('\n',''))
                temp_list.append(url+data.find('a')['href'])
            except:
                return DATA_result
            DATA_result.append(temp_list)
        return DATA_result
    
    async def _PARSER_SwEdu(self, url) -> list:
        DATA_result = []
        html = await self.request(url)
        DATA_raw = BeautifulSoup(html, 'html.parser')
        await asyncio.sleep(1)
        DATA_article = (DATA_raw.find_all('td',attrs={'class':'b-td-left'}))
        for data in DATA_article:
            temp_list=[]
            tag_a = data.select_one('a')
            #print(tag_a)
            if tag_a:
                url_parsed = tag_a['href']
                title = tag_a.select_one('span').text.strip()
                next_td = data.find_next_siblings('td')
                temp_list.append(next_td[1].text.strip())#date
                temp_list.append(title)
                temp_list.append(url+url_parsed)
                #print(temp_list)
                DATA_result.append(temp_list)
        return DATA_result
