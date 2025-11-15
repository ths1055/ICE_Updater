import gspread_asyncio
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import os
import asyncio

class dataIo:
    def __init__(self):
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(self.get_creds)
        self.agsp = None
        self.sheet = None

    async def set_agsp(self):
        self.agsp = await self.agcm.authorize()

    def get_creds(self):
        creds = Credentials.from_service_account_file(os.environ['JSON_KEY_NAME'])
        scoped = creds.with_scopes([
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ])
        return scoped

    async def set_worksheet(self, url:str, worksheet:str):
        doc = await self.agsp.open_by_url(url)
        sheet = await doc.worksheet(worksheet)
        self.sheet = sheet
    
    async def opensheet(self, url:str) -> None:
        doc = await self.agsp.open_by_url(url)
        sheet = await doc.worksheet('시트1')
        return sheet
    
    async def _insert_data(self, insert_data: list):
        await self.sheet.insert_rows(insert_data)

    async def get_all_sheetdata(self) -> list:
        sheet_data = await self.sheet.get_all_values()
        return sheet_data

    async def get_primary_sheetdata(self, target_URL: str, target_sheet: str) -> list: #초기 비교용 데이터 3개
        print(f'start - {target_sheet} : {target_URL}')
        await self.set_worksheet(target_URL, target_sheet)
        primary_sheet_data = await self.sheet.get('A1:C5')
        return primary_sheet_data
    
    async def data_save_process(self, data_set: list, duplicate_TF: bool, target_URL: str, target_sheet: str) -> None:
        await self.set_worksheet(target_URL, target_sheet)
        if duplicate_TF == True:
            await self.sheet.delete_rows(index=1, end_index=1)
        else:
            pass
        
        try:
            await self._insert_data(data_set)

        except TypeError:
            print('New Data is not founded')#log
            pass

    async def test_delete(self):
        await self.sheet.delete_rows(index=1)

async def test():
    d = dataIo()
    await d.set_agsp()

if __name__ == "__main__":
    asyncio.run(test())