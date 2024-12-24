# -*- coding:utf-8 -*-
import pandas as pd


def merge_adjacent_columns(ws):  # 合并表头相邻列值相同的单元格
    # 获取第一行的值
    first_row = [cell.value for cell in ws[1]]

    # 初始化合并的起始列和结束列
    start_col = 1
    end_col = 1

    # 遍历第一行的每一列
    for col in range(2, len(first_row) + 1):
        if first_row[col - 1] == first_row[col - 2]:
            # 如果当前列的值与前一列的值相同，更新结束列
            end_col = col
        else:
            # 如果当前列的值与前一列的值不同，合并单元格
            if start_col != end_col:
                ws.merge_cells(start_row=1, start_column=start_col, end_row=1, end_column=end_col)
            # 更新起始列和结束列
            start_col = col
            end_col = col

    # 合并最后一组相邻列
    if start_col != end_col:
        ws.merge_cells(start_row=1, start_column=start_col, end_row=1, end_column=end_col)


def format_two(records):
    express_keys = []
    result = []
    Charge_Dict = {'首重': 0, '续重': 1, '单价': 2, '0': 0, '1': 1, '2': 2}
    Goods_Dict = {'文件': 0, '包裹': 1}
    for item in records:
        # print('----', item)
        express_dict = {"时效": []}
        new_item = {}
        for key, details in item.items():
            # print(key, details)
            if key == '时效':
                result.append(item)
                continue
            if '重量' in details or isinstance(details, list):  # 格式一/四
                if not isinstance(details, list):
                    details = [details]
                new_item[key] = []
                for detail in details:
                    piece_weight = detail.get("计费单重", "1")
                    if not piece_weight:
                        piece_weight = '1'
                    charge_type = detail.get("计费类型", "")
                    if not charge_type:
                        if '-' in detail['重量'] or '+' in detail['重量']:
                            charge_type = "单价"
                        else:
                            charge_type = "首重"
                    goods_type = detail.get("货物类型", "包裹")
                    charge_num = Charge_Dict.get(charge_type, 2)
                    goods_num = Goods_Dict.get(goods_type, 1)
                    data = [detail['重量'], piece_weight, charge_num, goods_num,
                            detail['价格'], detail['操作费']]
                    new_item[key].append(data)
                    if detail.get("时效", ""):
                        if key not in express_keys:
                            express_dict["时效"].append([key, detail['时效']])
                            express_keys.append(key)
            elif '运费' in details and '计费单重' in details:  # 格式二
                new_item[key] = {}
                piece_weight = details.get("计费单重", "1")
                if not piece_weight:
                    piece_weight = '1'
                charge_type = details.get("计费类型", "")
                if not charge_type:
                    if '-' in key or '+' in key:
                        charge_type = "单价"
                    else:
                        charge_type = "首重"
                goods_type = details.get("货物类型", "包裹")
                charge_num = Charge_Dict.get(charge_type, 2)
                goods_num = Goods_Dict.get(goods_type, 1)
                new_item[key].update({'类型': [piece_weight, charge_num, goods_num],
                                      '运费': details['运费']})
            else:
                new_item[key] = details
        if new_item:
            result.append(new_item)
        if express_dict['时效']:
            result.append(express_dict)
    # 格式九，对同国家的进行合并
    merge_dict = {}
    for r in result:
        for k, v in r.items():
            if k not in merge_dict:
                merge_dict[k] = v
            else:
                if isinstance(v, list):
                    merge_dict[k].append(v[0])
    result_new = []
    for k2, v2 in merge_dict.items():
        result_new.append({k2: v2})
    return result_new


