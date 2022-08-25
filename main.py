import argparse
import os
import time

import cv2 as cv
import numpy as np
from cvhelpers.detection.bbox import *
import pandas as pd
import miner

import config
import toExcel
from cropping import ConnectedComponentsCropper as CompnentsCropper
from matching import *

def textDetToBBox(det):
    det = np.array(det)
    x_min = det[:, 0].min()
    x_max = det[:, 0].max() 
    y_min = det[:, 1].min()
    y_max = det[:, 1].max()  
    return BBox((x_min, y_min, x_max, y_max), False)

def checkTextAffinity(crops, det):
    bbox_det = textDetToBBox(det)
    index = -1
    best = 0
    curr = 0
    for crop in crops:
        bbox_crop = BBox(crop, xywh=False)
        score = IoU(bbox_crop, bbox_det)
        if score > best:
            index = curr
            best = score
        curr = curr + 1
    return index

#input:
#   export = [keyword,raw_ocr,func,part_no]
def unique_filter(export):
    unique = set()
    output = []
    for keyword,raw_ocr,func,part_no in export:
        pn_str = str(part_no)
        if pn_str not in unique:
            unique.add(pn_str)
            output.append([keyword,raw_ocr,func,part_no])
        else:
            for i in range(len(output)):
                if part_no == output[i][3] and len(keyword) > len(output[0]):
                    output[i][0] = keyword
                    output[i][1] = raw_ocr
                    output[i][2] = func
    return output

def result_unique_filter(result):
    unique = set()
    output = []
    for keyword,raw_ocr,func,part_no,page in export:
        pn_str = str(part_no)
        if pn_str not in unique:
            unique.add(pn_str)
            output.append([keyword,raw_ocr,func,part_no,page])
        else:
            for i in range(len(output)):
                if part_no == output[i][3] and len(keyword) > len(output[0]):
                    output[i][0] = keyword
                    output[i][1] = raw_ocr
                    output[i][2] = func
    return output
"""

Notice: Multiscaling here was not fully tested. Score may be not suitable for EasyOCR.

"""
def analyseSinglePage(fname,pd_excel):

    print("\nAnalyzing: {}".format(fname))
    density = config.INITIAL_DENSITY
    iname = fname[:-4]+".jpg"
   
    # Convert single-page PDF to picture
    cml = "convert -density {} -quality {} {} {}".format(density, 100, fname, iname)
    os.system(cml)
    image = cv.imread(iname)
    if image is None:
        print("No image input , skip to next page!")
        return None
        # crop image patches
    cropper = CompnentsCropper(image)
    crops = cropper.crop()
        # Inference and compare
    text_dets = miner.extractWord(fname,image)

    # Divide recognized texts into cropped patches
    affinity = []
    for crop in crops:
        affinity.append((crop, []))
    for det in text_dets:
        bbox = textDetToBBox(det[0])
        index = checkTextAffinity(crops, det[0])
        if index != -1:
            affinity[index][1].append((bbox, det[1]))
    # Match OCR results with HWDB and match part name to part number
    result = []
    matcher = Matcher(image, [(textDetToBBox(det[0]), det[1]) for det in text_dets])
    for crop, text_dets in affinity:
        for det in text_dets:
            bbox, text = det
            #cv.rectangle(image,(bbox.min_x,bbox.min_y) , (bbox.max_x,bbox.max_y),color=(0,0,255),thickness = 1,lineType=cv.LINE_AA)
            keyword, conf = kword_match(text, pd_excel)
            if conf > 0.5:
                part_nos,func,chip_idx = matcher.matchREFDES(bbox , keyword ,text,pd_excel, image)
                cv.rectangle(image,(bbox.min_x,bbox.min_y) , (bbox.max_x,bbox.max_y),color=(0,0,255),thickness=1,lineType=cv.LINE_AA)
                if part_nos != None:
                    result.append([keyword, text, func,part_nos])
            else:
                continue
    cv.imwrite(fname[:-4]+"_croped.jpg",image)
    result = unique_filter(result)
    return result 

def parse_args():
    parser = argparse.ArgumentParser() 
    parser.add_argument("input", help="""Input PDF file name""")
    parser.add_argument("-p", "--pages", default=None,
        help="""Indicate page range. use [a,b,...] for indicating a set of page 
        or "(a,b)" (please use quotation marks) to indicate a page range (both
        side inclusive).""") 
    return parser.parse_args()


