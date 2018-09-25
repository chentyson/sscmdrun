#coding=utf-8
import sys
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor,task
from ss import cfgshell
import db
from twisted.cred import checkers,credentials,portal
from zope.interface import Interface,implements
from SscmdAvater import SscmdAvater,ISscmdAvaterInterface
from twisted.internet.threads import deferToThread
import mailcheck
import sstime
from datetime import datetime
import base64

#define admin user and pass
_admin='tyson'
_newreg='newreg'
_newregpass='newregPass'

_usertype={}
_usertype[_newreg]='reg'

class SscmdRealm(object):
    implements(portal.IRealm)

    def requestAvatar(self,avaterId, mind, *interfaces):
        if ISscmdAvaterInterface in interfaces:
            log.msg('requestAvater: %s' % avaterId);
            avater=SscmdAvater()
            avater.avaterId=avaterId
            avater.usertype=_usertype[avaterId]
            return ISscmdAvaterInterface,avater,avater.logout

        raise NotImplementedError('''''This Realm only support IEchoAvatarInterface''')


class CmdProtocol(LineReceiver):

    delimiter = '\n'

    def __init__(self):
        log.msg('init cmdProtocol...')
        self._avater = None

    def connectionMade(self):
        self.client_ip = self.transport.getPeer()
        log.msg("Client connection from %s" % self.client_ip)
        if len(self.factory.clients) >= self.factory.clients_max:
            #kick connection timeout
            for time,trans in self.factory.clients.values():
               if (datetime.now()-time).seconds > 30:
                   trans.loseConnection()
                   self.factory.clients[self.client_ip]=(datetime.now(),self.transport)
                   return
            if len(self.factory.clients)>=self.factory.clients_max:
                log.msg("Too many connections. bye !")
                self.client_ip = None
                self.transport.loseConnection()
                return
        self.factory.clients[self.client_ip]=(datetime.now(),self.transport)

    def connectionLost(self, reason):
        log.msg('Lost client connection. Reason: %s' % reason)
        if self.client_ip:
            del self.factory.clients[self.client_ip]

    def lineReceived(self, line):
        log.msg('Cmd received from %s,%s' % (self.client_ip, line))
        if line.startswith('tysondebug'):
            line = line[11:]
        #为兼容客户端对expdate 和 端口登录仍使用原没用 b64编码
        elif line.startwith('expdate') or line[:5].isdigit():
            log.msg(' to compatible with client...'
        else:
            line = base64.b64decode(line)
        log.msg('Decode line:%s' % line)
        if not self._avater:
            avater=line.strip().split(' ')
            if len(avater)!=2:
               self.sendLine('Input user name and password(aplite by apace):');
            else:
               user=avater[0]
               #if avater[0].isdigit():
               #   user=str(int(avater[0]) + 20000)
               self.login(user,avater[1])
            return

        #login ok , get a avater
        #self.transport.write('-----------------------\n')
        #process command line
        if self.factory.cfgfile == None or self.factory.dbinfo == None:
            log.msg("Can not get port config file or db file!")
            self.transport.write('Fatal error! Command fail!\n')
            return
        ret,msg=self._avater.processCmd(line,self.factory.dbinfo,self.factory.cfgfile, self.factory)
        #output
        if ret==0 and msg:
            log.msg(msg)
            self.sendLine(msg)
        elif ret==-1:
            log.msg(msg)
            if msg: self.sendLine(msg)
            self.transport.loseConnection()
            return
    #      self.transport.write('=======================\n');

    #201
    def _cbLoginOK(self,(interface,avater,logout)):
        log.msg('login ok.')
        self._avater=avater
        self.sendLine('{"cmd":"201","id":"%s","res":"ok","msg":"Welcome %s! What can I do for you?"}' % (avater.avaterId,avater.avaterId))

    def _cbLoginFail(self,fail):
        log.msg('login failed!')
        self.sendLine('"cmd":"201","res":"fail","msg":"Login failed!"}')
        self.transport.loseConnection()

    def login(self,user,password):
        log.msg('Prepare to login! username[%s],password[%s]' % (user,password))
        d=self.factory._portal.login(
              credentials.UsernamePassword(user,password),
              None,
              ISscmdAvaterInterface)
        d.addCallbacks(self._cbLoginOK, self._cbLoginFail)

class MyFactory(ServerFactory):
    protocol = CmdProtocol

    def reloadUser(self):
        log.msg('reload user infomation...');
        self.checker.users={};
        self.checker.addUser( _newreg,_newregpass )
        #add port/password
        userinfo={}
        cols,rows=self.dbinfo.find(userinfo);
        for i in range(len(rows)):
            port,passwd=rows[i][:2]
            self.checker.addUser(str(port),passwd)
            _usertype[str(port)]='user'

        #add reg/password
        self.regid={}
        userinfo={'status':'ok'}
        cols,rows=self.dbinfo.regfind(userinfo);
        for i in range(len(rows)):
            email,passwd=rows[i][:2]
            self.checker.addUser(email,passwd)
            self.regid[email]=passwd
            if email==_admin:
                _usertype[email]='admin'
            else:
                _usertype[email]='login'

    def getaportal(self):
        log.msg('Get a portal...' )
        aportal=portal.Portal(SscmdRealm())
        self.reloadUser();
        aportal.registerChecker(self.checker)
        return aportal

    def __init__(self, clients_max=1):
        log.msg('Now init sscmd factory...')
        self.clients_max = clients_max
        self.clients = {}
        self.dbinfo=db.ssdb()
        self.cfgfile=cfgshell.cfgfile()
        self.checker=checkers.InMemoryUsernamePasswordDatabaseDontUse()
        self._portal = self.getaportal()
        self.regid={}
        
    def accountcheck(self):
        #if sstime.now().strftime('%H')='00':
	    
        if sstime.now().strftime('%H')!='10': return  #at 10 o'clock evary day 

        log.msg('Checking port status and mail to user if port is expired/will expire/testing...')
        #first, stop all expired port,and mail to user
        mailcheck.stopexp(self)
        #then,warn all who will expired in 3 days
        mailcheck.mailwillexp(self)
        #then,mail to testing user expired after 2 days
        mailcheck.mailtest(self)
        #mail to stoped user to buy
        mailcheck.mailstoped(self)
    
log.startLogging(sys.stdout)
#log.startLogging(open(r"./sscmd.log",'a'))
myfac=MyFactory(20)
reactor.listenTCP(39125, myfac)
t=task.LoopingCall(myfac.accountcheck)
#check every 1h
t.start(3600)
#t.start(20)

reactor.run()