def table_info_extract(excel_extract, excel_info):
    def is_numeric_string(s):
        if not s:
            return False
        if '-' in s or '+' in s or 'Minimum' in s:
            return True
        # 匹配整数或浮点数的字符串（包括负数）
        return bool(re.match(r"^-?\d+(\.\d+)?$", s))

    if isinstance(excel_info, list):
        excel_info = excel_info[0]

    price_excel_new = {}
    weight_loc_list = [v['产品位置'] for v in excel_extract.values() if '产品位置' in v]
    weight_loc_list2 = [v['重量位置'] for v in excel_extract.values() if '重量位置' in v]
    i = 0
    for section_name, datas in excel_extract.items():
        # print(section_name, datas)
        if isinstance(datas, list):
            price_excel_new[section_name] = format_two(datas)
        else:
            price_excel_new[section_name] = []
            excel_array = np.array(list(excel_info.values())[0])
            if '分区列' in datas:  # 格式六
                print('格式六')
                # 先判断运费列的截止行索引
                freight_row_start = datas["运费列"][0] + 1
                freight_column = datas["运费列"][1]
                data = {}
                for i, p in enumerate(excel_array[freight_row_start:, freight_column]):
                    if is_numeric_string(p):
                        weight = str(excel_array[datas['重量列'][0] + 1 + i, datas['重量列'][1]]).replace(' ', '')
                        if '-' in weight or '+' in weight:
                            charge_type = 2
                        else:
                            charge_type = 0
                        country = str(excel_array[datas['分区列'][0] + 1 + i, datas['分区列'][1]])
                        piece_weight = str(excel_array[datas['计费单重列'][0] + 1 + i, datas['计费单重列'][1]])
                        price = str(excel_array[datas['运费列'][0] + 1 + i, datas['运费列'][1]])
                        handling_fee = str(excel_array[datas['操作费列'][0] + 1 + i, datas['操作费列'][1]])
                        if weight not in data:
                            data[weight] = {"类型": [piece_weight, charge_type, 1], "运费": []}
                        data[weight]["运费"].append([country, price, handling_fee])
                    else:
                        break
                for k, v in data.items():
                    price_excel_new[section_name].append({k: v})
            elif '产品位置' in datas:  # 格式七
                print('格式七')
                weight_list = []
                weight_loc = [datas['产品位置'][0], (datas['产品位置'][1] + 1)]
                if not datas['索引']:
                    if i + 1 < len(weight_loc_list):
                        weight_list = excel_array[weight_loc[0]:weight_loc_list[i + 1][0], weight_loc[1]]
                    else:
                        weight_list = excel_array[weight_loc[0]:, weight_loc[1]]
                    # print('weight_list: ', weight_list)
                for j, weight in enumerate(weight_list):
                    if not is_numeric_string(weight):
                        break
                    if '-' in str(weight) or '+' in str(weight):
                        charge_type = 2
                        piece_weight = 1
                    else:
                        charge_type = 0
                        piece_weight = 0.5
                    if "货物类型" in datas:
                        goods_type = datas['货物类型']
                    else:
                        goods_type = '文件'
                    price_piece = excel_array[weight_loc[0] + j,
                                  (weight_loc[1] + 1):(weight_loc[1] + 1 + len(datas['分区']))]
                    price_lists = [[z.strip().replace(' ', ',').replace('/', ','), str(p)] for z, p in
                                   zip(datas['分区'], price_piece)]
                    price_excel_new[section_name].append({
                        weight: {
                            "类型":[piece_weight, charge_type, goods_type],
                            "运费": price_lists
                        }
                    })
            elif '重量位置' in datas:  # 格式八
                print('格式八')
                weight_list = []
                weight_loc = [(datas['重量位置'][0] + 1), datas['重量位置'][1]]
                # print('weight_loc: ', weight_loc)
                if not datas['索引']:
                    if i + 1 < len(weight_loc_list2):
                        weight_list = excel_array[weight_loc[0]:weight_loc_list2[i + 1][0], weight_loc[1]]
                    else:
                        weight_list = excel_array[weight_loc[0]:, weight_loc[1]]
                for j, weight in enumerate(weight_list):
                    if weight and '~' in str(weight):
                        weight = str(weight).replace('~', '-')
                    if not is_numeric_string(weight):
                        break
                    if '-' in str(weight) or '+' in str(weight):
                        charge_type = 2
                        piece_weight = 1
                    else:
                        charge_type = 0
                        piece_weight = 0.5
                    if "货物类型" in datas:
                        goods_type = datas['货物类型']
                    else:
                        goods_type = '包裹'
                    price_piece = excel_array[weight_loc[0] + j,
                                  (weight_loc[1] + 1):(weight_loc[1] + 1 + len(datas['分区']))]
                    price_lists = [[z.strip().replace(' ', ',').replace('/', ','), str(p)] for z, p in
                                   zip(datas['分区'], price_piece)]
                    price_excel_new[section_name].append({
                        weight: {
                            "类型": [piece_weight, charge_type, goods_type],
                            "运费": price_lists
                        }
                    })
            else:
                print('格式五')
                # 格式五：列分区、行重量模式/行分区、列重量模式
                for w_data in datas['重量']:
                    # [重量段,计费单重,(计费类型:首重0/续重1/单价2),(货物类型:文件0/包裹1),位置索引]
                    if len(w_data) == 5:
                        weight, piece_weight, charge_type, goods_type, weight_loc = w_data
                        if section_name == '深圳ARAMEX':  # 保护一下
                            if '-' in str(weight) or '+' in str(weight):
                                charge_type = 2
                                piece_weight = 1
                            else:
                                charge_type = 0
                                piece_weight = 0.5
                    # [重量段,(货物类型:文件0/包裹1),位置索引]
                    else:
                        weight, goods_type, weight_loc = w_data
                        if '-' in str(weight) or '+' in str(weight):
                            charge_type = 2
                            piece_weight = 1
                        else:
                            charge_type = 0
                            piece_weight = 0.5
                    # price_str = []
                    if not datas['索引']:
                        price_piece = excel_array[weight_loc[0],
                                      (weight_loc[1] + 1):(weight_loc[1] + 1 + len(datas['分区']))]
                    else:
                        price_piece = excel_array[(weight_loc[0] + 1):(weight_loc[0] + 1 + len(datas['分区'])),
                                      weight_loc[1]]
                    # for p_s in price_piece:
                    #     try:
                    #         price_str.append('%.2f' % float(p_s))
                    #     except:
                    #         price_str.append(str(p_s))
                    price_lists = [[z, str(p)] for z, p in zip(datas['分区'], price_piece)]
                    price_excel_new[section_name].append({
                        weight: {
                            "类型": [piece_weight, charge_type, goods_type],
                            "运费": price_lists
                        }
                    })
        i += 1
    return price_excel_new


