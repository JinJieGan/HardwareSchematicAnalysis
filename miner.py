import cv2 as cv
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox


def extractWord(pdfname,image):
    fp = open(pdfname, 'rb')
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages = PDFPage.get_pages(fp)
    result = []
    for page in pages:
        #image = cv.imread("exp_1-60/pd_00{}.jpg".format(pg))
        #print('Processing next page...',page.mediabox)
        h_pdf = page.mediabox[2]
        w_pdf = page.mediabox[3]
        h_img = image.shape[0]
        w_img = image.shape[1]
        if (h_pdf-w_pdf)*(h_img-w_img) < 0:
            h_pdf,w_pdf = w_pdf,h_pdf
        print("image w:{} h:{}. pdf w: {} h:{}".format(w_img,h_img,w_pdf,h_pdf))
        interpreter.process_page(page)
        layout = device.get_result()
        for lobj in layout:
            if isinstance(lobj, LTTextBox):
                x0,y0,x1, y1= lobj.bbox
                y0 = h_pdf - y0
                y1 = h_pdf - y1
                
                x0_img = int(x0/w_pdf*w_img)
                x1_img = int(x1/w_pdf*w_img)
                y0_img = int(y0/h_pdf*h_img)
                y1_img = int(y1/h_pdf*h_img)
                w = abs(x1 - x0)
                h = abs(y1 - y0)
                text = lobj.get_text()
                
                if w > h:
                    #cv.rectangle(image,(x0_img,y0_img) , (x1_img,y1_img),color=(0,0,255),thickness=3,lineType=cv.LINE_AA)
                    for te in text.split("\n"):
                        result.append( (  [ [x0_img,y0_img],[x1_img,y0_img],[x1_img,y1_img],[x0_img,y1_img]  ] , te, 1)  )
    #cv.imwrite("pdfminer.jpg",image)
    return result         
'''          
pdfname = "exp_1-60/pg_0055.pdf"                 
image = cv.imread("exp_1-60/pd_00{}.jpg".format(55))   
extractWord(pdfname,image)   
'''               