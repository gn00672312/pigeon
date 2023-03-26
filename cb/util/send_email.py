
import smtplib
import os

from module import log

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


# Constants used in configuration.
ZIP = 'zip'
GZIP = 'gzip'
BZ2 ='bz2'


from .config import load as load_config
MAIL_SETTINGS = load_config("mail_settings.conf")

from .filter import translate_tags


def send(subject, content, receivers=None, group=None):
    if receivers is None:
        if group is None:
            receivers = MAIL_SETTINGS['MAIL_RECEIVERS']['default']
        else:
            receivers = MAIL_SETTINGS['MAIL_RECEIVERS'][group]

    if receivers:
        if '<html>' not in content:
            content += "\n\n\n*** 本信件由系統自動發出，請勿直接回覆 ***\n"

        msg = MIMEMultipart()
        msg['From'] = MAIL_SETTINGS['MAIL_SENDER']
        msg['To'] = ','.join(receivers)

        if isinstance(subject, bytes):
            subject = subject.encode('UTF-8')
        msg['Subject'] = Header(subject, 'UTF-8').encode()

        if isinstance(content, bytes):
            content = content.encode('UTF-8')
        if '<html>' in content:
            msg.attach(MIMEText(content, 'html', 'UTF-8'))
        else:
            msg.attach(MIMEText(content, 'plain', 'UTF-8'))

        server = smtplib.SMTP(MAIL_SETTINGS['SMTP_SERVER'])

        if MAIL_SETTINGS['SMTP_STARTTLS_MODE']:
            server.starttls()
        if MAIL_SETTINGS['SMTP_EHLO_MODE']:
            server.ehlo()

        if MAIL_SETTINGS['SMTP_LOGIN']:
            server.login(MAIL_SETTINGS['SMTP_LOGIN'], MAIL_SETTINGS['SMTP_PWD'])

        text = msg.as_string()
        server.sendmail(MAIL_SETTINGS['MAIL_SENDER'], receivers, text)
        server.quit()
    else:
        log.warning("no mail receivers")