# 1_数达系统报价上传模板
def output_sheet_tmpl1(price_extract, price_excel_info):
    def convert_nine_to_three(input_data):
        transformed_data = []

        for detail in input_data:
            if not "时效" in detail:
                # Handle the weight and pricing information
                for country, pricing_info in detail.items():
                    for info in pricing_info:
                        weight, billing_weight, billing_type, package_type, price, handling_fee = info
                        transformed_detail = {
                            weight: {
                                "类型": [billing_weight, billing_type, package_type],
                                "运费": [[country, price, handling_fee]]
                            }
                        }
                        transformed_data.append(transformed_detail)
            else:
                # Handle the time efficiency information
                transformed_data.append(detail)

        return transformed_data

    product_list = {}
    result = ""

    for i, price_sheet in enumerate(price_extract):
        print(price_sheet)
        sheet_name = list(price_excel_info[i].keys())[0]
        try:
            multi_flag = False  # 单sheet是否含有多个产品
            if len(list(price_sheet.keys())) > 1:
                multi_flag = True

            for section_name, records in price_sheet.items():  # 可能多产品
                # 单产品一个表格
                sheet_data = {}
                express_timeliness = []
                express_keys = []
                for item in records:
                    if '时效' in item:
                        details = item.pop('时效')
                        for detail in details:
                            timeliness = detail[1].split('-')
                            if timeliness:
                                if len(timeliness) == 2:
                                    start_time, end_time = timeliness[0], [1]
                                else:
                                    start_time, end_time = timeliness[0], timeliness[0]
                            else:
                                start_time, end_time = '', ''
                            express_key = section_name + detail[0]
                            if express_key not in express_keys:
                                express_timeliness.append([
                                    detail[0],
                                    start_time,
                                    end_time,
                                    detail[0],
                                    section_name
                                ])
                                express_keys.append(express_key)
                if express_timeliness:
                    df1 = pd.DataFrame(express_timeliness,
                                       columns=["分区名称", "时效天数", "时效天数", "国家", "产品名称"])
                    sheet_data["分区模板"] = df1

                product_0 = records[0]  # 重量字典或者国家列表
                price_0 = list(product_0.values())[0] # 字典或者列表
                if isinstance(price_0, list):  # 格式九
                    records = convert_nine_to_three(records)

                print(section_name, records)
                rows = []
                header_init = True
                columns = []

                country_list = []
                # 格式三补全所有国家
                seen = set()
                for item in records:
                    for details in item.values():
                        if '运费' in details:
                            for price in details["运费"]:
                                if price[0] not in seen:
                                    seen.add(price[0])
                                    country_list.append(price[0])
                # Create a dictionary to hold the merged results
                merged_data = defaultdict(lambda: {"类型": None, "运费": []})

                # Iterate through the list of shipments
                for item in records:
                    for weight_range, details in item.items():
                        type_tuple = tuple(details["类型"])
                        key = (weight_range, type_tuple)

                        if merged_data[key]["类型"] is None:
                            merged_data[key]["类型"] = details["类型"]

                        merged_data[key]["运费"].extend(details["运费"])
                # Convert the merged data back to the desired format
                records = [{weight_range: {"类型": details["类型"], "运费": details["运费"]}}
                           for (weight_range, _), details in merged_data.items()]

                for item in records:
                    for key, details in item.items():
                        if '运费' in details:  # 格式三
                            if header_init:
                                columns = ["重量 (KG)", "计费单重 (KG)", "计费类型", "货物类型"]
                                rows = [
                                    ["重量 (KG)", "计费单重 (KG)", "计费类型", "货物类型"],
                                ]
                                for country in country_list:
                                    columns.append(country)  # 添加表头分区
                                    rows[0].append("价格")
                                    if len(details["运费"][0]) == 3:
                                        columns.append(country)  # 有操作费，再添加表头分区
                                        rows[0].append("操作费")

                                header_init = False
                            goods_type = details.get("货物类型", "包裹")
                            piece_weight = details["类型"][0]
                            Charge_Dict = {0: '首重', 1: '续重', 2: '单价'}
                            charge_type = Charge_Dict[details["类型"][1]]
                            Goods_Dict = {0: '文件', 1: '包裹'}
                            if len(details["类型"]) == 3:
                                goods_type = Goods_Dict[details["类型"][2]]
                            row = [
                                key,
                                piece_weight,
                                charge_type,
                                goods_type,
                            ]
                            for _ in country_list:
                                row.append(None)
                                if len(details["运费"][0]) == 3:
                                    row.append(None)
                            rows.append(row)
                            for price in details["运费"]:
                                country_index = country_list.index(price[0])
                                if len(details["运费"][0]) == 2:
                                    row[4 + country_index] = price[1]
                                elif len(details["运费"][0]) == 3:
                                    row[4 + country_index * 2] = price[1]
                                    row[4 + country_index * 2 + 1] = price[2]
                        else:
                            row = {field: value for field, value in details.items()}
                            rows.append(row)

                df2 = pd.DataFrame(rows, columns=columns)
                if multi_flag:
                    section_name = sheet_name + ' ' + section_name
                sheet_data[section_name] = df2
                product_list[section_name] = sheet_data

            result += "sheet %s 报价内容提取成功\n" % sheet_name
        except Exception as e:
            result += "sheet %s 暂不支持解析，请联系售后人员\n" % sheet_name
            print('Sheet %d error: ' % i, e)
    return result, product_list


