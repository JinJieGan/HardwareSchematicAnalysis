import cv2 as cv
import numpy as np
import math
import config
import re

from cvhelpers.detection.bbox import BBox

# match input keyword from excel with extracted character in pdf.
def kword_match(det_text,pd_excel):
    keywords = pd_excel[config.KEYWORD]
    result = None
    conf = 0
    text_no_blank = det_text.replace(" ","")
    
    for keyword in keywords:
        keyword_no_blank = keyword.replace(" ","")
        if keyword not in config.MANUAL_KEYWORDS and re.search(keyword_no_blank,text_no_blank,flags=re.I):
            result = keyword
            #print(keyword,det_text)
            conf = 1
    return result,conf

def same_box(box1,box2):
    b1x1 = box1.min_x
    b1x2 = box1.max_x
    b1y1 = box1.min_y
    b1y2 = box1.max_y
    b2x1 = box2.min_x
    b2x2 = box2.max_x
    b2y1 = box2.min_y
    b2y2 = box2.max_y
    if b1x1 == b2x1 and b1x2 == b2x2 and b1y1 == b2y1 and b1y2 == b2y2:
        return True
    return False


def merge_boxes(merged_big_box,self_contours):
    final_boxes = merged_big_box
    for contour in self_contours:
        cx1 = contour.min_x
        cx2 = contour.max_x
        cy1 = contour.min_y
        cy2 = contour.max_y
        is_inner_box = False
        for big_box in merged_big_box:
            bx1 = big_box.min_x
            bx2 = big_box.max_x
            by1 = big_box.min_y
            by2 = big_box.max_y
            if cx1>=bx1 and cx2<=bx2 and cy1>=by1 and cy2 <= by2:
                is_inner_box = True
                continue
        if is_inner_box == False:
            final_boxes.append(contour)
    return final_boxes


def del_inner_box(contours):
    final_contours = []
    for con1 in contours:
        cx1 = con1.min_x
        cx2 = con1.max_x
        cy1 = con1.min_y
        cy2 = con1.max_y
        cw = con1.w
        ch = con1.h
        is_inner_box = False
        for con2 in contours:
            bx1 = con2.min_x
            bx2 = con2.max_x
            by1 = con2.min_y
            by2 = con2.max_y
            bw = con2.w
            bh = con2.h
            if cx1==bx1 and cx2==bx2 and cy1==by1 and cy2 == by2 :
                continue
            if cx1>=bx1 and cx2<=bx2 and cy1>=by1 and cy2 <= by2 and cw<=bw and ch<=bh:
                #print("{}-{} , {}-{} , {}-{} , {}-{}".format(cx1,bx1,cx2,bx2,cy1,by1,cy2,by2))
                is_inner_box = True
                continue
        if is_inner_box == False and con1.w*config.CONTOUR_SCALE <= con1.h:
            final_contours.append(con1)
    #print("final outer contours len: ",len(final_contours))
    return final_contours

def merge_small_boxs(small_boxs ):
    contours = []
    for box1 in small_boxs:
        merged_box = box1
        mbx1 = merged_box.min_x
        mbw1 = merged_box.w
        for box2 in small_boxs:
            if same_box(merged_box,box2):  
                continue
            if mbx1 == box2.min_x and mbw1 == box2.w:
                x = mbx1
                y1 = min(merged_box.min_y,box2.min_y)
                y2 = max(merged_box.max_y,box2.max_y)
                w = mbw1
                h = y2-y1
                if merged_box.h+box2.h > 0.9* h:
                    merged_box = BBox((x, y1, w, h), xywh=True)
        if  not same_box (merged_box,box1) and merged_box.w*config.CONTOUR_SCALE <= merged_box.h:
            contours.append(merged_box)
    return contours

def merge_tables(contours):
    tables = []
    for box1 in contours:
        merged_box = box1
        mby1 = merged_box.min_y
        mbh1 = merged_box.h
        for box2 in contours:
            if same_box(merged_box,box2):  
                continue
            if mby1 == box2.min_y and mbh1 == box2.h and abs(merged_box.min_x - box2.min_x) < 2* box2.w:
                x1 = min(merged_box.min_x,box2.min_x)
                x2 = max(merged_box.max_x,box2.max_x)
                y = box2.min_y
                w = x2 -x1
                h = box2.h
                if merged_box.h+box2.h > 0.9* h:
                    merged_box = BBox((x1, y, w, h), xywh=True)
        if not same_box (merged_box,box1):
            tables.append(merged_box)
    return tables

