#coding=utf-8

import sqlite3
#import logging
from twisted.python import log

#logging.basicConfig(level=logging.DEBUG,
#                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#                datefmt='%a, %d %b %Y %H:%M:%S', 
#                filename='sscmd.log', 
#                filemode='a')
#
class ssdb:
    
    def __init__(self):
        self.conn=sqlite3.connect('/etc/shadowsocks/sscmd.db');
        self.cur=self.conn.cursor();
        self.cur.execute('create table if not exists users(port integer primary key not null,pass varchar(20), qq varchar(16),email varchar(30),startdate TEXT,enddate TEXT,ips integer,status varchar(10))');
        self.conn.commit();

    def add(self,port,userinfo={}):
        try:
            passwd=userinfo.get('pass');
            qq=userinfo.get('qq');
            email=userinfo.get('email')
            startdate=userinfo.get('startdate')
            if startdate==None: startdate=0;
            enddate=userinfo.get('enddate')
            if enddate==None: enddate=0;
            ips=userinfo.get('ips') #购买的多少并发用户数
            if ips==None: ips=1;
            status=userinfo.get('status');
            if status==None: status='test'
            count=self.cur.execute('select count(*) from users where port=%d' % port).fetchall()[0][0];
            if count>0: 
                log.err('db.py:Adding port[%d] is existed! return 0 back' % port)
                return 0
            self.cur.execute('insert into users(port,pass,qq,email,startdate,enddate,ips,status) values(%d,"%s","%s","%s","%s","%s",%d,"%s")' % (port,passwd,qq,email,startdate,enddate,ips,status));
            self.conn.commit();
            #logging.info('added a new port[%d],userinfo:[%s]!' % (port,str(userinfo))) 
            return port
        except Exception as e:
            log.err('db.py:Exception when add a user.port[%d],userinfo[%s]:%s' % (port,str(userinfo),e.message))
            log.err()
            return 0

    #查找信息，根据userinfo里面的内容，先匹配端口，再模糊匹配每个信息
    def find(self,userinfo={}):
        log.msg('now find records,param:%s' % str(userinfo));
        sql='';
        if userinfo.get('port')!=None:
            sql='port=%d' % userinfo.get('port')
        else:
            if userinfo.get('qq')!=None: 
                sql='qq like "%'+userinfo.get('qq')+'%"'
            if userinfo.get('email')!=None:
                if sql!='': sql+=' and ';
                sql+='email like "%'+userinfo.get('email')+'%"'
            if userinfo.get('startdate')!=None:
                if sql!='': sql+=' and ';
                sql+='startdate'+userinfo.get('startdate')   #{'startdate':'>20161211'}
            if userinfo.get('enddate')!=None:
                if sql!='': sql+=' and ';
                sql+='enddate'+userinfo.get('enddate')
            if userinfo.get('ips')!=None:
                if sql!='': sql+=' and ';
                sql+='ips'+userinfo.get('ips')
            if userinfo.get('status')!=None:
                if sql!='': sql+=' and ';
                sql+='status like "%'+userinfo.get('status')+'%"'
        cols='port,pass,qq,email,startdate,enddate,ips,status';
        sqls='select '+cols+' from users';
        if sql!='':
            sqls+=' where ' + sql; 
        log.msg(sqls);
        #load data from db
        return cols.split(','),self.cur.execute(sqls).fetchall();

    def getuserinfo(self,port):
        cols,rows=self.find({'port':port});
        if len(rows)==0: return {};
        return dict(zip(cols,rows[0]));

    def update(self,port,userinfo):
        #nothing to update,return None
        if len(userinfo)==0: return 0
        #port is not found,return none
        #cols,rows=self.find({'port':port});
        #if len(rows)==0: return 0;
        #found,update to db
        sets=','.join(a+'="'+str(b)+'"' for a,b in userinfo.items())
        sets='update users set %s where port=%d' % (sets,port);
        log.msg(sets)
        self.cur.execute(sets)
        self.conn.commit()
        return port
        #rec=dict(zip(cols,rows))
        #rec.update(userinfo);  #update rec from userinfo
        #save to db
       
    def delete(self,port):
        cols,rows=self.find({'port':port});
        if len(rows)==0: return 0,[];
        if rows[0][cols.index('status')]!='stop': return -1,[];
        self.cur.execute('delete from users where port=%d' % port);
        self.conn.commit()
        return port,dict(zip(cols,rows[0]))
     
    def getfreeport(self,ips):
        rows=self.cur.execute('select port from users where port>=%d order by port' % (10000+ips*1000)).fetchall();
        for i in range(10000+ips*1000,10000+ips*1000+999):
            try:
                rows.index((i,));
            except ValueError:
                return i;
        return 0;
