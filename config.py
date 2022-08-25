# General
# Available choices: ["PackageMgr", "StandaloneJar", "NativeImage"]
PDFTK_INSTALLATION_TYPE = "PackageMgr"
BACKGROUND_THRESHOLD = 240

# Multi-scale configurations
INITIAL_DENSITY = 360
MAX_SCALE = 1
SCALE_STEP = 1.2
STOP_TH = 1.05

# Line detection approach configurations
LINE_INT_TOLERANCE = 8

# Connected components approach configurations
CC_AREA_LOWER_BOUND = 0.001
CC_AREA_UPPER_BOUND = 0.8
CC_EXPAND_RATE = 0.03

#contours
AREA_THRESHOLG = 0.5#0.65 # chip area : contour area
VALID_RANGE = 0.2   #valid detective range of area of component contour
CONTOUR_SCALE = 0.8

#ocr accuracy
KEYWORD_ERROR_RATE = 0.3

#DataBase
MPN =  "Manufacturing Part Number(MPN)"
KEYWORD = "keyword"
FUNCTION = "function"
NETNAME = "Net Name Keyword"
REFDES = "reference designator(REFDES)"
NOTES = "Notes"


#Manual keywords
MANUAL_KEYWORDS = ["SATA","USB","HDMI","EMMC","USB3","OPT","UFS"]