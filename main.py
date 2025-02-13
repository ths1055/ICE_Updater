import async_dataIo
import async_parser
import async_msg
import async_DataProcess
import asyncio
import os

ICE_URL = os.environ['ICE_URL']
COMPUTER_URL = os.environ['COMPUTER_URL']
YU_NEWS = os.environ['YU_NEWS']

ANNO_SHEET = os.environ['ANNO_SHEET']
ARTICLE_SHEET = os.environ['ARTICLE_SHEET']

def msg_send_process(text_list) -> None:
    sMsg = async_msg.sendMSG()
    for text in text_list:
        param=sMsg.set_param(text=text)
        sMsg.send_msg(param)

async def get_primary_data(data, sheet_url: str, type: str):
    #await data.set_worksheet(sheet_url, type)
    Data = await data.get_primary_sheetdata(sheet_url, type)
    print(f'set worksheet - {type} : {sheet_url}')
    return Data

async def test_scheduler():
    object_list = []
    #//object_list[0] = parser, [1] = dataIo, [2] = DataProcess,  [3] = createMSG
    for i in range(5):
        temp = []
        temp.append(async_parser.YUParser())
        temp.append(async_dataIo.dataIo())
        temp.append(async_DataProcess.DataProcess())
        temp.append(async_msg.createMSG())
        await temp[1].set_agsp()
        object_list.append(temp)
    

    result = await asyncio.gather(
        object_list[1][0].parser('anno', ICE_URL),
        object_list[1][0].parser('article', ICE_URL),
        object_list[2][0].parser('anno', COMPUTER_URL),
        object_list[3][0].parser('article', COMPUTER_URL),
        object_list[4][0].parser('yu_news', YU_NEWS), return_exceptions=True
)
    primary_result = await asyncio.gather(
        get_primary_data(object_list[0][1], ARTICLE_SHEET, 'yu_news'),
        get_primary_data(object_list[1][1], ARTICLE_SHEET, 'ice'),
        get_primary_data(object_list[2][1], ARTICLE_SHEET, 'computer'),
        get_primary_data(object_list[3][1], ANNO_SHEET, 'ice'),
        get_primary_data(object_list[4][1], ANNO_SHEET, 'computer'), return_exceptions=True
    )
    cut_data_set = await asyncio.gather(
         object_list[0][2].select_data(result[0], primary_result[3]),
         object_list[1][2].select_data(result[1], primary_result[1]),
         object_list[2][2].select_data(result[2], primary_result[4]),
         object_list[3][2].select_data(result[3], primary_result[2]),
         object_list[4][2].select_data(result[4], primary_result[0]), return_exceptions=True
    )

    msg_list = await asyncio.gather(
        object_list[2][3].set_text_process(cut_data_set[0][0], cut_data_set[0][1], 'ICE_Announcement'),
        object_list[3][3].set_text_process(cut_data_set[1][0], cut_data_set[1][1], 'ICE_Article'),
        object_list[0][3].set_text_process(cut_data_set[2][0], cut_data_set[2][1], 'COMPUTER_Announcement'),
        object_list[1][3].set_text_process(cut_data_set[3][0], cut_data_set[3][1], 'COMPUTER_Article'),
        object_list[4][3].set_text_process(cut_data_set[4][0], cut_data_set[4][1], 'YU-NEWS'), return_exceptions=True
)
    
    total_msg_list = []
    for i in range(5):
        total_msg_list += msg_list[i]

    msg_send_process(total_msg_list)

    await asyncio.gather(
        object_list[2][1].data_save_process(cut_data_set[0][0], cut_data_set[0][1], ANNO_SHEET, 'ice'),
        object_list[3][1].data_save_process(cut_data_set[1][0], cut_data_set[1][1], ARTICLE_SHEET, 'ice'),
        object_list[0][1].data_save_process(cut_data_set[2][0], cut_data_set[2][1], ANNO_SHEET, 'computer'),
        object_list[1][1].data_save_process(cut_data_set[3][0], cut_data_set[3][1], ARTICLE_SHEET, 'computer'),
        object_list[4][1].data_save_process(cut_data_set[4][0], cut_data_set[4][1], ARTICLE_SHEET, 'yu_news'), return_exceptions=True
    )

if __name__ == "__main__":
    asyncio.run(test_scheduler())