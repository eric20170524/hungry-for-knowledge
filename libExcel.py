# -*- coding:utf-8 -*-
import re
import pandas as pd
from multiprocessing import Manager
import threading

# 创建共享内存管理器
manager = Manager()
memory_store = manager.dict()

# 设置短期记忆的上限
MEMORY_LIMIT = 100

# # 示例用法
# user_id = "user123"
# memory_name = "uploaded_file"
# # 添加记忆
# store_memory(user_id, memory_name, "First entry")
# store_memory(user_id, memory_name, "Second entry")
# # 获取所有记忆
# all_memories = get_memory(user_id, memory_name)
# print("All memories:", all_memories)
# # 获取最近两条记忆
# recent_memories = get_memory(user_id, memory_name, num_entries=2)
# print("Recent memories:", recent_memories)
def store_memory(user_id, memory_name, content):
    if user_id not in memory_store:
        memory_store[user_id] = manager.dict()
    if memory_name not in memory_store[user_id]:
        memory_store[user_id][memory_name] = manager.list()
    memory_list = memory_store[user_id][memory_name]
    memory_list.append(content)
    # 如果超过上限，删除最早的记录
    if len(memory_list) > MEMORY_LIMIT:
        memory_list.pop(0)
    memory_store[user_id][memory_name] = memory_list

def get_memory(user_id, memory_name, num_entries=None):
    if user_id in memory_store and memory_name in memory_store[user_id]:
        memory_list = memory_store[user_id][memory_name]
        if num_entries is None:
            return list(memory_list)
        else:
            return list(memory_list)[-num_entries:]
    return []


# OpenRouter API Key
OPENROUTE_API_KEY = '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'


def generate_sn(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string


def replace_with_comma(text):
    # 使用正则表达式替换换行符、中文逗号、空格和制表符为英文逗号
    return re.sub(r'[\\n\n，/\s\t]+', ',', text)


def clean_esc(text):
    # 定义要去除的特殊字符的正则表达式
    special_chars_pattern = r'[\xa0\t\n\r\u200B\u3000\u200C\u200D\u202F\u205F\u2028\u2029\x0B\x0C]'
    # 使用正则表达式替换特殊字符
    cleaned_text = re.sub(special_chars_pattern, ' ', text)
    return cleaned_text.strip()  # 去除首尾空格


def find_prompt(name, file_path="智能表格经验.xlsx"):
    df = pd.read_excel(file_path, sheet_name=0)

    # 创建字典
    result_dict = {}
    for index, row in df.iterrows():
        sheet_name = row['sheet名称'].strip()
        prompt = row['prompt']
        table_name = row['表格名称']

        result_dict[sheet_name] = {
            'prompt': prompt,
            '表格名称': table_name
        }

    # # 转换为JSON格式
    # result_json = json.dumps(result_dict, ensure_ascii=False, indent=2)
    if name in result_dict:
        res = result_dict[name]
    else:
        res = result_dict['通用prompt']
    return res


def read_excel(file_stream):
    def format_value(x):
        if isinstance(x, int):  # 判断是否为整数
            return str(x)  # 转为字符串
        elif isinstance(x, float):  # 判断是否为浮点数
            if '.' in str(x):
                decimal_part = str(x).split('.')[1]
                if len(decimal_part) == 1:  # 检查是否为整数值（即无小数部分）
                    return f"{x:.1f}"  # 格式化为保留1位小数的字符串
                else:
                    return f"{x:.2f}"
        return x  # 如果不是数值，返回原值
    
    dfs = pd.ExcelFile(file_stream)
    sheet_names= dfs.sheet_names
    sheets_list = []
    sheets_text = {}
    for sheet in sheet_names:
        df = pd.read_excel(file_stream, sheet_name=sheet, header=None)
        # 填充空值为字符串以避免显示 NaN
        df = df.fillna("")
        # 插入索引列
        df.insert(0, '索引', range(len(df)))
        sheet_data = []
        # 表格过长，只解析前1000行
        if df.shape[0] > 1000:
            head_rows = df.head(1000).iterrows()
        else:
            head_rows = df.iterrows()
        for index, row in head_rows:
            sheet_data.append([format_value(row[col]) for col in df.columns])
        sheet = sheet.strip()
        sheets_list.append({sheet: sheet_data})
        sheet_text = df.to_string(index=False, header=False)
        sheets_text[sheet_name] = sheet_text
    return sheets_list, sheets_text


def excel_to_text(file_path):
    # 读取Excel文件
    xls = pd.ExcelFile(file_path)
    sheets_text = {}

    # 遍历每个sheet
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        df = df.fillna("")
        df.insert(0, '索引', range(len(df)))
        sheet_text = df.to_string(index=False, header=False)
        sheets_text[sheet_name] = sheet_text

    return sheets_text


def openrouter_endpoint(system_prompt, user_prompt):
    payload = {
        "model": "gpt-4o-mini",
        "prompt": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 50
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        'https://api.openrouter.ai/v1/chat/completions',
        json=payload,
        headers=headers
    )

    return response.json()


def analysis_excel(data):
    sheets_list, sheets_text = data
    pass


if __name__ == '__main__':
    file_path = "小包VIP20240615.xlsx"
    parsed_data = read_excel(file_path)
    print(len(parsed_data))
    for data in parsed_data:
        print(data)
    
    # 示例用法
    sheets_text = excel_to_text(file_path)
    for sheet_name, text in sheets_text.items():
        print(f"Sheet: {sheet_name}")
        print(text)
        print("\n")



