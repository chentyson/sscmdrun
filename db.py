# coding=utf-8

import sqlite3
# import logging
from twisted.python import log
from datetime import datetime
import ssmail
import string
from random import choice

# logging.basicConfig(level=logging.DEBUG,
#                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#                datefmt='%a, %d %b %Y %H:%M:%S', 
#                filename='sscmd.log', 
#                filemode='a')
#
class ssdb:

    def __init__(self):
        log.msg('begin init ssdb...');
        self.conn = sqlite3.connect('/etc/shadowsocks/sscmd.db');
        self.cur = self.conn.cursor();
        self.cur.execute('create table if not exists users(port integer primary key not null,pass varchar(20), qq varchar(16),email varchar(30),wechat varchar(20),startdate TEXT,enddate TEXT,ips integer,devs integer,status varchar(10))');
        try:
            self.cur.execute('alter table users add column billdate TEXT'); 
        except: pass;
        try:
            self.cur.execute('alter table users add column loginid TEXT'); 
        except: pass;
        try:
            self.cur.execute('alter table users add column deldate TEXT'); 
        except: pass;

        self.cur.execute('create table if not exists logs(id integer PRIMARY KEY autoincrement,loginid TEXT,time datetime,port integer,cmd TEXT,userinfo TEXT)')
        self.cur.execute('create table if not exists delusers(port integer,pass varchar(20),qq varchar(16),email varchar(30),wechat varchar(20),startdate TEXT,enddate TEXT, ips integer,devs integer,status varchar(10), billdate TEXT,loginid TEXT,delloginid TEXT, deldate datetime)');
        self.cur.execute('create table if not exists reg(id integer PRIMARY KEY autoincrement,email TEXT unique,pass TEXT,name TEXT,qq TEXT,phone TEXT,vcode TEXT,vcodetime datetime,status TEXT)')
        self.conn.commit();
        log.msg('end init ssdb.');

    def GenPassword(self,length=8,chars=string.digits):
        return ''.join([choice(chars) for i in range(length)])

    def genvcode(self,email):
       code=self.GenPassword(6,string.digits)
       try:
           self.cur.execute('replace into reg(email,vcode,vcodetime) values("%s","%s",datetime("now","30 minutes"))' % (email,code));
           self.conn.commit();
           if not ssmail.mail('震撼网络服务注册验证码','你本次注册验证码是:%s\n注意：验证码在你点获取验证码时起30分钟内有效。' % code,'',email):
               return ''
           else: return code
       except Exception as e:
           log.err('gen and mail verification code error:%s' % e.message)
           log.err()
           return ''

    def reg(self,logininfo={}):
        try:
            log.msg('register new id:%s' % logininfo)
            email = logininfo.get('email')
            qq = logininfo.get('qq')
            passwd = logininfo.get('pass')
            name = logininfo.get('name')
            phone = logininfo.get('phone')
            vcode = logininfo.get('vcode')
            if email==None or passwd==None:
                return -1,'invalid register information!'
            rows = self.cur.execute('select vcode,vcodetime from reg where email="%s"' % email).fetchall()
            if len(rows)<1 or vcode!=row[0][0]:
                return -2,'need the right email and verification code!'
            #now register
            self.cur.execute('replace info reg(email,pass,name,qq,phone,status) values("%s","%s","%s","%s","%s","pending")' % (email,passwd,name,qq,phone))
            self.conn.commit();
            return 0,'ok'
        except Exception as e:
            log.err('register fail! error:%s' % e.message)
            log.err()
            return -3,'register failed! got an exception!'

    def regapprove(self,email):
        try:
            log.msg('register approving %s...' % email)
            self.cur.execute('update reg set status="ok" where email="%s"' % email)
            return 0,'ok'
        except Exception as e:
            log.err('register approve failed! error:%s' % e.message)
            log.err()
            return -1,'register approve failed!'

    def addlog(self,loginid,port,cmd):
        try:
            self.cur.execute('insert into logs(loginid,time,port,cmd,userinfo) values("%s",datetime("now"),%d,"%s","%s")' % (loginid, port, cmd, self.getuserinfo(port)) );
            self.conn.commit();
        except Exception as e:
            log.err('addlog error:%s' % e.message);
            log.err();

    def add(self, port, userinfo={}):
        try:
            passwd = userinfo.get('pass')
            qq = userinfo.get('qq')
            email = userinfo.get('email')
            wechat = userinfo.get('wechat')
            startdate = userinfo.get('startdate')
            loginid = userinfo.get('loginid')
            if startdate == None: startdate = 0
            enddate = userinfo.get('enddate')
            if enddate == None: enddate = 0
            ips = userinfo.get('ips')  # 购买的多少并发用户数
            if ips == None: ips = 1;  # default personal version,1 ip
            devs = userinfo.get('devs')  # how many devices
            if devs == None: devs = 2;  # default personal version,2 devices
            status = userinfo.get('status');
            if status == None: status = 'test'
            billdate = None;
            if userinfo.get('billed') != None: 
                billdate = startdate;
            count = self.cur.execute('select count(*) from users where port=%d' % port).fetchall()[0][0];
            if count > 0:
                log.err('db.py:Adding port[%d] is existed! return 0 back' % port)
                return 0
            self.cur.execute('insert into users(port,pass,qq,wechat,email,startdate,enddate,ips,devs,status,billdate,loginid) values(%d,"%s","%s","%s","%s","%s","%s",%d,%d,"%s","%s","%s")' % (port, passwd, qq, wechat, email, startdate, enddate, ips, devs, status, billdate,loginid));
            self.conn.commit();
            # logging.info('added a new port[%d],userinfo:[%s]!' % (port,str(userinfo)))
            return port
        except Exception as e:
            log.err('db.py:Exception when add a user.port[%d],userinfo[%s]:%s' % (port, str(userinfo), e.message))
            log.err()
            return 0

    # 查找信息，根据userinfo里面的内容，先匹配端口，再模糊匹配每个信息
    def find(self, userinfo={}):
        log.msg('now find records,param:%s' % str(userinfo));
        sql = '';
        if userinfo.get('port') != None:
            if sql != '': sql += ' and ';
            sql = 'port=%d' % userinfo.get('port')
        else:
            if userinfo.get('qq') != None:
                if sql != '': sql += ' and ';
                sql = 'qq like "%' + userinfo.get('qq') + '%"'
            if userinfo.get('wechat') != None:
                if sql != '': sql += ' and ';
                sql = 'wechat like "%' + userinfo.get('wechat') + '%"'
            if userinfo.get('email') != None:
                if sql != '': sql += ' and ';
                sql += 'email like "%' + userinfo.get('email') + '%"'
            if userinfo.get('startdate') != None:
                if sql != '': sql += ' and ';
                sql += 'startdate' + userinfo.get('startdate')  # {'startdate':'>20161211'}
            if userinfo.get('enddate') != None:
                if sql != '': sql += ' and ';
                sql += 'enddate' + userinfo.get('enddate')
            if userinfo.get('ips') != None:
                if sql != '': sql += ' and ';
                sql += 'ips' + userinfo.get('ips')  # 参数中已经带了比较符号
            if userinfo.get('status') != None:
                if sql != '': sql += ' and ';
                sql += 'status like "%' + userinfo.get('status') + '%"'
            if userinfo.get('devs') != None:
                if sql != '': sql += ' and ';
                sql += 'devs' + userinfo.get('devs')
        cols = 'port,pass,qq,wechat,email,startdate,enddate,billdate,ips,devs,status,loginid';
        sqls = 'select ' + cols + ' from users';
        if sql != '':
            sqls += ' where ' + sql;
        log.msg(sqls);
        #rows = self.cur.execute(sqls).fetchall();
        #log.msg('%d records found!' % len(rows));
        # load data from db
        return cols.split(','), self.cur.execute(sqls).fetchall();

    def getuserinfo(self, port):
        cols, rows = self.find({'port': port});
        if len(rows) == 0: return {};
        return dict(zip(cols, rows[0]));

    def update(self, port, userinfo):
        # nothing to update,return None
        if len(userinfo) == 0: return 0
        # port is not found,return none
        # cols,rows=self.find({'port':port});
        # if len(rows)==0: return 0;
        # found,update to db
        sets = ','.join(a + '="' + str(b) + '"' for a, b in userinfo.items())
        sets = 'update users set %s where port=%d' % (sets, port);
        log.msg(sets)
        self.cur.execute(sets)
        self.conn.commit()
        return port
        # rec=dict(zip(cols,rows))
        # rec.update(userinfo);  #update rec from userinfo
        # save to db

    def delete(self, loginid, port):
        cols, rows = self.find({'port': port});
        if len(rows) == 0: return 0, [];
        if rows[0][cols.index('status')] != 'stop': return -1, [];
        self.cur.execute('insert into delusers(port,pass,qq,email,wechat,startdate,enddate,ips,devs,billdate,loginid,status,delloginid,deldate) select port,pass,qq,email,wechat,startdate,enddate,ips,devs,billdate,loginid,status,"%s",datetime("now") from users where port=%d' % (loginid,port));
        self.cur.execute('delete from users where port=%d' % port);
        self.conn.commit()
        return port, dict(zip(cols, rows[0]))

    def getfreeport(self, ips):
        rows = self.cur.execute('select port from users where port>=11000 order by port').fetchall();
        for i in range(11000, 29999):
            try:
                rows.index((i,));
            except ValueError:
                return i;
        return 0;
    
    def genbills(self,loginid):
        col = 'port,qq,email,wechat,billdate,startdate,enddate,status';
        sql = 'select %s,"",0 from users union select %s,delloginid,deldate from delusers' % (col,col)
        log.msg(sql); 
        rows=self.cur.execute(sql).fetchall()
        cols = col.split(',')
        
        iport = cols.index('port');
        iqq = cols.index('qq');
        iemail = cols.index('email');
        iwechat = cols.index('wechat');
        ibill = cols.index('billdate');
        istart = cols.index('startdate');
        iend = cols.index('enddate');
        ista = cols.index('status');
        ideldate = ista + 2;

        bills = [];
        bill = {};
        totalmonth = 0;
        if len(rows)== 0: return bills;
        for row in rows:
            status = row[ista];
            if status == 'test': continue;

            billdate = row[ibill];
            enddate = row[iend];
            #if billdate no data,equal to startdate
            if billdate == None or billdate == '' or billdate=='None':
                billdate = row[istart];
            if billdate>=enddate: continue;

            dend = datetime.strptime(enddate,"%Y%m%d")
            dbill = datetime.strptime(billdate,"%Y%m%d")
            months = ((dend-dbill).days + 10)/30; 
            
            if months > 0:
                bill['port']=row[iport];
                bill['startdate']=row[istart]
                bill['billdate']=billdate;
                bill['enddate']=enddate;
                bill['paymonth']=months;
                bill['qq']=row[iqq];
                bill['email']=row[iemail];
                bill['wechat']=row[iwechat];
                bill['deldate']=row[ideldate];
                bills.append(bill.copy());
                totalmonth += months;
        bills.append({'port':'#','paymonth':totalmonth});
        return bills;

    def login(self,email,passwd):
        rows=self.cur.execute('select name,qq from reg where email="%s" and pass="%s"' % (email,passwd)).fetchall()
        if len(rows)<1:
            return -1,'uknown email or wrong password!'
        return 0,rows
