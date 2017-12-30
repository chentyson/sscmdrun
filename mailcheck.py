import ssmail
from SscmdAvater import stopport
from twisted.python import log
from datetime import timedelta
from twisted.internet.threads import deferToThread
import sstime

def getrows(dbinfo,expdays,status):
    userinfo={}
    expdate=sstime.now()+timedelta(days=expdays);
    userinfo['enddate']='<'+expdate.strftime('%Y%m%d');
    userinfo['status']=status;
    return dbinfo.find(userinfo)
    
def stopexp(myfac):
    #mail to payed user expired
    cols,rows=getrows(myfac.dbinfo,0,'pay')
    for row in rows:
        port=int(row[cols.index('port')])
        ret,msg=stopport(port,myfac.dbinfo,myfac.cfgfile)
        log.msg('sscmd system stop port[%d] auto.port info:%s' % (port,str(row)))
    if len(rows)>0:
        deferToThread(ssmail.mailexp,cols,rows)
    cols,rows=getrows(myfac.dbinfo,0,'test')
    for row in rows:
        port=int(row[cols.index('port')])
        ret,msg=stopport(port,myfac.dbinfo,myfac.cfgfile)
        port,nouse=myfac.dbinfo.delete(port);
        if port==0:
            log.msg('Test port[%s] is expired but can not found in db!' % port)
        else: 
            log.msg('sscmd system stop and delete port[%d] auto.port info:%s' % (port,str(row)))
    if len(rows)>0:
        deferToThread(ssmail.mailexp,cols,rows)

def mailtest(myfac):
    #mail to test user who whill expired after 2 days
    cols,rows=getrows(myfac.dbinfo,3,'test')
    if len(rows)>0:
        deferToThread(ssmail.mailtest,cols,rows)

def mailwillexp(myfac):
    #mail to payed user who will expired after 5 day
    cols,rows=getrows(myfac.dbinfo,6,'pay')
    if len(rows)>0:
        deferToThread(ssmail.mailwillexp,cols,rows)

def mailstoped(myfac):
    #mail to stoped users to buy service if they need it
    cols,rows=getrows(myfac.dbinfo,30,'stop')
    if len(rows)>0:
        deferToThread(ssmail.mailstoped,cols,rows)

#def mailcclpx(myfac):
    #run cclpx, get all ports that connect number is over 2,then mail to user warning,

