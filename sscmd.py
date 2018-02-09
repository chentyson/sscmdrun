#coding=utf-8
import sys
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.internet import reactor,task
from ss import cfgshell
import db
from twisted.cred import checkers,credentials,portal
from zope.interface import Interface
from SscmdAvater import SscmdAvater,SscmdRealm,ISscmdAvaterInterface,_adminuser,_adminpass
from twisted.internet.threads import deferToThread
import mailcheck
import sstime
from datetime import datetime

class CmdProtocol(LineReceiver):

  delimiter = '\n'
  def __init__(self):
      log.msg('now init cmdProtocol...')
      self._avater=None
 
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
      log.msg('Cmd received from %s : %s' % (self.client_ip, line))
      if not self._avater:
          avater=line.strip().split(' ')
          if len(avater)!=2:
             self.sendLine('Input user name and password(aplite by apace):');
          else:
             self.login(avater[0],avater[1])
          return;
      #login ok , get a avater
      #self.transport.write('-----------------------\n')
      #process command line
      if self.factory.cfgfile==None or self.factory.dbinfo==None:
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
 
  def _cbLoginOK(self,(interface,avater,logout)):
      log.msg('login ok.')
      self._avater=avater
      self.sendLine('Welcome %s! What can I do for you?' % avater.avaterId)

  def _cbLoginFail(self,fail):
      log.msg('login failed!')
      self.sendLine('Login failed!' )
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
        self.checker.addUser( _adminuser,_adminpass )
        userinfo={}
        cols,rows=self.dbinfo.find(userinfo);
        for i in range(len(rows)):
            port,passwd=rows[i][:2]
            self.checker.addUser(str(port),passwd)
        
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
        
    def accountcheck(self):
        if sstime.now().strftime('%H')!='10': return  #at 10 o'clock evary day 

        log.msg('Checking port status and mail to user if port is expired/will expire/testing...')
        #first, stop all expired port,and mail to user
        mailcheck.stopexp(self)
        #then,warn all who will expired in 3 days
        mailcheck.mailwillexp(self)
        #then,mail to testing user expired after 2 days
        mailcheck.mailtest(self)
        #mail to stoped user to buy
        #mailcheck.mailstoped(self)
    
log.startLogging(sys.stdout)
#log.startLogging(open(r"./sscmd.log",'a'))
myfac=MyFactory(2)
reactor.listenTCP(39125, myfac)
t=task.LoopingCall(myfac.accountcheck)
#check every 1h
t.start(3600)
#t.start(20)

reactor.run()
