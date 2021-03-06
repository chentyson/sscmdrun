# coding=utf-8
import sstime
from datetime import datetime, timedelta
import json
import commands
from twisted.python import log
from zope.interface import Interface, implements
from twisted.cred import checkers, credentials, portal
from twisted.internet.threads import deferToThread
import os
import signal
from config import config
import telnetlib
from ssmail import mail

myconfig = config()

class ISscmdAvaterInterface(Interface):
    def logout(self):
        '''''
        Interface to credentials
        '''

    def processCmd(self, line):
        '''''
        deal with command line
        '''


def get_pid(name):
    status, output = commands.getstatusoutput("pidof %s" % name)
    log.msg('get pid status,outpu: %d,%s' % (status, output))
    if status > 0:
        log.msg('because of fail commands, ss has no received reload signal.')
        return [];
    else:
        return map(int, output.split())


def param2dict(cmd, paramfrom, adict):
    for i in range(paramfrom, len(
            cmd)):  # command example: add pass:12345 qq:1716677 startdate:20180101 ,  so loop for every argument
        arg = cmd[i].split(':');
        if len(arg) == 1:
            return None, 'Argument[%s] format error,example: add pass:12345 qq:1716677 status:pay. By default,status is test, ips is 1\n' % \
                   cmd[i];
        if arg[0] in ('port', 'ips', 'devs'):
            value = int(arg[1])
        else:
            value = arg[1];
        adict[arg[0]] = value;
        if arg[0] == 'qq' and (not adict.has_key('email') or adict['email'] == None or adict['email'] == 'None'):
            adict['email'] = arg[1] + '@qq.com';
        if arg[0] == 'startdate' and adict['status'] == 'test':
            # default test for 2 days
            adict['enddate'] = (datetime.strptime(arg[1], '%Y%m%d') + timedelta(days=2)).strftime('%Y%m%d')
    return adict, ''


def stopport(port, dbinfo, cfgfile, factory):
    userinfo = {}
    userinfo['status'] = 'stop'
    port = dbinfo.update(port, userinfo)
    if port == 0:
        return 0, 'Fail. May be the port is not found.\n'
    # delete port from config file
    port, msg = cfgfile.del_port(port);
    if port > 0:
        cfgfile.save_config();
        signalpass(port)
        factory.reloadUser();  # 重新加载用户资料
    else:
        return 0, 'Fail.%s\n' % msg
    return 0, 'Ok. the port[%s] is stoped now.\n' % str(port)


def signalpass(port):
    pids = get_pid("shadowsocks-server")
    # send signal ,to reset port listener
    for i in pids:
        os.kill(i, signal.SIGHUP)
        log.msg('Sent a SIGHUP signal to ss, done');

def gettypestat( astatus, ips, devs ):
    if astatus == 'test':
        atype = '临时'
    elif int(ips) == 1 and int(devs) > 2:
        atype = '多设备共享网'
    elif int(ips) > 2 and int(devs) > 2:
        atype = '多设备独立网'
    else:
        atype = '个人版'
    if astatus == 'stop':
        astat = '停用'
    else:
        astat = '正常'
    return atype,astat

