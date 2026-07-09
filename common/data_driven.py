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
    #遍历行数据
    total=[]
    for line in range(2,row_max+1):
        line_data=[]
        #遍历列数据
        for col in range(1,col_max+1):
            #遍历每个单元格的数据,cell,读取数据
            cell_data=sheet_data.cell(row=line,column=col)
            line_data.append(cell_data.value)
        total.append(line_data)
    return total
