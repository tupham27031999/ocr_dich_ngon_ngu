from typing import Any
import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw,ImageFont, ImageDraw
import os
from support_main.lib_main import edit_csv_tab,remove
import path
import shutil
import time




path_phan_mem = path.path_phan_mem
path_close = remove.tao_folder(path_phan_mem + "/close")
path_ngon_ngu = remove.tao_folder(path_phan_mem + "/ngon_ngu")
print(path_phan_mem + "/input_ocr")
path_input = remove.tao_folder(path_phan_mem + "/input_ocr")
path_output = remove.tao_folder(path_phan_mem + "/output_ocr")

remove.remove_all_in_folder(path_close)
remove.remove_all_in_folder(path_input)
# remove.remove_all_in_folder(path_output)



list_nguon_ngu = ["ch","ch_tra","en","fr","ar","es","pt","ru","ge","kr","jp","it","hi","ug",\
                  "fa","ur","oc","mr","ne","rs_cyrillic","rs_latin","bg","uk",'be',"te","kn",\
                  "ta","mg","bm","ku_cent","od","th"]

ngon_ngu = "en"
ocr = PaddleOCR(use_angle_cls = True,lang = ngon_ngu)
time_check = 0
# Define the text and its properties
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 1
color = (255, 0, 0)  # Blue color in BGR
thickness = 2


def check_img():
    global ngon_ngu,ocr,time_check
    ds_ngon_ngu = os.listdir(path_ngon_ngu)
    if len(ds_ngon_ngu) != 0:
        if ngon_ngu != ds_ngon_ngu[0]:
            for i in range(0,len(list_nguon_ngu)):
                if ds_ngon_ngu[0] == list_nguon_ngu[i]:
                    ngon_ngu = ds_ngon_ngu[0]
                    ocr = PaddleOCR(use_angle_cls = True,lang = ngon_ngu)
    ds_img = os.listdir(path_input)
    if len(ds_img) != 0:
        if time_check == 0:
            time_check = time.time()
        if  time_check != 0 and time.time() - time_check > 1:
            time_check = 0
            name_csv = str(ds_img[0]).split(".")[0]
            edit_csv_tab.new_csv_replace(path_output + "/" + name_csv + ".csv",["Name","Text","Judgement","X1","Y1","X2","Y2"])
            for i1 in range(0,len(ds_img)):
                result = ocr.ocr(path_input + "/" + ds_img[i1],cls = True)
                img = cv2.imread(path_input + "/" + ds_img[i1])
                if len(result) != 0:
                    if str(result[0]) != "None":
                        result = result[0]
                        for i in range(0,len(result)):
                            x1 = min(int(result[i][0][0][0]),int(result[i][0][1][0]),int(result[i][0][2][0]),int(result[i][0][3][0]))
                            y1 = min(int(result[i][0][0][1]),int(result[i][0][1][1]),int(result[i][0][2][1]),int(result[i][0][3][1]))
                            x2 = max(int(result[i][0][0][0]),int(result[i][0][1][0]),int(result[i][0][2][0]),int(result[i][0][3][0]))
                            y2 = max(int(result[i][0][0][1]),int(result[i][0][1][1]),int(result[i][0][2][1]),int(result[i][0][3][1]))
                            text = str(result[i][1][0])
                            phan_tram = str(int(float(result[i][1][1])*10000)/100)
                            # Add text to the image
                            cv2.rectangle(img, (x1,y1), (x2,y2),(255,0,255),1)
                            size_text = (x2-x1)*0.003
                            cv2.putText(img, phan_tram + "%", (x1,int(y1-22*size_text)),cv2.FONT_HERSHEY_DUPLEX, size_text, (255, 0, 255))
                            cv2.putText(img, text, (x1,y1),cv2.FONT_HERSHEY_DUPLEX, size_text, (255, 0, 255))
                            edit_csv_tab.append_csv(path_output + "/" + name_csv + ".csv",[ds_img[i1],text,phan_tram,x1,y1,x2,y2])
                # Save or display the image
                cv2.imwrite('output_image.jpg', img)
                shutil.copy('output_image.jpg',path_output + "/" + ds_img[i1])
                remove.remove_file(path_input + "/" + ds_img[0])
while True:
    close_window = os.listdir(path_close)
    if len(close_window) != 0:
        break
    check_img()
