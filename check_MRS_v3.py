#coding:utf-8

import xml.etree.ElementTree as ET
import os
import gzip
import pandas as pd

modulus = [0.001,0.0035,0.0075,0.015,0.025,0.035,0.045,0.055,0.065,0.075,0.085,0.095,
           0.11,0.13,0.15,0.17,0.19,0.225,0.275,0.325,0.375,0.425,0.475,0.55,0.65,0.75,0.85,0.95]

def cellId_cal(num):
    num = int(num)
    divNum = divmod(num, 256)
    cellId = str(divNum[0]) + "-" + str(divNum[1])
    return cellId

def mr_cal(str):
    mr_lst = str.split(" ")
    mr_lst = [int(x) for x in mr_lst]
    cover = mr_lst[8:]                              #前8位为弱覆盖采样点
    if sum(mr_lst) == 0:
        return "#DIV/0!"
    else:
        cover_rate = sum(cover) / sum(mr_lst)
        return cover_rate

def phr_cal(str):
    phr_lst = str.split(" ")
    phr_lst = [int(x) for x in phr_lst]
    less_than_zero = phr_lst[0:23]                              #前23位为低于0采样点
    if sum(phr_lst) == 0:
        return "#DIV/0!"
    else:
        less_than_zero_rate = sum(less_than_zero) / sum(phr_lst)    #低于0采样点除以总采样点
        return less_than_zero_rate

def plr_cal(str):
    packetLoss = 0
    plr_lst = str.split(" ")
    plr_lst = [int(x) for x in plr_lst]
    for i, j in zip(plr_lst, modulus):
        packetLoss += i*j
    if sum(plr_lst) == 0:
        return "#DIV/0!"
    else:
        packetLoss_rate = 100 * packetLoss / sum(plr_lst)
        return packetLoss_rate

class MrsData:
    def __init__(self,xml_path):
        self.tree = ET.parse(xml_path)
        self.MR_attrib = self.tree.findall(".//measurement[@mrName='MR.RSRP']/object")
        self.MR_data = self.tree.findall(".//measurement[@mrName='MR.RSRP']/object/")
        self.PHR_attrib = self.tree.findall(".//measurement[@mrName='MR.PowerHeadRoom']/object")
        self.PHR_data = self.tree.findall(".//measurement[@mrName='MR.PowerHeadRoom']/object/")
        self.PLR_UL_attrib = self.tree.findall(".//measurement[@mrName='MR.PacketLossRateULQci1']/object")
        self.PLR_UL_data = self.tree.findall(".//measurement[@mrName='MR.PacketLossRateULQci1']/object/")
        self.PLR_DL_attrib = self.tree.findall(".//measurement[@mrName='MR.PacketLossRateDLQci1']/object")
        self.PLR_DL_data = self.tree.findall(".//measurement[@mrName='MR.PacketLossRateDLQci1']/object/")
        self.time = self.tree.findall("./fileHeader")

    def get_mr_data(self,):
        dict_res = {}
        for i, j in zip(self.MR_attrib, self.MR_data):
            data = j.text                    #data type :<class 'str'>
            id = i.attrib                    #id type : dict
            dict_res[id['id']] = data        #添加至字典

        dict_result = {}
        for key, value in dict_res.items():        #遍历字典,将原始数据转化成cellId和覆盖率
            cellId = cellId_cal(key)
            cover_rate = mr_cal(value)
            dict_result[cellId] = cover_rate
        return dict_result

    def get_phr_data(self,):
        dict_res = {}
        for i, j in zip(self.PHR_attrib, self.PHR_data):
            data = j.text                    #data type :<class 'str'>
            id = i.attrib                    #id type : dict
            dict_res[id['id']] = data        #添加至字典

        dict_result = {}
        for key, value in dict_res.items():        #遍历字典,将原始数据转化成cellId和覆盖率
            cellId = cellId_cal(key)
            phr_rate = phr_cal(value)
            dict_result[cellId] = phr_rate
        return dict_result

    def get_PLR_UL(self,):
        dict_res = {}
        for i, j in zip(self.PLR_UL_attrib, self.PLR_UL_data):
            data = j.text                    #data type :<class 'str'>
            id = i.attrib                    #id type : dict
            dict_res[id['id']] = data        #添加至字典

        dict_result = {}
        for key, value in dict_res.items():
            cellId = cellId_cal(key)
            plr_ul_rate = plr_cal(value)
            dict_result[cellId] = plr_ul_rate
        return dict_result

    def get_PLR_DL(self,):
        dict_res = {}
        for i, j in zip(self.PLR_DL_attrib, self.PLR_DL_data):
            data = j.text
            id = i.attrib
            dict_res[id['id']] = data

        dict_result = {}
        for key, value in dict_res.items():
            cellId = cellId_cal(key)
            plr_dl_rate = plr_cal(value)
            dict_result[cellId] = plr_dl_rate
        return dict_result

    def get_time(self,):
        return self.time[0].attrib["reportTime"]

def un_gz(file_name):
    f_name = file_name.replace(".gz", "")
    g_file = gzip.GzipFile(file_name)
    open(f_name, "wb").write(g_file.read())       #生成一个新的文件，将原始.gz文件内容写入
    g_file.close()
    return f_name

output_cols = ["reportTime", 'cellId', "MR覆盖率", "PHR低于0占比", "上行丢包率", "下行丢包率"]

def main():
    path = os.getcwd()
    dirs = os.listdir(path)                                          #获取当前文件夹下文件路径，带文件后缀。类型为list，元素类型为str。
    file_path = []
    for i in dirs:
        if ".gz" in i and "MRS" in i:
            file = un_gz(i)                                         #将解压的新文件赋值给file
            file_path.append(file)

    df_empty = pd.DataFrame(columns=output_cols)
    if len(file_path) == 0:
        input("没有MRS压缩(.gz)文件，请放入MRS压缩文件:")
    else:
        index = 0
        for file in file_path:
            mrsData = MrsData(file)
            time, mr_dict, phr_dict, PLR_UL, PLR_DL = mrsData.get_time(), mrsData.get_mr_data(), mrsData.get_phr_data(), mrsData.get_PLR_UL(), mrsData.get_PLR_DL()
            for key in mr_dict:
                insertRow = []
                insertRow.append(time)
                insertRow.append(key)
                insertRow.append(mr_dict[key])
                insertRow.append(phr_dict[key])
                insertRow.append(PLR_UL[key])
                insertRow.append(PLR_DL[key])
                df_empty.loc[index] = tuple(insertRow)
                index += 1
            os.remove(file)
    df_empty.to_excel("check_result.xlsx", index=False)

main()