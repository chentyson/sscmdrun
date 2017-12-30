import sys
sys.path.append('..')
import db
aa=db.ssdb()
print 'test add function.... '
print "-------------------------------"
print aa.add(11252,{})
print aa.add(11253,{'qq':'1716677','startdata':20170310,'status':'pay'})
print "=============================================="
print 'test find function....'
print "-------------------------------"
print "find({'status':'pay'})"
print "-------------------------------"
print aa.find({'status':'pay'})
print "=============================================="
print "find({})..."
print "-------------------------------"
print aa.find({})
print "=============================================="
print "find({'status':'test'})"
print "-------------------------------"
print aa.find({'status':'test'})
print "=============================================="
print "find({'qq':'171'})"
print "-------------------------------"
print aa.find({'qq':'171'})
print "=============================================="
print "find({'qq':'171','status':'pay'})"
print "-------------------------------"
print aa.find({'qq':'171','status':'pay'})
print "=============================================="
print "find({'startdate':'>20170101'})"
print "-------------------------------"
print aa.find({'startdate':'>20170101'})
print "=============================================="
print "update(11250,{'enddate':20180102})"
print "-------------------------------"
print aa.update(11250,{'enddate':20180103,'ips':5,'status':'pay'})

