class config:
    serverip = 's00.boosoo.cn'
    proxyname = 'ph1'
    qq = '3556841256'
    portpre = '33'

    
    def getaport(self, port):
        return int(self.portpre + str(port)[len(self.portpre):5])

    def getaid(self, port):
        return self.proxyname + '-' + str(self.getaport(port))

    def getaserver(self):
        return self.proxyname + '.boosoo.cn'
