import sys
sys.path.append('..')
from datetime import datetime
import timetool

aa=datetime.now()
print aa 
print 'now add 2 month'
print timetool.monthdelta(aa,2)