# 2_Parcels系统报价模版
def output_sheet_tmpl2(price_extract, price_excel_info):
    def convert_three_to_nine(input_data):
        transformed_data = []

        country_dict = {}
        for detail in input_data:
            if not "时效" in detail:  # 重量字典
                # Handle the weight and pricing information
                for weight, pricing_info in detail.items():
                    for info in pricing_info['运费']:
                        if len(info) == 2:
                            country_weight = [weight] + pricing_info['类型'] + info[1:] + ['']
                        else:
                            country_weight = [weight] + pricing_info['类型'] + info[1:]
                        if info[0] not in country_dict:
                            country_dict[info[0]] = [country_weight]
                        else:
                            country_dict[info[0]].append(country_weight)
            else:
                # Handle the time efficiency information
                transformed_data.append(detail)
        for k, v in country_dict.items():
            transformed_data.append({k: v})
        return transformed_data

    product_list = {}
    result = ""

    for i, price_sheet in enumerate(price_extract):
        sheet_name = list(price_excel_info[i].keys())[0]
        try:
            multi_flag = False  # 单sheet是否含有多个产品
            if len(list(price_sheet.keys())) > 1:
                multi_flag = True

            for section_name, records in price_sheet.items():  # 可能多产品
                # 单产品一个表格
                sheet_data = {}
                express_timeliness = []
                express_keys = []
                for item in records:
                    if '时效' in item:
                        details = item.pop('时效')
                        for detail in details:
                            timeliness = detail[1].split('-')
                            if timeliness:
                                if len(timeliness) == 2:
                                    start_time, end_time = timeliness[0], [1]
                                else:
                                    start_time, end_time = timeliness[0], timeliness[0]
                            else:
                                start_time, end_time = '', ''
                            express_key = section_name + detail[0]
                            if express_key not in express_keys:
                                express_timeliness.append([
                                    detail[0],
                                    start_time,
                                    end_time,
                                    detail[0],
                                    section_name
                                ])
                                express_keys.append(express_key)
                if express_timeliness:
                    df1 = pd.DataFrame(express_timeliness,
                                       columns=["分区名称", "时效天数", "时效天数", "国家", "产品名称"])
                    sheet_data["分区模板"] = df1

                product_0 = records[0]  # 重量字典或者国家列表
                price_0 = list(product_0.values())[0]  # 字典或者列表
                if isinstance(price_0, dict):  # 格式三
                    records = convert_three_to_nine(records)

                print(section_name, records)
                rows = []
                header_init = True
                columns = []

                # 格式九补全所有重量
                weight_ranges = set()
                for country_data in records:  # 提取所有重量范围
                    for country, weights in country_data.items():
                        for weight in weights:
                            weight_ranges.add(weight[0])

                # 对重量范围进行排序
                sorted_weight_ranges = sorted(weight_ranges, key=lambda x: float(re.split(r'[+-]', x)[0]))
                sorted_weight_info = {}
                # 补齐每个国家的重量范围
                for country_data in records:
                    for country, weights in country_data.items():
                        weight_dict = {weight[0]: weight for weight in weights}
                        new_weights = []
                        for weight_range in sorted_weight_ranges:
                            if weight_range in weight_dict:
                                new_weights.append(weight_dict[weight_range])
                                if weight_range not in sorted_weight_info:
                                    sorted_weight_info[weight_range] = [weight_dict[weight_range][1],
                                                                        weight_dict[weight_range][2]]
                            else:
                                # 使用默认值补齐缺失的重量范围
                                new_weights.append([weight_range, '', '', '', '', ''])
                        country_data[country] = new_weights

                for item in records:
                    for key, details in item.items():  # 格式九
                        if header_init:
                            columns = ["分区名称", "体积系数", "计泡方式", "计泡百分比", "报价名称"]
                            rows = [
                                ["分区名称", "体积系数", "计泡方式", "计泡百分比", "报价名称"],
                            ]
                            for weight in sorted_weight_ranges:
                                columns.extend([weight] * 3)  # 添加表头分区
                                if sorted_weight_info[weight][1] == 0:  # 首重
                                    rows[0].append('首重/%sKG' % sorted_weight_info[weight][0])
                                    rows[0].append('续重/0.0KG')
                                    rows[0].append('处理费')
                                else:
                                    rows[0].append('首重/0.0KG')
                                    rows[0].append('续重/%sKG' % sorted_weight_info[weight][0])
                                    rows[0].append('处理费')
                            header_init = False
                        row = [[key, '6000.0', '全泡', '', '公示价'],
                               [key, '6000.0', '全泡', '', '销售底价'],
                               [key, '6000.0', '全泡', '', '成本价']]
                        row_c = []
                        for detail in details:
                            if detail[2] == 0:  # 首重
                                row_c.extend([detail[4], '0.00', detail[5]])
                            elif detail[2] in [1, 2]:  # 续重/单价
                                row_c.extend(['0.00', detail[4], detail[5]])
                            else:
                                row_c.extend(['', '', ''])

                        for i in range(3):
                            row[i].extend(row_c)
                            rows.append(row[i])

                df2 = pd.DataFrame(rows, columns=columns)
                if multi_flag:
                    section_name = sheet_name + ' ' + section_name
                sheet_data[section_name] = df2
                product_list[section_name] = sheet_data

            result += "sheet %s 报价内容提取成功\n" % sheet_name
        except Exception as e:
            result += "sheet %s 暂不支持解析，请联系售后人员\n" % sheet_name
            traceback.print_exc()
            print('Sheet %d error: ' % i, e)
    return result, product_list