class Matcher:

    def __init__(self, image, text_dets):

        self.text_dets = text_dets
        self.img_contours = image.copy()
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        # Approach 1 - Directly binarlize
        _, bin_img = cv.threshold(image, 240, 255, cv.THRESH_BINARY)
        _, _, stats, _ = cv.connectedComponentsWithStats(bin_img)
        
        image_area = image.shape[0] * image.shape[1]
        self.chip_contours = []
        small_boxs = []
        for stat in stats:
            x = stat[cv.CC_STAT_LEFT]
            y = stat[cv.CC_STAT_TOP]
            w = stat[cv.CC_STAT_WIDTH]
            h = stat[cv.CC_STAT_HEIGHT]
            bbox = BBox((x, y, w, h), xywh=True)
            bbox_area = bbox.area()
        
            if h <= image.shape[0] * 0.8  and w <= image.shape[1] * 0.8  and h >= image.shape[0] * 0.01 and w >= image.shape[1] * 0.01  and bbox_area * config.AREA_THRESHOLG < stat[cv.CC_STAT_AREA]: 
                small_boxs.append(bbox)
                if w*config.CONTOUR_SCALE <= h:
                    self.chip_contours.append(bbox)
                #cv.rectangle(self.img_contours,(x,y) , (x+w,y+h),color=(0,255,0),thickness=5,lineType=cv.LINE_AA)
        
        merged_big_box = merge_small_boxs(small_boxs)
        if len(merged_big_box) != 0:
            self.chip_contours = merge_boxes(merged_big_box,self.chip_contours)
        self.chip_contours += merge_tables(self.chip_contours)
        print(" inner contours len:",len(self.chip_contours))
        self.chip_contours = del_inner_box(self.chip_contours)
        
        for chip in self.chip_contours:
            cv.rectangle(self.img_contours,(chip.min_x,chip.min_y) , (chip.max_x,chip.max_y),color=(0,255,0),thickness=10,lineType=cv.LINE_AA)
        cv.imwrite("./all_contour_boxes.jpg",self.img_contours)
        

    # Find the closest chip contour to the given part name bbox.
    def closestContour(self, bbox ,keyword ,image):
        best_dist = 65535
        best_index = -1
        best_center_index = -1
        img = image.copy()
        for i in range(len(self.chip_contours)):
            chip = self.chip_contours[i]
            dist_x = np.array([
                abs(bbox.min_x - chip.min_x),
                abs(bbox.max_x - chip.min_x),
                abs(bbox.min_x - chip.max_x),
                abs(bbox.max_x - chip.max_x),
            ]).min()
            dist_y = np.array([
                abs(bbox.max_y - chip.min_y),
                abs(bbox.min_y - chip.min_y),
                abs(bbox.min_y - chip.max_y),
                abs(bbox.max_y - chip.max_y)
            ]).min()
            if dist_y < best_dist and bbox.max_x > chip.min_x - chip.w*config.VALID_RANGE and bbox.min_x < chip.max_x + chip.w*config.VALID_RANGE and dist_x < chip.w and dist_y < chip.h//2:
                #print(bbox.max_x,chip.min_x,bbox.min_x,chip.max_x,bbox.max_y ,chip.max_y, bbox.min_y , chip.min_y)
                if bbox.max_y > chip.max_y or bbox.min_y < chip.min_y:
                    print("                      matching contour success!           ") 
                    best_dist = dist_y
                    best_index = i
                elif bbox.min_y > chip.min_y and bbox.max_y < chip.max_y and bbox.min_x > chip.min_x and bbox.max_x < chip.max_x:
                    print("                      matching contour(in center) success!")
                    best_dist = dist_y
                    best_center_index = i
                else:
                    #print("MATCH FAILED!")
                    continue
        final_index = max(best_center_index,best_index)
        if final_index != -1:
            if final_index == best_center_index:
                print("This component number ( {} ) is in center of Chip !!!".format(keyword))
            return self.chip_contours[final_index] , final_index    
        else:
            print("                 MATCH FAILED!               ")
            return None,None


    # Find the text with a center closest to the given point.
    def closestText(self, p):
        def mat(p):
            return np.array(list(p)).astype(np.float64)
        best_dist = 65535
        best_text = None
        for bbox, text in self.text_dets:
            center = (bbox.min_x + bbox.w//2, bbox.min_y + bbox.h//2)
            dist = cv.norm(mat(p), mat(center), cv.NORM_L2)
            if dist < best_dist:
                best_dist = dist
                best_text = text
        return best_text, best_dist
        
    # find the function name by keyword in excel data.
    def function_in_excel(self,keyword, pd_excel):
        func = ""
        for i in range( len(pd_excel)):
            kword = pd_excel[config.KEYWORD][i]
            if kword == keyword :
                func = pd_excel[config.FUNCTION][i]
        return func  

    #input: chip contour , possible partNo bbox, partName bbox  in corner
    def filter_condition(self,matched_chip,detbox):
        x1 = matched_chip.min_x
        x2 = matched_chip.max_x
        y1 = matched_chip.min_y
        y2 = matched_chip.max_y
        if (detbox.max_x + detbox.w) > x1 and (detbox.min_x - detbox.w) < x2:
                if detbox.max_y > y2 and detbox.max_y-y2 > detbox.h/2  or detbox.min_y < y1 and y1-detbox.min_y > detbox.h/2:
                    return True
        return False

    #select possible partNo in center 
    def filter_center_condition(self,matched_chip,detbox):
        x1 = matched_chip.min_x
        x2 = matched_chip.max_x
        y1 = matched_chip.min_y
        y2 = matched_chip.max_y
        box_center_x = (detbox.min_x + detbox.max_x)//2
        box_center_y = (detbox.min_y + detbox.max_y)//2
        if box_center_x > x1 and box_center_x < x2 and box_center_y > y1 and box_center_y < y2:
            return True
        return False

    #find the closest character to four corners of rectangle of chip
    def closestNo(self,matched_chip, dets_corner, dets_center,part_name):
        x1 = matched_chip.min_x
        x2 = matched_chip.max_x
        y1 = matched_chip.min_y
        y2 = matched_chip.max_y
        w = matched_chip.w
        h = matched_chip.h
        result = []
        coordinate = [(x1,y1),(x2,y1),(x1,y2),(x2,y2)]
        #add 4 corners part No
        for x,y in coordinate:
            min_dist = 65535 
            min_box = ""
            min_text = None
            for detbox,text in dets_corner:
                box_center_x = (detbox.min_x + detbox.max_x)//2
                box_center_y = (detbox.min_y + detbox.max_y)//2
                dist = math.sqrt(math.pow((box_center_x - x), 2) + math.pow((box_center_y - y), 2))
                #if dist < min_dist and str(part_name) != str(text) and len(str(text)) !=0 and len(str(text)) !=1:
                if dist < min_dist and len(str(text)) !=0 and len(str(text)) !=1:
                    min_box = detbox
                    min_text = text
                    min_dist = dist
            if min_text is not None:
                result.append(min_text)
        #add center part NO
        min_dist_center = 65535 
        min_box_center = ""
        min_text_center = None
        for detbox,text in dets_center:
            box_center_x = (detbox.min_x + detbox.max_x)//2
            box_center_y = (detbox.min_y + detbox.max_y)//2
            #a text box center point's distance to top below line, and left right line
            dist_center = abs( (abs(box_center_x-x1) - abs(x2 - box_center_x)) )+ abs( (abs(box_center_y - y1) + abs(y2 - box_center_y)) )
            
            if dist_center < min_dist_center and str(part_name) != str(text) and len(str(text)) !=0 and len(str(text)) !=1:
                min_box_center = detbox
                min_text_center = text
                min_dist_center = dist_center
            #print("det text in center:",text," dist: ",dist_center," current min dist: ",min_dist_center," min_text_center: ",min_text_center)
        if min_text_center is not None:
            result.append(min_text_center)
        
        
        #sort the result list and merge same part NO
        result.sort(key = lambda i:len(i),reverse=False)
        print("this is result of sort : " , result)
        new_list = []
        for i in result:
            if i not in new_list:
                new_list.append(i)
        print("this is result of set sorted : " , new_list)
        return new_list

    def matchREFDES(self , bbox , keyword ,part_name , pd_excel,image):
        matched_chip,idx = self.closestContour(bbox,keyword,image.copy())
        if matched_chip == None or idx == None:
            return None,None,None
        cv.rectangle(image,(matched_chip.min_x,matched_chip.min_y) , (matched_chip.max_x,matched_chip.max_y),color=(0,255,0),thickness=5,lineType=cv.LINE_AA)
        print("chip w:{} ,chip h :{}".format(matched_chip.w,matched_chip.h) )
        dets_corner = []
        dets_center = []
        for detbox,det in self.text_dets:
            if self.filter_condition(matched_chip,detbox):
                dets_corner.append((detbox,det))           #ALL possible corner part NO
                #print("part number:{}".format(det))
            if self.filter_center_condition(matched_chip,detbox):
                dets_center.append((detbox,det))           #ALL possible center part NO
                #print(det,detbox.min_x,detbox.min_y,detbox.max_x,detbox.max_y)
            continue
        
        ret = "NO MATCHED PART NUMBER!"
        ret = self.closestNo(matched_chip,dets_corner,dets_center , part_name)
        best_function = "NO MATCHED FUNCTION!"
        best_function = self.function_in_excel(keyword,pd_excel)
        return  ret,best_function,idx       

