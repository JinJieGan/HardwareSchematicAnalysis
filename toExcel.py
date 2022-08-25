import xlwt
import pandas as pd
def export_excel(export ,name):
   if len(export) == 0:
     return None
   pf = pd.DataFrame(list(export))
   pf.columns = ['KeyWord','Part name' ,'Function','Part NO.' ,'page']
   file_path = pd.ExcelWriter( str(name) +'.xlsx')
   pf.fillna(' ',inplace = True)
   pf.to_excel(r"{}.xlsx".format(name))