if __name__ == "__main__":
    start_time = time.time()
    args = parse_args()
    pdf_content = args.input
    pdf_name = pdf_content.split("/")[-1]
    dir_name = "exp_" + pdf_name[0:4] + str(int(time.time()))
    os.system("mkdir {}".format(dir_name))
    os.chdir(dir_name)
    if config.PDFTK_INSTALLATION_TYPE == "PackageMgr":
        os.system("pdftk ../{} burst".format(pdf_content))
    if config.PDFTK_INSTALLATION_TYPE == "StandaloneJar":
        os.system("java -jar ../pdftk-all.jar ../{} burst".format(pdf_content))
    if config.PDFTK_INSTALLATION_TYPE == "NativeImage":
        os.system("../pdftk ../{} burst".format(pdf_content))
    
    if args.pages is None:
        # Detect in all pages
        pdf_list = []
        for fname in os.listdir("."):
            if fname[-4:] != ".pdf":
                continue
            else:
                pdf_list.append(fname)
        pdf_list = sorted(pdf_list, key=lambda x: int(x[3:-4]))
    else:
        # Detect in a selected set of pages
        pages_indicator = args.pages.strip()
        if pages_indicator[0] == "(":
            pages_indicator = [int(str) for str in pages_indicator[1:-1].split(",")]
            pages_in_dataset = list(range(pages_indicator[0], pages_indicator[-1] + 1))
        elif pages_indicator[0] == "[":
            pages_in_dataset = [int(str) for str in pages_indicator[1:-1].split(",")]
        else:
            print("Wrong page indicator format.")
            exit(-1)
        pdf_list = ["pg_{:0>4d}.pdf".format(x) for x in pages_in_dataset]
    
    pages_in_dataset = []
    results = []
    pd_excel = pd.read_excel("../hw-dataset.xlsx") 
    pdfKeyword = pdf_name[0:3] # pdf Keyword , use the first three words of pdfname
    for fname in pdf_list:
        pages_in_dataset.append(fname)
        s_time = time.time()
        results.append(analyseSinglePage(fname,pd_excel))
        print("Analyse time: %.0f seconds"%(time.time()-s_time))
    
    export  = []
    os.chdir("..")
    det_list = []
    with open(str(dir_name) + "/" + str(pdf_name) + ".txt","a+") as log:
        log.writelines("{:<20s} | {:<20s} | {:<10s} | {:<10s} ".format("KeyWord", "Part name", "function","Part No.\n"))
        log.writelines("-------------------- | -------------------- | ---------- | -----------\n")
    for page, result in zip(pages_in_dataset, results):
        print("==== Page {} ====".format(page))
        print("{:<20s} | {:<20s} | {:<10s} | {:<10s} ".format("KeyWord", "Part name", "function","Part No."))
        print("-------------------- | -------------------- | ---------- | -----------")
        if result == None:
            continue
        with open(str(dir_name) + "/" + str(pdf_name) + ".txt","a+") as log:
            log.writelines("result of {} :\n".format(str(page)) )
            for keyword, raw_ocr,func,part_no in result:
                export.append([keyword,raw_ocr,func,part_no,page[:7]])
                det_list.append(keyword)
                print("{:<20s} | {:<20s} | {:<10s} | {}".format(keyword, raw_ocr, func, ', '.join(part_no) ))
                log.writelines("{:<20s} | {:<20s} | {:<10s} | {}".format(keyword, raw_ocr,func, ', '.join(part_no) ) + "\n")
    
    toExcel.export_excel(result_unique_filter(export),dir_name+ "/" + pdf_name)
    #check if there are missed part_name in excel
    '''
    keyword_list = []
    for i in range(len(pd_excel)):
        true_pdf_keyWord = pd_excel["pdf keyWord"][i]
        if true_pdf_keyWord == pdfKeyword:
            keyword_list.append([pd_excel[config.KEYWORD][i] , 0])
    for i in range(len(keyword_list)):
        if keyword_list[i][0] in det_list:
            keyword_list[i][1] += 1
    cnt = 0
    with open(str(dir_name) + "/" + str(pdf_name) + ".txt","a+") as log:
        for keyword,num in keyword_list:
            if num == 0:
                cnt += 1
                print("Part name : {} not detected. ".format(keyword))
                log.writelines("Missed part name : {} \n".format(keyword))
        print("Missed part name rate: {:.2%}".format(cnt/len(keyword_list)))
        log.writelines("Missed part name rate: {:.2%}\n".format(cnt/len(keyword_list)))
        print("All spend time: %.0f mins" % ((time.time()-start_time)/60) )
        log.writelines("All spend time: %.0f mins \n" % ((time.time()-start_time)/60))
    '''