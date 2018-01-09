#coding=utf-8
import sstime
from random import choice
from datetime import datetime,timedelta
import json
import commands
from twisted.python import log
from zope.interface import Interface,implements
from twisted.cred import checkers,credentials,portal
import string
from subprocess import check_output
import os
import signal
from config import config

#define admin user and pass
_adminuser='tyson'
_adminpass='IamadminTyson'

def get_pid(name):
    return map(int,check_output(["pidof",name]).split())

class SscmdRealm(object):
    implements(portal.IRealm)

    def requestAvatar(self,avaterId, mind, *interfaces):
        if ISscmdAvaterInterface in interfaces:
            log.msg('requestAvater: %s' % avaterId);
            avater=SscmdAvater()
            avater.avaterId=avaterId
            if avaterId!=_adminuser: 
                avater.usertype='user'
            else: avater.usertype='admin'
            return ISscmdAvaterInterface,avater,avater.logout

        raise NotImplementedError('''''This Realm only support IEchoAvatarInterface''')

class ISscmdAvaterInterface(Interface):
    def logout(self):
        ''''' 
        Interface to credentials 
        '''
    def processCmd(self,line):
        '''''
        deal with command line 
        '''

#gen a random password
def GenPassword(length=8,chars=string.digits):
    return ''.join([choice(chars) for i in range(length)])

def param2dict(cmd, paramfrom, adict):
    for i in range(paramfrom,len(cmd)):   #command example: add pass:12345 qq:1716677 startdate:20180101 ,  so loop for every argument
        arg=cmd[i].split(':');
        if len(arg)==1:
            return None,'Argument[%s] format error,example: add pass:12345 qq:1716677 status:pay. By default,status is test, ips is 1\n' % cmd[i];
        if arg[0] in ('port','ips'): value=int(arg[1])
        else: value=arg[1];
        adict[arg[0]]=value;
        if arg[0]=='qq' and (not adict.has_key('email') or adict['email']==None or adict['email']=='None'):
            adict['email']=arg[1]+'@qq.com';
        if arg[0]=='startdate' and adict['status']=='test':
            adict['enddate']=(datetime.strptime(arg[1],'%Y%m%d')+timedelta(days=2)).strftime('%Y%m%d');  #default test for 2 days
    return adict,''

def stopport(port,dbinfo,cfgfile):
    userinfo={};
    userinfo['status']='stop';
    port=dbinfo.update(port,userinfo);
    if port==0: 
        return 0,'Fail. May be the port is not found.\n'
    #delete port from config file
    port,msg=cfgfile.del_port(port);
    if port>0:
        cfgfile.save_config();
    else: 
        return 0,'Fail.%s\n' % msg
    return 0,'Ok. the port[%s] is stoped now.\n' % str(port)

def signalpass(port):
    pids=get_pid("shadowsocks-server")
    #send signal ,to reset port listener
    for i in pids: 
        os.kill(i,signal.SIGHUP)            
        log.msg('Sent a SIGHUP signal to ss, done');
    
