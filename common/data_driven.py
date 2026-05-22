import openpyxl
def read_excel(file_path,sheet_name):
    #读取excel文件
    wb=openpyxl.load_workbook(file_path)
    #读取excel文件里面的sheet
    sheet_data=wb[sheet_name]
    #查看最大行数
    row_max=sheet_data.max_row
    #查看最大行数
    col_max=sheet_data.max_column
    # print(f"最大行数:{row_max}")
    # print(f"最大列数:{col_max}")
    #遍历行数据
    total=[]
    for line in range(2,row_max+1):
        line_data=[]
        #遍历列数据
        for col in range(1,col_max+1):
            #遍历每个单元格的数据,cell,读取数据
            cell_data=sheet_data.cell(row=line,column=col)
            line_data.append(cell_data.value)
        #     print(cell_data.value)
        # print(line_data)
        total.append(line_data)
        print(total)
    return total

# test_data = [
#     ["这是用例1", "test_new_9999", 123456, "200", '{"code":"200","msg":"注册成功1"}'],
#     ["这是用例2", "test_new_10000", 123456, "200", '{"code":"200","msg":"注册成功1"}'],
#     ["这是用例3", "test_new_10001", 123456, "200", '{"code":"200","msg":"注册成功1"}'],
#     ["这是用例4", "test_new_10002", 123456, "200", '{"code":"200","msg":"注册成功1"}'],
#     ["这是用例5", "test_new_10003", 123456, "200", '{"code":"200","msg":"注册成功1"}'],
# ]
if __name__ == '__main__':
    read_excel(file_path=r"E:\soft\test.xlsx",sheet_name="Sheet1")