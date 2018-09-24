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
        log.msg('begin init ssdb...')
        self.conn = sqlite3.connect('/etc/shadowsocks/sscmd.db')
        self.cur = self.conn.cursor();
        #user and deluser
        self.cur.execute('create table if not exists users(port integer primary key not null,pass varchar(20), qq varchar(16),email varchar(30),wechat varchar(20),startdate TEXT,enddate TEXT,ips integer,devs integer,status varchar(10))')
        try:
            self.cur.execute('alter table users add column billdate TEXT') 
            self.cur.execute('alter table users add column loginid TEXT') 
            self.cur.execute('alter table users add column deldate TEXT')
        except: pass;
        self.cur.execute('create table if not exists delusers(port integer,pass varchar(20),qq varchar(16),email varchar(30),wechat varchar(20),startdate TEXT,enddate TEXT, ips integer,devs integer,status varchar(10), billdate TEXT,loginid TEXT,delloginid TEXT, deldate datetime)')
        #logs
        self.cur.execute('create table if not exists logs(id integer PRIMARY KEY autoincrement,loginid TEXT,time datetime,port integer,cmd TEXT,userinfo TEXT)')
        #reg login id
        self.cur.execute('create table if not exists reg(id integer PRIMARY KEY autoincrement,email TEXT unique,pass TEXT,name TEXT,qq TEXT,phone TEXT,vcode TEXT,vcodetime datetime,status TEXT)')
        try:
            self.cur.execute('alter table reg add column feerateid integer')
        except: pass;
        self.cur.execute('replace into reg(id,email,pass,name,status,feerateid) values(1,"tyson","IamadminTyson","admin","ok",1)')
        #price and feerate
        self.cur.execute('create table if not exists price(id integer PRIMARY KEY,name TEXT,ips integer,devs integer,year integer,halfyear integer,quarter integer,month integer)')
        self.cur.execute('create table if not exists feerate(id integer PRIMARY KEY,priceid integer,rateyear float,ratehalfy float,ratequarter float,ratemonth float)')
        
        self.conn.commit();
        log.msg('end init ssdb.');

    def GenPassword(self,length=8,chars=string.digits):
        return ''.join([choice(chars) for i in range(length)])

    def genvcode(self,email):
        code=self.GenPassword(6,string.digits)
        try:
            rows = self.cur.execute('select status from reg where email="%s"' % email).fetchall();
            if len(rows) > 0:
                if rows[0][0] == 'pending':
                    return 'already', '该邮箱已经注册!\n\n请用您注册时登记的QQ号码联系 QQ：1716677，以便更快能审核通过！'
                elif rows[0][0] == 'ok':
                    return 'already', '您注册的邮箱已经是用户，可直接登录！'
                else:
                    self.cur.execute('update reg set vcode="%s",vcodetime=datetime("now","30 minutes") where email="%s"' % (code, email))
            else:
                self.cur.execute('insert into reg(email,vcode,vcodetime) values("%s","%s",datetime("now","30 minutes"))' % (email,code));
            self.conn.commit();
            if not ssmail.mail('震撼网络服务注册验证码', '你本次注册验证码是:%s\n注意：验证码在你点获取验证码时起30分钟内有效。' % code,'',email):
                return 'mailerr', '验证发送异常，请检查注册的邮箱地址是否正确。有疑问可联系 1716677@qq.com 咨询。'
            else:
                return 'ok', 'ok'
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
            if not email or not passwd or not vcode or not qq:
                return 'infomiss','无效的注册信息，注册时必填的项目不能少！'
            rows = self.cur.execute('select vcode,vcodetime from reg where email="%s"' % email).fetchall()
            if len(rows) < 1 or vcode != rows[0][0]:
                return 'nomatch', '您的验证码和注册邮箱不匹配，请您当时获取验证码的邮箱内查找并取得正确的验证码后填入再试试！'
            #now register
            self.cur.execute('update reg set pass="%s",name="%s",qq="%s",phone="%s",status="pending" where email="%s"' % (passwd,name,qq,phone,email))
            self.conn.commit();
            return 'ok','ok'
        except Exception as e:
            log.err('register fail! error:%s' % e.message)
            log.err()
            return 'err','register failed! got an exception!'

    def regapprove(self,email,feerateid):
        try:
            log.msg('register approving %s, use feerateid is %d...' % (email,feerateid))
            rows = self.cur.execute('select id from feerate where id=%s' % feerateid).fetchall()
            if len(rows)==0:
                return 'nofind', '审核用户通过的费用方案 %s 不存在！' % feerateid
            rows = self.cur.execute('select status from reg where email="%s"' % email).fetchall()
            if len(rows) == 0:
                return 'nofind', '无法找到审核的 email: %s ' % email
            if not rows[0][0] == 'pending':
                return 'errstat', '该用户状态无需审核！'
            ret = self.cur.execute('update reg set status="ok",feerateid=%d where email="%s"' % (feerateid,email))
            self.conn.commit();
            #log.msg('update result:%s' % ret.fetchall())
            return 'ok', 'ok'
        except Exception as e:
            log.err('register approve failed! error:%s' % e.message)
            log.err()
            return 'fail', '注册审批失败，有异常产生！'

    # 查找信息，根据userinfo里面的内容，先匹配端口，再模糊匹配每个信息
    def regfind(self, userinfo={}):
        log.msg('now find regrecords,param:%s' % str(userinfo));
        sql = '';
        if userinfo.get('email') != None:
            if sql != '': sql += ' and ';
            sql = 'email="%s"' % userinfo.get('email')
        else:
            if userinfo.get('qq') != None:
                if sql != '': sql += ' and ';
                sql = 'qq like "%' + userinfo.get('qq') + '%"'
            if userinfo.get('name') != None:
                if sql != '': sql += ' and ';
                sql = 'name like "%' + userinfo.get('name') + '%"'
            if userinfo.get('phone') != None:
                if sql != '': sql += ' and ';
                sql += 'phone like "%' + userinfo.get('phone') + '%"'
            if userinfo.get('status') != None:
                if sql != '': sql += ' and ';
                sql += 'status = "' + userinfo.get('status') + '"'
        cols = 'email,pass,qq,name,status,id,phone,feerateid';
        sqls = 'select ' + cols + ' from reg';
        if sql != '':
            sqls += ' where ' + sql;
        log.msg(sqls);
        #rows = self.cur.execute(sqls).fetchall();
        #log.msg('%d records found!' % len(rows));
        # load data from db
        return cols.split(','), self.cur.execute(sqls).fetchall();

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
                sql += '(' + ' or '.join('status like "%' + a + '%"' for a in userinfo.get('status').split('|')) + ')'
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
        col = 'a.port,a.qq,a.email,a.wechat,a.billdate,a.startdate,a.enddate,a.loginid,b.name,b.feerateid,c.year,c.halfyear,c.quarter,c.month,d.rateyear,d.ratehalfy,d.ratequarter,d.ratemonth,a.status';
        if loginid=='':
            sql = 'select %s,"",0 as deldate from users a left join reg b on a.loginid=b.email left join price c on a.ips=c.ips and a.devs=c.devs left join feerate d on b.feerateid=d.id and c.id=d.priceid union select %s,delloginid,deldate from delusers a left join reg b on a.loginid=b.email left join price c on a.ips=c.ips and a.devs=c.devs left join feerate d on b.feerateid=d.id and c.id=d.priceid' % (col,col)
        else:
            sql = 'select %s,"",0 as deldate from users a left join reg b on a.loginid=b.email left join price c on a.ips=c.ips and a.devs=c.devs left join feerate d on b.feerateid=d.id and c.id=d.priceid where a.loginid="%s" union select %s,delloginid,deldate from delusers a left join reg b on a.loginid=b.email left join price c on a.ips=c.ips and a.devs=c.devs left join feerate d on b.feerateid=d.id and c.id=d.priceid where a.loginid="%s"' % (col,loginid,col,loginid)
        log.msg(sql); 
        rows=self.cur.execute(sql).fetchall()
        cols = col.split(',')
        
        iport = cols.index('a.port');
        iqq = cols.index('a.qq');
        iemail = cols.index('a.email');
        iwechat = cols.index('a.wechat');
        ibill = cols.index('a.billdate');
        istart = cols.index('a.startdate');
        iend = cols.index('a.enddate');
        iname = cols.index('b.name');
        irateid = cols.index('b.feerateid')
        ifeey = cols.index('c.year');
        iratey = cols.index('d.rateyear');
        ifeeh = cols.index('c.halfyear');
        irateh = cols.index('d.ratehalfy');
        ifeeq = cols.index('c.quarter');
        irateq = cols.index('d.ratequarter')
        ifeem = cols.index('c.month')
        iratem = cols.index('d.ratemonth')
        ista = cols.index('a.status');
        ideldate = ista + 2;

        bills = [];
        bill = {};
        totalmonth = 0;
        totalfee = 0.0;
        if len(rows)== 0: return bills;
        for row in rows:
            status = row[ista];
            if status == 'test': continue;

            billdate = row[ibill];
            enddate = row[iend];
            deldate = row[ideldate]
            #if billdate no data,equal to startdate
            if billdate == None or billdate == '' or billdate=='None':
                billdate = row[istart];
            if deldate>0: #if port is deleted,enddate is which day deleted
                enddate=deldate;
            if billdate>=enddate: continue;

            dend = datetime.strptime(enddate,"%Y%m%d")
            dbill = datetime.strptime(billdate,"%Y%m%d")
            months = ((dend-dbill).days + 10)/30; 
            if row[ifeey]==None or row[iratey]==None: feey=0
            else:feey = row[ifeey] * row[iratey]
            if row[ifeeh]==None or row[irateh]==None: feeh=0
            else:feeh = row[ifeeh] * row[irateh]
            if row[ifeeq]==None or row[irateq]==None: feeq=0
            else:feeq = row[ifeeq] * row[irateq]
            if row[ifeem]==None or row[iratem]==None: feem=0
            else:feem = row[ifeem] * row[iratem]
            
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
                bill['name']=row[iname];
                if feey==0 or feeh==0 or feeq==0 or feem==0:
                    #bills.append({'port':'#','paymonth':'Error rate setting'})
                    log.msg('port:%s feey:%s feeh:%s feeq:%s feem:%s sql:%s' % (row[iport],feey,feeh,feeq,feem,sql))
                    bill['fee']='ERROR'
                    totalfee = -1;
                else:
                    bill['fee']=(months/12)*feey + (months%12/6)*feeh + (months%12%6/3)*feeq + (months%12%6%3)*feem
                    if totalfee>=0: totalfee += bill['fee'];
                bills.append(bill.copy());
                totalmonth += months;
        bills.append({'port':'#','paymonth':totalmonth,'fee':totalfee});
        return bills;

    def login(self,email,passwd):
        rows=self.cur.execute('select name,qq from reg where email="%s" and pass="%s"' % (email,passwd)).fetchall()
        if len(rows)<1:
            return -1,'uknown email or wrong password!'
        return 0,rows
