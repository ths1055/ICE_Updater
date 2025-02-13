import asyncio

class DataProcess:
    def _compare_data(self, parse_data: list, sheet_data: list) -> int:
        #index// 0: date, 1: title, 2: URL
        #갱신된 것이 없으면 None을 return
        if len(parse_data) >= 2:
            for compare_data in sheet_data:
                for i, DATA_parsed in enumerate(parse_data):
                    if compare_data[1] in DATA_parsed:
                        return i, False
                    elif compare_data[2] in DATA_parsed:
                        return i, True
                    else:
                        pass
            return None
        
        else:
            for compare_data in sheet_data:
                #print(compare_data[1], parse_data[0])
                if compare_data[1] in parse_data[0]:#title compare
                        return 0, False
                elif compare_data[2] in parse_data[0]:#URL compare
                    return 0, True
                else:
                    pass
            return None
        
    def _cut_data(self, data_set: list, compare_num: int, duplicate_TF: bool) -> list:
        if compare_num == None:
            return None
        else:    
            if duplicate_TF == True:
                compare_num += 1
            else:
                pass
            cut_data=data_set[:compare_num]
            return cut_data
        
    async def select_data(self, parse_data: list, sheet_data: list) -> list:
        NUM_refresh, duplicate_TF = self._compare_data(parse_data, sheet_data)

        cut_data = self._cut_data(parse_data, NUM_refresh, duplicate_TF)

        return cut_data, duplicate_TF
