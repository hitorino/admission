from django.conf import settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
def send_mail(subject, addr_to, content, html_content=''):
    '''Send an HTML email

    @param str subject
    @param str addr_to
    @param str content
    @return void
    '''
    if(html_content):
        msg = MIMEMultipart('alternative')
        msg_plaintext = MIMEText(content, 'plain')
        msg_html = MIMEText(html_content, 'html')
        msg.attach(msg_html)
        msg.attach(msg_plaintext)
    else:
        msg = MIMEText(content, 'plain')
    msg['Subject'] = subject
    msg['From'] = settings.YORINO_MAIL
    msg['To'] = addr_to
    smtp = smtplib.SMTP(settings.YORINO_SMTP)
    smtp.starttls()
    smtp.login(settings.YORINO_MAIL,settings.YORINO_PASS)
    smtp.send_message(msg)
    smtp.quit()

def new_commit(report):
    r=lambda a:a.replace('*','＊')
    subject = '任务：里区申请 '
    send_mail(subject, settings.YORINO_TASK, '* '+'  \r\n'.join(['问：%s  \r\n答%s'%(r(i),r(report[i])) for i in report.keys()]))
