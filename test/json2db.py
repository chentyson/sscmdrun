import sys
sys.path.append('..')
from ss import cfgshell
import db
from datetime import datetime,timedelta
import timetool

cfgfile=cfgshell.cfgfile()
ports=cfgfile.portpass()
ssdb=db.ssdb()

print '%d ports in the config file!' % len(ports)

savecount=0;
for port,passwd in ports.items():
    #print port,passwd
    #print port,passwd,type(port)
    pp=passwd.split('-');

    qq=None;
    if pp[0].isdigit(): qq=pp[0];

    email=None;
    if qq!=None: email=qq+'@qq.com'

    start=0;
    end=0;
    if pp[-1]=='test': 
        status='test';
        start=int(datetime.strftime(datetime.now(),'%Y%m%d'))
        end=int(datetime.strftime(datetime.now()+timedelta(days=3),'%Y%m%d'))
    elif pp[-1]=='stop': 
        status='stop';
        start=int(datetime.strftime(datetime.now(),'%Y%m%d'))
        end=start
    else: 
        status='pay';
        mm=12;  #default 12 month expired
        if pp[-1].isdigit() and len(pp)==3 and pp[-2].isdigit(): 
            start=int(pp[-2])
            mm=int(pp[-1])
        elif len(pp)>1 and pp[-1].isdigit(): start=int(pp[-1]) 
        if len(str(start))==6: start=int('20'+str(start));
        if start>0: 
            try: 
                end=datetime.strptime(str(start),'%Y%m%d').date()
                end=timetool.monthdelta(end,mm);
                end=int(datetime.strftime(end,'%Y%m%d'))
            except: 
                print 'error:::::::::::::::::::::',port,passwd
                continue;

    ssdb.add(int(port),{'qq':qq,'pass':passwd,'email':email,'startdate':start,'enddate':end,'status':status})
    savecount+=1;

ssdb.update(11250,{'qq':'1716677','email':'1716677@qq.com','enddate':88880101,'ips':10})
ssdb.update(11261,{'qq':'1716677','email':'1716677@qq.com','enddate':88880101,'ips':10})
ssdb.update(11544,{'qq':'2355808854','email':'2355808854@qq.com','startdate':20161010,'enddate':20171010})
ssdb.update(11563,{'qq':'2355808854','email':'2355808854@qq.com','startdate':20161219,'enddate':20171219})
ssdb.update(11564,{'qq':'2355808854','email':'2355808854@qq.com','startdate':20161219,'enddate':20171219})

print '%d ports saved to db' % savecount