class SscmdAvater(object):
    implements(ISscmdAvaterInterface)
    avaterId = None
    usertype = None

    def logout(self):
        avaterId = None
        log.msg('User logout!!!')

    def chkarg(self, cmd, n):
        if len(cmd) != n:
            log.msg('Command need %d args.' % n);
            return False, 'Command need %d args.\n' % n
        return True, ''

    def processCmd(self, line, dbinfo, cfgfile, factory):
        if line[-1] == '\r': line = line[:-1]

        cmd = line.split(' ')
        if cmd == None: return 0, None;

        if cmd[0] == 'exit': return -1, None

        portinfo = '欢迎您成为震撼用户！请牢记您的账户ID\n-------------\n%s\n------------\n无论您需要售后支持或续费支付时都需备注您的账户ID，以表明身份！\n\n以下是您的详细账户资料：\n\n服务器IP:' + myconfig.getaserver() + '\n服务器端口:%d\n密码:%s\n账户类型:%s\n设备数:%s\n服务到期日:%s\n状态:%s\n\n安装使用步骤：微信搜索并关注公众号 震撼网络服务，进入后点公众号底部的安装帮助，按说明下载安装并设置即可。\n';

        if cmd[0] == 'cfglist' and self.usertype == 'admin':
            portlist = cfgfile.portpass();
            if len(cmd) == 1:
                # ports='\n'.join(str(i) for i in portlist)
                return 0, '\n'.join(
                    str(p) + ':' + str(s) for p, s in portlist.items())  # str(portlist).replace(',','\n') + '\n'
            elif len(cmd) == 2:
                return 0, '\n'.join(str(p) + ':' + str(s) for p, s in portlist.items() if str(p).find(cmd[1]) != -1)
                # for p,s in portlist.items():
                #    if s.find(cmd[1])!=-1:
                #        self.transport.write( '%s:%s\n' % (str(p),s) );
            return 0, None;

        if cmd[0] == 'list' and self.usertype == 'admin':
            userinfo = {}
            if len(cmd) > 1:
                if cmd[1] == 'pay' or cmd[1] == 'test' or cmd[1] == 'stop':
                    userinfo['status'] = cmd[1];
                # list expired ports now
                elif cmd[1] == 'exp' and len(cmd) == 2:
                    expdate = datetime.now().strftime('%Y%m%d');
                    userinfo['enddate'] = '<' + expdate;
                    userinfo['status'] = 'pay';
                # list expired ports after cmd[2] days
                elif cmd[1] == 'exp' and len(cmd) == 3 and cmd[2].isdigit():
                    expdate = datetime.now() + timedelta(days=int(cmd[2]));
                    userinfo['enddate'] = '<' + expdate.strftime('%Y%m%d');
                    userinfo['status'] = 'pay';
                else:
                    return 0, 'Unknown command! example: list test/stop/pay; list exp 30(means list all ports that will expire in 30 days) \n'
            cols, rows = dbinfo.find(userinfo);
            # ret='\n'.join( for
            # self.transport.write('测试下:bbbbb\n');
            return 0, str(cols) + '\n' + '\n'.join(str(a) for a in rows) + '\n%d records listed!\n' % len(rows);

        if cmd[0] == 'cfgfind' and self.usertype == 'admin':
            ret, msg = self.chkarg(cmd, 2)
            if not ret: return 0, msg

            (port, password) = cfgfile.find_port(cmd[1])
            print port, password
            if port != '0':
                aid = myconfig.getaid(row[cols.index('port')])
                return 0, portinfo % (aid, int(port), password, '', '', '', '正常')
            else:
                return 0, 'Port or password can not find [%s]!\n' % cmd[1]

        # find <port>/all
        # find <col-name>:<col-value> ....
        if cmd[0] == 'find' and self.usertype in ['admin', 'login']:
            if len(cmd) == 1:
                return 0, 'Missing arguments!\n'

            args = cmd[1].split(':')
            userinfo = {}
            info = None
            if len(args) == 1:
                if cmd[1].isdigit():
                    userinfo['port'] = int(cmd[1])
                    info = portinfo
                elif cmd[1] != 'all':
                    return 0, 'Unknown arguments!\n'
            else:
                for i in range(len(cmd)):
                    if i == 0: continue;
                    args = cmd[i].split(':')
                    if len(args) <= 1: continue;
                    userinfo[args[0]] = args[1]
            cols, rows = dbinfo.find(userinfo)
            # 如果记录数较多采用记录集返回
            if len(rows) >= 1:
                #msg = str(cols) + '\n' + '\n'.join(str(a) for a in rows) + '\n' + str(len(rows)) + ' records found!\n'
                msg = '\n'.join(' '.join(cols[i] + ':' + str(a[i]) for i in range(len(cols)-1)) for a in rows) + '\n' + str(len(rows)) + ' records found!\n'
            # 如果只有一条,则用格式返回
            if info and len(rows) == 1:
                ips = str(rows[0][cols.index('ips')])
                devs = str(rows[0][cols.index('devs')])
                stat = str(rows[0][cols.index('status')])
                if stat == 'test':
                    atype = '临时'
                elif int(ips) == 1 and int(devs) > 2:
                    atype = '多设备共享IP'
                elif int(ips) > 2 and int(devs) > 2:
                    atype = '多设备独立IP'
                else:
                    atype = '个人版'
                if self.usertype == 'user':
                    atype = '######'
                    ips = '######'
                    msg = ''  # 如果是普通用户,则省略详细信息
                if stat == 'stop':
                    astat = '停用'
                else:
                    astat = '正常'
                #msg += 'port:%s pass:%s qq:%s email:%s wechat:%s startdate:%s enddate:%s devs:%s ips:%s status:%s' % (cmd[1], str(rows[0][cols.index('pass')]), str(rows[0][cols.index('qq')]), str(rows[0][cols.index('email')]), str(rows[0][cols.index('wechat')]), str(rows[0][cols.index('startdate')]), str(rows[0][cols.index('enddate')]), str(rows[0][cols.index('devs')]), str(rows[0][cols.index('ips')]), str(rows[0][cols.index('status')]))
                msg += '\n' + info % (myconfig.getaid(cmd[1]), int(cmd[1]), str(rows[0][cols.index('pass')]), atype, devs, str(rows[0][cols.index('enddate')]), astat)
            if len(rows) < 1:
                msg = '查无满足条件账户记录!'
            return 0, msg

        if cmd[0] == 'cfgcount' and self.usertype in ['admin']:
            return 0, '%d\n' % cfgfile.count_port('')

        if cmd[0] == 'add' and self.usertype in ['admin', 'login']:
            # get parameters, init userinfo
            userinfo = {}
            userinfo['pass'] = dbinfo.GenPassword()  # 默认产生随机密码
            userinfo['status'] = 'test'  # 默认临时账户
            userinfo['ips'] = 2
            userinfo['devs'] = 2
            userinfo['startdate'] = datetime.now().strftime('%Y%m%d')
            userinfo['enddate'] = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d');  # default test for 2 days
            userinfo['loginid'] = self.avaterId
            userinfo, msg = param2dict(cmd, 1, userinfo)
            if msg: return 0, msg
            #如果是远程执行
            #if userinfo.has_key('server'):

            # get free port and save to db
            # portpsw=portshell.add_new_port(config,userinfo['pass'],'', userinfo['ips']);
            if userinfo.has_key('port'):
                port = userinfo['port']
            else:
                port = dbinfo.getfreeport(userinfo['ips'])
            if port == 0:
                return 0, 'Fail,port for ipnumbers[%d] is full,delete stoped port or change ipnums.\n' % userinfo['ips']
            # save to db
            port = dbinfo.add(port, userinfo)
            if port == 0:
                return 0, 'Fail,when save user information!\n'
            log.msg('Port[%d] is now saved to db,user information[%s]' % (port, str(userinfo)))
            # save to config file and active
            # portpsw=portshell.add_new_port(config,userinfo['pass'],'', userinfo['ips']);
            cfgfile.portpass()[str(port)] = userinfo['pass'];
            log.msg('Port[%d] is new added to mem(not saved),password[%s]' % (port, userinfo['pass']))
            cfgfile.save_config();
            log.msg('Port[%s] is saved to config and actived ,password[%s]' % (port, userinfo['pass']))
            dbinfo.addlog(self.avaterId, port, line);
            # reload pass
            signalpass(port)
            factory.reloadUser()  # 重新加载用户资料
            ips = userinfo['ips']
            devs = userinfo['devs']
            atype,astat = gettypestat( userinfo['status'], int(ips), int(devs) )
            result = portinfo % (myconfig.getaid(port), myconfig.getaport(port), userinfo['pass'], atype, ips, userinfo['enddate'], astat)
            if userinfo['email']:
                deferToThread(mail, '震撼网络账户开户资料(' + myconfig.getaid(port) + ')',result,'', userinfo['email'] )  
            return 0, result

        if cmd[0] == 'update' and self.usertype in ['admin', 'login']:
            if len(cmd) < 3 or not cmd[1].isdigit():
                return 0, 'Invalid argument. example: update 11250 qq:1716677 email:1716677@qq.com \n'
            userinfo = dbinfo.getuserinfo(int(cmd[1]))
            if len(userinfo) == 0:
                return 0, 'Can not find port[%d] record!\n' % int(cmd[1])
            userinfo, msg = param2dict(cmd, 2, userinfo)
            if msg: return 0, msg
            port = dbinfo.update(int(cmd[1]), userinfo)
            if port == 0:
                return 0, 'Fail when update user information to db.\n'
            log.msg('port[%d] is updated. New user information[%s].' % (port, str(userinfo)))
            dbinfo.addlog(self.avaterId, port, line)
            return 0, 'port[%d] is updated. New user information[%s]. \n' % (port, str(userinfo))

        if cmd[0] == 'passwd' and self.usertype in ['admin', 'login', 'user']:
            if len(cmd) < 3 or not cmd[1].isdigit():
                return 0, 'Invalid argument. usage: passwd <port> <new password>.  example: passwd 11250 aaaa \n'
            if self.usertype == 'user' and cmd[1] != self.avaterId and self.avaterId != '11000':
                return 0, '只有线路管理员 或 用户自己才能修改密码.\n'
            userinfo = dbinfo.getuserinfo(int(cmd[1]))
            if len(userinfo) == 0:
                return 0, 'Fail,Can not find d-port[%d].\n' % int(cmd[1])
            userinfo = {}
            userinfo['pass'] = cmd[2]
            port = dbinfo.update(int(cmd[1]), userinfo)
            if port == 0:
                return 0, 'Fail when change d-port password.\n'
            log.msg('port[%d] password is changed to db.New userinfo[%s].' % (port, str(userinfo)))
            if not cfgfile.portpass().has_key(str(port)):
                return 0, 'Can not find f-port[%d] .\n' % port
            cfgfile.portpass()[str(port)] = userinfo['pass']
            cfgfile.save_config()
            signalpass(port)
            factory.reloadUser() # 重新加载用户资料
            log.msg('Port[%s] password is changed to config file. New password is [%s]' % (port, userinfo['pass']))
            dbinfo.addlog(self.avaterId, port, line)
            return 0, 'port[%d] password is changed! Active. \n' % (port)

        if cmd[0] == 'expdate' and self.usertype in ['admin', 'login', 'user']:
            if len(cmd) < 2 or not cmd[1].isdigit():
                return 1, 'Invalid argument format'
            port = int(cmd[1])
            # if port<30000:
            #    port=port+20000
            if self.usertype == 'user' and str(port) != self.avaterId:
                return 1, 'The port you queryed shold be logined.'
            userinfo = dbinfo.getuserinfo(port)
            if len(userinfo) == 0:
                return 1, 'Fail,Can not find d-port[%d].' % port
            else:
                return 0, str('ok,%s' % userinfo['enddate'])

        # pay a port. update db status to 'pay', check config file and create if not exists
        if cmd[0] == 'pay' and self.usertype in ['admin', 'login']:
            if len(cmd) != 3 or not cmd[1].isdigit() or not cmd[2].lstrip('-').isdigit():
                return 0, 'Invalid argument.Usage:pay <port> <months>  Example:pay 11250 12  (Means port 11250 expire date will add 12 months). \n'
            userinfo = dbinfo.getuserinfo(int(cmd[1]))
            if len(userinfo) == 0:
                return 0, 'Can not find port[%d].\n' % int(cmd[1])
            log.msg('Find port[%s], userinfo[%s].' % (cmd[1], str(userinfo)))
            # status change to pay,and update end date;
            # if userinfo['status']=='test':
            #    end=datetime.strptime(userinfo['startdate'],'%Y%m%d').date()
            # else:
            end = datetime.strptime(userinfo['enddate'], '%Y%m%d').date()
            if end < datetime.now().date():
                end = datetime.now().date()
                # pay month num will wrong ,if port is expired for months. billdate should be today
                userinfo['billdate'] = datetime.strftime(end, '%Y%m%d')
            userinfo['status'] = 'pay'
            end = sstime.monthdelta(end, int(cmd[2]))
            end = datetime.strftime(end, '%Y%m%d')
            userinfo['enddate'] = end;
            log.msg('Update port[%s] userinfo to new[%s].' % (cmd[1], str(userinfo)));
            # update to db
            port = dbinfo.update(int(cmd[1]), userinfo);
            if port == 0:
                return 0, 'Fail. May be the port is not found. please add it first.\n'
            # update config file
            cfgfile.portpass()[str(port)] = userinfo['pass']
            cfgfile.save_config();
            signalpass(port)
            factory.reloadUser();  # 重新加载用户资料
            log.msg('pay command. port[%s] is payed for [%s] months. New user infomation[%s]\n' % (
            cmd[1], cmd[2], str(userinfo)));
            dbinfo.addlog(self.avaterId, port, line)
            return 0, 'Ok. the port[%s] is payed for [%s] months. New end date[%s]\n' % (
            cmd[1], cmd[2], userinfo['enddate'])

        # set status 'stop' in db, and delete port from config file
        if cmd[0] == 'stop' and self.usertype in ['admin', 'login']:
            ret, msg = self.chkarg(cmd, 2)
            if not ret: return 0, msg
            if not cmd[1].isdigit():
                return 0, 'Command paramater should be a port number! Such as: pay 11250. \n'
            port = int(cmd[1])
            ret, msg = stopport(int(cmd[1]), dbinfo, cfgfile, factory)
            dbinfo.addlog(self.avaterId, port, line)
            return ret, msg

            # del userinfo from db and config file
        if cmd[0] == 'del' and self.usertype in ['admin', 'login']:
            ret, msg = self.chkarg(cmd, 2)
            if not ret: return 0, msg
            if not cmd[1].isdigit():
                return 0, 'Fail,invalid argument, it should be a num. example: del 11001.\n'
            port, rows = dbinfo.delete(self.avaterId, int(cmd[1]));
            if port == 0:
                log.msg('Port[%s] is not found in db!' % port)
            #    self.transport.write('Fail,delete user from db fail. Maybe the port[%s] can not be found.\n' % cmd[1]);
            #    return;
            elif port == -1:
                return 0, 'Fail,Can not delete not stoped port! Please stop it first!\n'
            else:
                log.msg('Port[%s] is deleted from db!' % port)
            port = int(cmd[1]);
            # delete port from config file, if not exist, not care
            cfgfile.del_port(port);
            cfgfile.save_config();
            signalpass(port)
            factory.reloadUser();  # 重新加载用户资料
            log.msg('Port[%d] is deleted from config file! userinfO:%s' % (port, str(rows)))
            dbinfo.addlog(self.avaterId, port, line);
            return 0, 'OK,port[%d] is deleted. ' % port

        if cmd[0] == 'cfgreset' and self.usertype in ['admin']:  # reset config file, depend on sscmd.db
            cfgfile.save_config();  # backup
            cfgfile.clear_port();
            userinfo = {};
            cols, rows = dbinfo.find(userinfo);
            for r in rows:
                if r[cols.index('status')] == 'pay':
                    port = r[cols.index('port')];
                    cfgfile.portpass()[str(port)] = r[cols.index('pass')];
            cfgfile.save_config();
            signalpass(0)
            factory.reloadUser();  # 重新加载用户资料
            log.msg('OK,config file is reseted to db pay user infomation!');
            dbinfo.addlog(self.avaterId, 0, line);
            return 0, 'OK,config file is reseted to db pay user infomation!'

        if cmd[0] == 'restart' and self.usertype == 'admin':
            (status, output) = cfgfile.commit()
            log.msg('Commit,status(%s),output(%s)' % (status, output))
            dbinfo.addlog(self.avaterId, port, line);
            if status > 0:
                return 0, 'Fail,Restart server error. \n%s\n' % output
            else:
                return 0, 'Ok,restart server done.\n%s\n' % output

        if cmd[0] == 'cclp' and self.usertype == 'admin':
            (status, output) = commands.getstatusoutput('/root/sscmdrun/cclp')
            log.msg('Run cclp,status(%s)' % status)
            if status > 0:
                return 0, 'Fail,run cclp error. \n%s\n' % output
            else:
                return 0, 'Ok,\n%s\n' % output

        if cmd[0] == 'netstat' and self.usertype == 'admin':
            if len(cmd) < 2 or not cmd[1].isdigit():
                return 0, 'Invalid argument. usage: netstat <port>. example: netstat 11250\n'
            (status, output) = commands.getstatusoutput('netstat -anp | grep %s' % cmd[1])
            log.msg('run netstat -anp | grep %s' % cmd[1])
            if status > 0:
                return 0, 'Fail,run netstat error. \n%s\n' % output
            else:
                return 0, output

        # 301
        if cmd[0] == 'bills' and self.usertype in ['admin', 'login']:  # gen bills of ports which not payed
            if len(cmd) >= 2 and self.usertype == 'login' and cmd[1] != self.avaterId:
                return 0, '{"cmd":"301","res":"fail","msg":"Fail,Pemission denied!"}'
            if len(cmd) < 2:
                if self.usertype == 'admin':
                    loginid = ''
                else:
                    loginid = self.avaterId
            else:
                loginid = cmd[1]
            ret = {'cmd': '301', 'res': 'ok'}
            ret['msg'] = dbinfo.genbills(loginid)
            return 0, json.dumps(ret)

        # 302
        if cmd[0] == 'expired' and self.usertype in ['admin', 'login']:  # return all ports which expired after n days
            if len(cmd) < 2 or not cmd[1].isdigit():
                return 0, '{"cmd":"302","res":"fail","msg":"Invalid command. usage: expired <days num>. example:expired 10"}'
            userinfo = {}
            expdate = sstime.now() + timedelta(days=int(cmd[1]));
            userinfo['enddate'] = '<' + expdate.strftime('%Y%m%d');
            userinfo['status'] = 'pay|test';
            if self.usertype != 'admin':
                userinfo['loginid'] = self.avaterId
            cols, rows = dbinfo.find(userinfo);
            rets = []
            ret = {}
            iport = cols.index('port');
            ienddate = cols.index('enddate');
            iqq = cols.index('qq');
            iwechat = cols.index('wechat');
            iemail = cols.index('email');
            for r in rows:
                ret['port'] = r[iport];
                ret['enddate'] = r[ienddate];
                ret['qq'] = r[iqq];
                ret['wechat'] = r[iwechat];
                ret['email'] = r[iemail];
                dend = datetime.strptime(r[ienddate], "%Y%m%d")
                ret['left'] = (dend - datetime.now()).days + 1;
                rets.append(ret.copy())
            result = {'cmd': '302', 'res': 'ok'}
            result['msg'] = rets
            return 0, json.dumps(result)

        if cmd[0] == 'testport' and self.usertype in ['admin']:  # test a remote port
            if len(cmd) < 3 or not cmd[1].isdigit():
                return 0, 'Invalid command. usage: testport <host> <port>.\n'
            try:
                tn = telnetlib.Telnet(cmd[1], port=int(cmd[2]), timeout=5)
                tn.close()
                return 0, 'ok'
            except:
                return 0, 'fail'

        # 105
        if cmd[0] == 'genvcode' and self.usertype in [
            'reg']:  # generate a verification code and save and mail it, ex: genvcode 1716677@qq.com
            if len(cmd) < 2 or not '@' in cmd[1] or not '.' in cmd[1]:
                return 0, '{"cmd":"105","res":"err","msg":"Invalid command.usage: genvcode <email address>.\n"}'
            email = cmd[1]
            res, msg = dbinfo.genvcode(email)
            return 0, '{"cmd":105,"res":"%s","msg":"%s"}' % (res, msg)
        # 101
        if cmd[0] == 'reg' and self.usertype in ['reg']:
            if len(cmd) < 2:
                return 0, '{"cmd":"101","res":err","msg":"Invalid command.usage:reg <register info json>.\n"}'
            try:
                logininfo = json.loads(cmd[1])
            except Exception as e:
                log.err('register cmmand failed,wrong json format:%s, error:%s' % (cmd[1], e.message))
                log.err()
                return 0, '{"cmd":"101","res":"err","msg":"Invalid command.wrong register information format.\n"}'
            res, msg = dbinfo.reg(logininfo);
            return 0, '{"cmd":101,"res":"%s","msg":"%s"}' % (res, msg)
        # 102
        if cmd[0] == 'regupdate' and self.usertype in ['admin']:
            if len(cmd) < 3 or not ('@' in cmd[1]) or not ('.' in cmd[1]) or not ('{' in cmd[2]) or not ('}' in cmd[2]):
                return 0, '{"cmd":"102","res":"fail","msg":"Invalid command. usage:appupdate <email> <json info>”}'
            userinfo = json.loads(cmd[2])
            ret1, ret2 = dbinfo.regupdate(cmd[1], userinfo)
            if ret1 == 'ok':
                factory.reloadUser()  # 重新加载用户资料
            return 0, '{"cmd":"102","res":"%s","msg":"%s"}' % (ret1, ret2)

        # regfind <col-name>:<col-value> ....
        # 103
        if cmd[0] == 'regfind' and self.usertype in ['admin']:
            args = []
            if len(cmd) > 1:
                args = cmd[1].split(':')
            userinfo = {};
            if len(args) == 1:
                if cmd[1].isdigit():
                    userinfo['id'] = int(cmd[1]);
                else:
                    userinfo['email'] = cmd[1]
            else:
                for i in range(len(cmd)):
                    if i == 0: continue;
                    args = cmd[i].split(':');
                    if len(args) <= 1: continue;
                    userinfo[args[0]] = args[1];
            cols, rows = dbinfo.regfind(userinfo);
            # 如果记录数较多采用记录集返回
            msgs = []
            col = {}
            colnum = len(cols)
            for row in rows:
                for i in range(colnum):
                    col[cols[i]] = row[i]
                msgs.append(col.copy())
            ret = {'cmd': '103', 'res': 'ok'}
            ret['msg'] = msgs
            return 0, json.dumps(ret)
    
        #303
        if cmd[0] == 'mail' and self.usertype in ['admin']:
            if len(cmd) <> 2 or not cmd[1].isdigit():
                return 0,'{"cmd":"303","res":"fail","msg":"Invalid command. usage:mail <port>"}'
            port = int(cmd[1])
            userinfo = {'port':port}
            cols, rows = dbinfo.find(userinfo);
            print( cols,rows ) 
            if len(rows)<1:
               return 0,'{"cmd":"303","res":"fail","msg":"port not found!"}'
            for col in cols:
                userinfo[col]=str(rows[0][cols.index(col)])
            if not userinfo['email']:
               return 0,'{"cmd":"303","res":"fail","msg":"no email addr found!"}'
            ips = int(userinfo['ips'])
            devs = int(userinfo['devs'])
            atype,astat = gettypestat( userinfo['status'], ips, devs )
            result = portinfo % (myconfig.getaid(port), myconfig.getaport(port), userinfo['pass'], atype, ips, userinfo['enddate'], astat)
            deferToThread(mail, '震撼网络账户资料(' + myconfig.getaid(port) + ')',result,'', userinfo['email'])    
            ret = {'cmd':'303','res':'ok'}
            return 0, json.dumps(ret)

        return 0, 'Fail,Unknown command or permission denied.\n'  # Command should be "add","stop","del","list","find","exit","count","commit"\n');