class SscmdAvater(object):
    implements(ISscmdAvaterInterface)
    avaterId=None
    usertype=None
    def logout(self):
        avaterId=None
        log.msg('User logout!!!')

    def chkarg(self,cmd,n):
        if len(cmd)!=n:
            log.msg('Command need %d args.' % n);
            return False,'Command need %d args.\n' % n
        return True,''

    def processCmd(self, line, dbinfo, cfgfile):
        if line[-1]=='\r': line=line[:-1]
  
        cmd = line.split(' ')    
        if cmd==None: return 0,None;
  
        if cmd[0]=='exit': return -1,None
       
        portinfo='欢迎您使用震撼翻墙软件，以下是您的账户信息：\n\n服务器IP:'+config.serverip'\n服务器端口:%d\n      密码:%s\n账户类型:%s\n设备数:%s\n服务到期日:%s\n\n安装步骤：运行安装软件，弹出的配置界面填入以上服务器ip、端口和密码，点确定即可！\n注意：安装过程如有360等拦截窗，切记选择允许或信任！\n\n安装完成打开浏览器测试地址：https://www.google.com/ncr\n';
  
        if cmd[0]=='cfglist' and self.usertype=='admin':
            portlist=cfgfile.portpass();
            if len(cmd)==1:
                #ports='\n'.join(str(i) for i in portlist)
                return 0, '\n'.join(str(p)+':'+str(s) for p,s in portlist.items())   #str(portlist).replace(',','\n') + '\n'
            elif len(cmd)==2:
                return 0,'\n'.join(str(p)+':'+str(s) for p,s in portlist.items() if str(p).find(cmd[1])!=-1)
                #for p,s in portlist.items():
                #    if s.find(cmd[1])!=-1:
                #        self.transport.write( '%s:%s\n' % (str(p),s) );
            return 0,None;
        
        if cmd[0]=='list' and self.usertype=='admin':
            userinfo={}
            if len(cmd)>1:
                if cmd[1]=='pay' or cmd[1]=='test' or cmd[1]=='stop': userinfo['status']=cmd[1];
                #list expired ports now
                elif cmd[1]=='exp' and len(cmd)==2:
                    expdate=datetime.now().strftime('%Y%m%d');
                    userinfo['enddate']='<'+expdate;
                    userinfo['status']='pay';
                #list expired ports after cmd[2] days 
                elif cmd[1]=='exp' and len(cmd)==3 and cmd[2].isdigit():
                    expdate=datetime.now()+timedelta(days=int(cmd[2]));
                    userinfo['enddate']='<'+expdate.strftime('%Y%m%d');
                    userinfo['status']='pay';
                else: 
                    return 0,'Unknown command! example: list test/stop/pay; list exp 30(means list all ports that will expire in 30 days) \n'
            cols,rows=dbinfo.find(userinfo);
            #ret='\n'.join( for 
            #self.transport.write('测试下:bbbbb\n');
            return 0,str(cols)+'\n'+'\n'.join(str(a) for a in rows) +'\n%d records listed!\n' % len(rows);
  
        if cmd[0]=='cfgfind' and self.usertype=='admin':
            ret,msg = self.chkarg(cmd,2)
            if not ret: return 0,msg

            (port,password)=cfgfile.find_port(cmd[1])
            print port,password
            if port!='0':
                return 0, portinfo % (int(port),password,'','','')
            else:
                return 0, 'Port or password can not find [%s]!\n' % cmd[1]
 
        #find <port>/all
        #find <col-name>:<col-value> .... 
        if cmd[0]=='find' and self.usertype=='admin':
            if len(cmd)==1: 
                return 0,'Missing arguments!\n'
            args=cmd[1].split(':')
            userinfo={};info=None
            if len(args)==1:
                if cmd[1].isdigit(): 
                    userinfo['port']=int(cmd[1]);
                    info=portinfo
                elif cmd[1]!='all': 
                    return 0,'Unknown arguments!\n'
            else: 
                for i in range(len(cmd)):
                    if i==0: continue;
                    args=cmd[i].split(':');
                    if len(args)<=1: continue;
                    userinfo[args[0]]=args[1];
            cols,rows=dbinfo.find(userinfo);
            msg=str(cols)+'\n'+'\n'.join(str(a) for a in rows) +'\n'+str(len(rows))+' records found!\n'
            if info and len(rows)==1:
                ips=str(rows[0][cols.index('ips')]);
                if int(ips)>2:
                    atype='多人共享版'
                else:
                    atype='个人版'
                msg += '\n'+info % (int(cmd[1]),str(rows[0][cols.index('pass')]),atype,ips,str(rows[0][cols.index('enddate')]))
            return 0,msg
            
        if cmd[0]=='cfgcount' and self.usertype=='admin':
            return 0,'%d\n' % cfgfile.count_port('')
        
        if cmd[0]=='add' and self.usertype=='admin':
            #get parameters, init userinfo
            userinfo={}
            userinfo['pass']=GenPassword();
            userinfo['status']='test';
            userinfo['ips']=1;
            userinfo['startdate']=datetime.now().strftime('%Y%m%d');
            userinfo['enddate']=(datetime.now()+timedelta(days=1)).strftime('%Y%m%d');  #default test for 2 days
            userinfo,msg=param2dict(cmd,1,userinfo);
            if msg: return 0,msg
            #get free port and save to db
            #portpsw=portshell.add_new_port(config,userinfo['pass'],'', userinfo['ips']);
            if userinfo.has_key('port'): port=userinfo['port'];
            else: port=dbinfo.getfreeport(userinfo['ips']);
            if port==0:
                return 0,'Fail,port for ipnumbers[%d] is full,delete stoped port or change ipnums.\n' % userinfo['ips']
            #save to db
            port=dbinfo.add(port,userinfo);
            if port==0:
                return 0,'Fail,when save user information!\n'
            log.msg('Port[%d] is now saved to db,user information[%s]' % (port,str(userinfo)))
            #save to config file and active
            #portpsw=portshell.add_new_port(config,userinfo['pass'],'', userinfo['ips']);
            cfgfile.portpass()[str(port)]=userinfo['pass'];
            log.msg('Port[%d] is new added to mem(not saved),password[%s]' % (port,userinfo['pass']))
            cfgfile.save_config();
            log.msg('Port[%s] is saved to config and actived ,password[%s]' % (port,userinfo['pass']))
            ips=userinfo['ips']
            if int(ips)>2:
                atype='多人共享版'
            else: atype='个人版'
            return 0, portinfo % (port,userinfo['pass'],atype,ips,userinfo['enddate'])
  
        if cmd[0]=='update' and self.usertype=='admin':
            if len(cmd)<3 or not cmd[1].isdigit():
                return 0, 'Invalid argument. example: update 11250 qq:1716677 email:1716677@qq.com \n'
            userinfo=dbinfo.getuserinfo(int(cmd[1]))
            if len(userinfo)==0: 
                return 0,'Can not find port[%d] record!\n' % int(cmd[1])
            userinfo,msg=param2dict(cmd,2,userinfo)
            if msg: return 0,msg
            port=dbinfo.update(int(cmd[1]),userinfo);
            if port==0:
                return 0,'Fail when update user information to db.\n'
            log.msg('port[%d] is updated. New user information[%s].' % (port,str(userinfo)))
            return 0,'port[%d] is updated. New user information[%s]. \n' % (port,str(userinfo))
  
        if cmd[0]=='passwd':
            if len(cmd)<3 or not cmd[1].isdigit():
                return 0,'Invalid argument. usage: passwd <port> <new password>.  example: passwd 11250 aaaa \n'
            if self.usertype=='user' and cmd[1]!=self.avaterId:
                return 0, 'You can only change password for logined id.\n'
            userinfo=dbinfo.getuserinfo(int(cmd[1]));
            if len(userinfo)==0: 
                return 0, 'Fail,Can not find d-port[%d].\n' % int(cmd[1])
            userinfo={}
            userinfo['pass']=cmd[2]
            port=dbinfo.update(int(cmd[1]),userinfo);
            if port==0:
                return 0,'Fail when change d-port password.\n'
            log.msg('port[%d] password is changed to db.New userinfo[%s].' % (port,str(userinfo)))
            if not cfgfile.portpass().has_key(str(port)):
                return 0,'Can not find f-port[%d] .\n' % port
            cfgfile.portpass()[str(port)]=userinfo['pass'];
            cfgfile.save_config();
            signalpass(port); 
            log.msg('Port[%s] password is changed to config file. New password is [%s]' % (port,userinfo['pass']))
            return 0,'port[%d] password is changed! Active. \n' % (port)
  
        if cmd[0]=='reset':
            if len(cmd)<2 or not cmd[1].isdigit():
                return 0,'Invalid argument. usage: reset <port>. example: reset 11250\n'
            if self.usertype=='user' and cmd[1]!=self.avaterId:
                return 0,'You can only reset the port of yourself.\n'
            pids=get_pid("shadowsocks-server")
            #send signal ,to reset port listener
            for i in pids 
                os.kill(i,signal.SIGUSR1)            
            return 0,''

        if cmd[0]=='expdate':
            if len(cmd)<2 or not cmd[1].isdigit():
                return 1,'Invalid argument format'
            if self.usertype=='user' and cmd[1]!=self.avaterId:
                return 1,'The port you queryed shold be logined.'
            userinfo=dbinfo.getuserinfo(int(cmd[1]));
            if len(userinfo)==0: 
                return 1, 'Fail,Can not find d-port[%d].' % int(cmd[1])
            else 
                return 0, userinfo['enddate']
        
        #pay a port. update db status to 'pay', check config file and create if not exists
        if cmd[0]=='pay' and self.usertype=='admin':
            if len(cmd)!=3 or not cmd[1].isdigit() or not cmd[2].isdigit():
                return 0,'Invalid argument.Usage:pay <port> <months>  Example:pay 11250 12  (Means port 11250 expire date will add 12 months). \n'
            userinfo=dbinfo.getuserinfo(int(cmd[1]));
            if len(userinfo)==0:
                return 0,'Can not find port[%d].\n' % int(cmd[1])
            log.msg('Find port[%s], userinfo[%s].' % (cmd[1],str(userinfo)));
            #status change to pay,and update end date;
            if userinfo['status']=='test':
                end=datetime.strptime(userinfo['startdate'],'%Y%m%d').date()
            else:
                end=datetime.strptime(userinfo['enddate'],'%Y%m%d').date()
            userinfo['status']='pay'
            end=sstime.monthdelta(end,int(cmd[2]));
            end=datetime.strftime(end,'%Y%m%d')
            userinfo['enddate']=end;
            log.msg('Update port[%s] userinfo to new[%s].' % (cmd[1],str(userinfo)));
            #update to db
            port=dbinfo.update(int(cmd[1]),userinfo);
            if port==0: 
                return 0,'Fail. May be the port is not found. please add it first.\n'
            #update config file
            cfgfile.portpass()[str(port)]=userinfo['pass'];
            cfgfile.save_config();
            log.msg('pay command. port[%s] is payed for [%s] months. New user infomation[%s]\n' % (cmd[1],cmd[2],str(userinfo)));
            return 0,'Ok. the port[%s] is payed for [%s] months. New end date[%s]\n' % (cmd[1],cmd[2],userinfo['enddate'])
  
        #set status 'stop' in db, and delete port from config file 
        if cmd[0]=='stop' and self.usertype=='admin':
            ret,msg=self.chkarg(cmd,2)
            if not ret: return 0,msg
            if not cmd[1].isdigit():
                return 0,'Command paramater should be a port number! Such as: pay 11250. \n'
            return stopport(int(cmd[1]),dbinfo,cfgfile)
    
        #del userinfo from db and config file
        if cmd[0]=='del' and self.usertype=='admin':
            ret,msg=self.chkarg(cmd,2)
            if not ret: return 0,msg
            if not cmd[1].isdigit(): 
                return 0,'Fail,invalid argument, it should be a num. example: del 11001.\n'
            port,rows=dbinfo.delete(int(cmd[1]));
            if port==0:
                log.msg('Port[%s] is not found in db!' % port)
            #    self.transport.write('Fail,delete user from db fail. Maybe the port[%s] can not be found.\n' % cmd[1]);
            #    return;
            elif port==-1:
                return 0,'Fail,Can not delete not stoped port! Please stop it first!\n'
            else: 
                log.msg('Port[%s] is deleted from db!' % port)
            port=int(cmd[1]);
            #delete port from config file, if not exist, not care
            cfgfile.del_port(port);
            cfgfile.save_config();
            log.msg('Port[%d] is deleted from config file!' % port)
            return 0,'OK,port[%d] is deleted. Userinfo is %s.\n' % (port,str(rows))
  
        if cmd[0]=='restart' and self.usertype=='admin':
            (status,output)=cfgfile.commit()
            log.msg('Commit,status(%s),output(%s)' % (status,output)) 
            if status>0: 
                return 0,'Fail,Restart server error. \n%s\n' % output
            else:
                return 0,'Ok,restart server done.\n%s\n' % output
  
        if cmd[0]=='cclp' and self.usertype=='admin':
            (status,output)=commands.getstatusoutput('./cclp')
            log.msg('Run cclp,status(%s)' % status) 
            if status>0:
                return 0,'Fail,run cclp error. \n%s\n' % output
            else:
                return 0,'Ok,\n%s\n' % output
  
        return 0,'Fail,Unknown command.\n'  #Command should be "add","stop","del","list","find","exit","count","commit"\n');

