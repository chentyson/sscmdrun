#coding=utf-8
import smtplib
from email.mime.text import MIMEText
from email.header import Header

from datetime import datetime
import sstime
from config import config
from twisted.python import log
from email.utils import formataddr


my_comp='震撼科技'
my_sender='info@boosoo.cn'    # 发件人邮箱账号
my_pass = 'Zhenhan1716677'  # 发件人邮箱密码
my_smtpserver='smtp.mxhichina.com'  #发件服务器地址
my_smtpport=465

def mail(subject,text_content,html_content,my_user):
    ret=True
    #msg['From'] = Header(formataddr([my_comp,my_sender]) 'utf-8')
    #msg['To'] =  Header(formataddr(["震撼用户",my_user]), 'utf-8')
    #msg['Subject'] = Header(subject, 'utf-8')
    try:
        if html_content=='':
            # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
            msg = MIMEText(text_content, 'plain', 'utf-8')
        else:
            msg=MIMEText(html_content,'html','utf-8')

        msg['From']=formataddr([my_comp,my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To']=formataddr([my_user,my_user])          # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Bcc']='tyson@boosoo.cn'
        msg['Subject']=subject                # 邮件的主题，也可以说是标题
        
        server=smtplib.SMTP_SSL(my_smtpserver, my_smtpport)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender,[my_user,],msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception as e:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret=False
        log.err('mail exception:%s' % e.message)
        log.err()
    return ret

#def mail(subject, text_content, html_content, email):
#    message = MIMEText(html_content,'html','utf-8')
#    message['From'] = Header("震撼科技<1716677@qq.com>",'utf-8')
#    message['To'] = Header(
#    msg = EmailMultiAlternatives(subject, text_content, '震撼科技<1716677@qq.com>', [email,'1716677@qq.com'])
#    msg.attach_alternative(html_content, "text/html")
#    msg.send()
    

def mailwillexp(cols,rows):
    subject = u'震撼网络服务即将到期续费提醒（%d）'
    text_content = u'尊敬的震撼网络用户：\n    您所使用的以下震撼网络账户：\n\n      端口:%d\n    服务器:%s\n账户到期日:%s\n\n    即将到期，届时网络服务将自动停止。为了不影响您的正常使用，特提醒您提前续费。以下为续费/购买的淘宝链接:\n\n    https://item.taobao.com/item.htm?id=537154137831 \n\n    注意：在拍入的商品备注栏务必填写您所续费的端口号，以便工作>人员为您端口自动续期。'
    html_content = u'<!DOCTYPE html><html><body>尊敬的震撼网络用户，您所使用的以下震撼网络账户：<br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务器端口:<b>%d</b><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务器地址:<b>%s</b><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp账户到期日:<b>%s</b><br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp即将在&nbsp<b>%d天</b>&nbsp后到期>，届时网络服务将自动停止，为了不影响您的正常使用，特提醒您提前续费。请点击下方震撼网络账户续费淘宝链接进行续费续期：<br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp<a href="https://item.taobao.com/item.htm?id=537154137831"><b>https://item.taobao.com/item.htm?id=537154137831</b></a> <br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp注意：在拍入>商品时，请<b>务必在备注栏填写您所续费的端口号</b>，以便工作人员为您端口自动续期。<br><br>震撼科技&nbsp&nbsp QQ:1716677<br>祝使用愉快！</body></html>'
    
    message = MIMEText(html_content,'html','utf-8')

    for row in rows:
        end=datetime.strptime(row[cols.index('enddate')],'%Y%m%d')
        end=end.replace(tzinfo=sstime.tz)
        days=(end-sstime.now()).days+1
        #mail to user every 3 days if days>20, mail every 2 days if days>10, mail every day if days<=10
        if (days>10 and days%2==0) or (days<=10):
            port=int(row[cols.index('port')])
            enddate=end.strftime('%Y-%m-%d')
            email=row[cols.index('email')]

            subject = subject % port
            text_content = text_content % (port,config.serverip,enddate)
            html_content = html_content % (port,config.serverip,enddate,days)
            mail(subject,text_content,html_content,email)

def mailtest(cols,rows):
    subject = u'震撼网络试用账户购买提醒（%d）'
    text_content = u'尊敬的震撼网络临时用户，您目前正在试用以下震撼网络服务：\n\n    服务器端口: %d\n    服务器地址: %s\n    试用开通日: %s\n\n如试用满意，您可通过点击下方震撼网络账户淘宝购买链接购买并自动开通正式账户：\n\n    <a href="https://item.taobao.com/item.htm?id=537154137831"><b>https://item.taobao.com/item.htm?id=537154137831</b></a>\n\n注意：在拍入商品时请 务必在备注栏填写您所购买的端口号，以便工作人员为您及时开通服务。\n\n震撼科技  QQ:1716677 \n祝使用愉快!'

    html_content = u'<!DOCTYPE html><html><body>尊敬的震撼网络临时用户，您目前正在试用以下震撼网络服务：<br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务器端口:&nbsp<b>%d</b><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务器地址:&nbsp<b>%s</b><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务开通日:&nbsp<b>%s</b><br><br>如试用满意，您可通过点击下方震撼网络账户淘宝购买链接购买并自动开通正式账户：<br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp<a href="https://item.taobao.com/item.htm?id=537154137831"><b>https://item.taobao.com/item.htm?id=537154137831</b></a> <br><br>注意：在拍入商品时请&nbsp<b>务必在备注栏填写您所购买的端口号</b>，以便工作人员为您及时开通服务。<br><br>震撼科技&nbsp&nbsp QQ:1716677<br>祝使用愉快！</body></html>'
    
    for row in rows:
        port=int(row[cols.index('port')])
        startdate=row[cols.index('startdate')]
        email=row[cols.index('email')]
        
        subject = subject % port
        text_content = text_content % (port,config.serverip,startdate)
        html_content = html_content % (port,config.serverip,startdate)
        mail(subject,text_content,html_content,email)


def mailexp(cols,rows):
    subject = u'震撼网络服务到期暂停通知（%d）'
    text_content = u'尊敬的震撼网络用户，您所使用的以下震撼网络账户：\n\n    服务器端口: %d\n    服务器地址: %s\n    账户到期日: %s\n\n    已经到期，服务已自动停止，如果您对我们的服务比较满意并且希望继续使用震撼网络服务，可点击下方淘宝链接进行续费续期并自动开通：\n\n    https://item.taobao.com/item.htm?id=537154137831 \n\n     注意：在拍入商品时，请 务必在备注栏填写您所续费的端口号，以便工作人员为您端口自动续期。\n\n震撼科技  QQ:1716677\n祝使用愉快！'

    html_content = u'<!DOCTYPE html><html><body>尊敬的震撼网络用户，您所使用的以下震撼网络账户：<br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务器端口:<b>%d</b><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务器地址:<b>%s</b><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp账户到期日:<b>%s</b><br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp已经到期，服务已自动停止，如果您对我们的服务比较满意并且希望继续使用震撼网络服务，可点击下方淘宝链接进行续费续期并自动开通：<br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp	<a href="https://item.taobao.com/item.htm?id=537154137831"><b>https://item.taobao.com/item.htm?id=537154137831</b></a> <br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp注意：在拍入商品时，请<b>务必在备注栏填写您所续费的端口号</b>，以便工作人员为您端口自动续期。<br><br>震撼科技&nbsp&nbsp QQ:1716677<br>祝使用愉快！</body></html>'
    
    for row in rows:
        port=int(row[cols.index('port')])
        enddate=row[cols.index('enddate')]
        email=row[cols.index('email')]
        subject = subject % port
        text_content = text_content % (port,config.serverip,enddate)
        html_content = html_content % (port,config.serverip,enddate)
        mail(subject,text_content,html_content,email)

def mailstoped(cols,rows):
    emails={}
    lastdate=0
    for row in rows:
        email=row[cols.index('email')]
        port=int(row[cols.index('port')])
        enddate=row[cols.index('enddate')]

        if not emails.has_key(email): emails[email]=[]
        emails[email].append((port,enddate))
    if len(emails)==0: return

    subject = u'震撼翻墙服务已过期，继续使用吗？'
    for email in emails:
        ports=u'<br>'.join(u'&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp服务器端口:<b>%d</b>&nbsp&nbsp&nbsp账户到期日:&nbsp<b>%s</b>' % (port,enddate) for port,enddate in emails[email])
        text_content = u'  震撼网络用户您好，您所使用账户已经过期！如果您还有使用该服务的需求，可直接点击下方续费淘宝链接进行重新开通，只要您在商品拍入的备注写明您续费的端口，我们将会自动按备注端口按续费日为您重新开通，端口/密码无需变更：\n\n https://item.taobao.com/item.htm?id=537154137831 \n\n震撼网络服务是专为外贸商务提供的一种网络中转服务，速度快、运行稳定，并同时提供电脑Windows版本、苹果Macbook版本、手机安卓和苹果IOS版本的软件，可同时在电脑和手机等移动端在线使用。我们为个人用户同时也为公司多人同时在线使用提供不同的账户版本。咨询可联系下方QQ，或直接回复邮件。\n\n 震撼科技  QQ:1716677 \n祝使用愉快！\n'
        html_content = u'<!DOCTYPE html><html><body>震撼网络用户您好，您使用的下列账户已经过期：<br><br>%s<br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp您还需要该服务吗？ 如果需要，可点击下方链接重新续费开通（注意在拍入的备注栏写明账户端口），我们将会自动按备注端口为您重新开通，端口/密码无需变更：<br>	&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp<a href="https://item.taobao.com/item.htm?id=537154137831"><b>https://item.taobao.com/item.htm?id=537154137831</b></a> <br><br>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp震撼网络服务是专为外贸提供的网络中转解决方案，速度快、运行稳定，服务期内提供7×24小时售后技术支持。 我们同时提供Windows版本、Macbook版本、手机的安卓和苹果版本软件。可同时在电脑和手机使用。同时提供个人版和多人同时在线的多人版本。咨询可联系下方QQ，或直接回复邮件。<br><br>如您不再希望收到收件提醒，可直接回复内容为“不再提醒”的邮件即可！<br><br> 震撼科技&nbsp&nbsp QQ:1716677<br>祝使用愉快！</body></html>' % ports
        mail(subject,text_content,html_content,email)