def export_xlsx(product_list):
    for name, sheet_data in product_list.items():
        output_file = "-".join(['报价上传表', name + '.xlsx'])
        with pd.ExcelWriter(output_file) as writer:
            for sheet_name, df in sheet_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                if worksheet['A1'].value == '重量 (KG)':
                    # 合并单元格
                    worksheet.merge_cells('A1:A2')
                    worksheet.merge_cells('B1:B2')
                    worksheet.merge_cells('C1:C2')
                    worksheet.merge_cells('D1:D2')
                    worksheet['A1'] = '重量 (KG)'
                    worksheet['B1'] = '计费单重 (KG)'
                    worksheet['C1'] = '计费类型'
                    worksheet['D1'] = '货物类型'
                    merge_adjacent_columns(worksheet)
                elif worksheet['B1'].value == '体积系数':
                    worksheet.merge_cells('A1:A2')
                    worksheet.merge_cells('B1:B2')
                    worksheet.merge_cells('C1:C2')
                    worksheet.merge_cells('D1:D2')
                    worksheet.merge_cells('E1:E2')
                    worksheet['A1'] = '分区名称'
                    worksheet['B1'] = '体积系数'
                    worksheet['C1'] = '计泡方式'
                    worksheet['D1'] = '计泡百分比'
                    worksheet['E1'] = '报价名称'
                merge_adjacent_columns(worksheet)
            workbook = writer.book
            workbook._sheets.sort(key=lambda ws: ws.title != "分区模板")
            

