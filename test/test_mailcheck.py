import sys
sys.path.append('..')
import db
from ss import cfgshell
import mailcheck

dbinfo=db.ssdb()
cfgfile=cfgshell.cfgfile()

print 'choice test func...'
print '1=getrows(dbinfo,expdays,status)'
print '2-stopexp(dbinfo,cfgfile)'
print '3-mailtest(dbinfo)'
print '4-mailwillexp(dbinfo)'

while True:
    c=raw_input('choice test function no:',1)

    if c=='2':
        mailcheck.stopexp(dbinfo,cfgfile)
    elif c=='1':
        a=raw_input('expdays status:')
        a=a.split(' ')
        print mailcheck.getrows(dbinfo,int(a[0]),a[1])
    elif c=='3':
        mailcheck.mailtest(dbinfo)
    elif c=='4':
        mailcheck.mailwillexp(dbinfo)    
