import json
import os
import http.client

class sendMSG:
    def __init__(self) -> None:
        self.TELEGRAM_API_HOST='api.telegram.org'
        self.TOKEN=os.environ['TOKEN']
        self.connection = http.client.HTTPSConnection(self.TELEGRAM_API_HOST)
        self.url=f'/bot{self.TOKEN}/sendMessage'
        self.headers={'content-type': 'application/json'}
    
    def set_param(self, id = '5543864766', text='default'):
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
        self.close()

    def close(self):
        self.connection.close()

class createMSG:
    async def _set_send_text(self, data_status:str , type:str, data_list:list) -> str:
        text=f'''Data status : {data_status}
Type : {type}

Date : {data_list[0]}

Title : {data_list[1]}

Url : {data_list[2]}
'''
        return text
    
    async def set_text_process(self, data_list: list, duplicate: bool, data_type: str) -> list:
        text_list=[]
        try:
            for i, data in enumerate(data_list):
                if duplicate == True and data == data_list[len(data_list) - 1]:
                    text=await self._set_send_text('TEST--Changed', data_type, data)
                    text_list.append(text)
                else:
                    text=await self._set_send_text('TEST--New', data_type, data)
                    text_list.append(text)

        except TypeError:
            pass
        
        return text_list