if __name__ == '__main__':
    
    """
    5. 格式五：  # 已转为三
    {
    产品名称: {
        "索引": 索引类型,
        "分区"：[国家/分区,...],
        "重量"：[[重量段,计费单重,(计费类型:首重0/续重1/单价2),(货物类型:文件0/包裹1),位置索引],...]
        }
    }
    6. 格式六：  # 已转为三
    {
    产品名称:
        {
        "分区列": 分区列,
        "重量列": 重量列,
        "计费单重列": 计费单重列,
        "运费列": 运费列,
        "操作费列": 操作费列,
        }
    }
    7. 格式七：  # 已转为三
    {
    产品名称: {
        "索引": 索引类型,
        "分区": [
        国家/分区
        ],
        "产品位置": 位置索引,
        "货物类型": 货物类型
    },
    }
    8. 格式八：  # 已转为三
    {
    产品名称: {
        "索引": 索引类型,
        "分区": [国家/分区,...],
        "重量位置": 位置索引
    },
    }
    1. 格式一： # 已转为九
    {
    产品名称: [
        {
        国家: {
            "重量": (计费重量段),
            "计费单重": (计费单重，如无则为空),
            "计费类型": (计费类型，如无则为空),
            "货物类型": (货物类型，默认值为'包裹'),
            "价格": (运费价格),
            "操作费": (处理费),
            "时效": (参考时效)
        }
        }
    ]
    }
    2. 格式二： # 已转为三
    {
    产品名称: [
        {
        重量: {
            "计费单重": (计费单重，如无则为空),
            "计费类型": (计费类型，如无则为空),
            "货物类型": (货物类型，默认值为'包裹'),
            "运费": [[(国家/分区), (价格), (操作费)], ]
        }
        },
        {"时效": [[国家/分区, 时效天数],]}
    ]
    }
    4. 格式四：  # 已转为九
    {
    产品名称: [
        {
        国家: [{
            "重量": (计费重量段),
            "计费单重": (计费单重，如无则为空),
            "计费类型": (计费类型，如无则为空),
            "货物类型": (货物类型，默认值为'包裹'),
            "价格": (运费价格),
            "操作费": (处理费),
            "时效": (参考时效)
        }]
        }
    ]
    }
    5. 格式六：  # 已转为三
    {
    产品名称: [
        {
        "国家": (分区),
        "重量": (计费重量段),
        "计费单重": (计费单重),
        "计费类型": (计费类型),
        "货物类型": (货物类型),
        "价格": (运费价格),
        "操作费": (操作费),
        }
    ]
    }
    格式三：
    {
    产品名称: [
        {
        重量: {
            "类型": [(计费单重),(计费类型:首重0/续重1/单价2),(包裹类型:文件0/包裹1)], # 可选
            "运费": [[(国家/分区), (价格), (操作费)],]
        }
        },
        {"时效": [[国家/分区, 时效天数],]}
    ]
    }
    格式九：
    {
    产品名称: [
        {
        国家: [[(重量), (计费单重), (计费类型:首重0/续重1/单价2), (包裹类型:文件0/包裹1), (价格), (操作费)],]]
        },
        {"时效": [[国家/分区, 时效天数],]}
    ]
    }
    """