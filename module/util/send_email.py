from datetime import datetime
import smtplib
import os

from module import log

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.base import MIMEBase
from email import encoders


# Constants used in configuration.
ZIP = 'zip'
GZIP = 'gzip'
BZ2 ='bz2'


from .config import load as load_config


def send(subject, content, receivers=None, group=None, attachment_files=None):
    MAIL_SETTINGS = load_config("mail_settings.conf")

    if receivers is not None:
        try:
            if not isinstance(receivers, (list, tuple)):
                receivers = receivers.split(',')
        except:
            receivers = None

    log.diag('send mail to', receivers)
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
            subject = subject.decode('UTF-8')
        msg['Subject'] = Header(subject, 'UTF-8').encode()

        if isinstance(attachment_files, (list, tuple)) and len(attachment_files):
            for _file in attachment_files:
                try:
                    part = MIMEBase('application', 'octet-stream')
                    attachment = open(_file, "rb")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=os.path.basename(_file)
                    )

                    msg.attach(part)
                except:
                    log.exception()

        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        if '<html>' in content:
            msg.attach(MIMEText(content, 'html', 'UTF-8'))
        else:
            msg.attach(MIMEText(content, 'plain', 'UTF-8'))

        if "SMTP_SERVER" in MAIL_SETTINGS:
            if "SMTP_PORT" in MAIL_SETTINGS:
                server = smtplib.SMTP(MAIL_SETTINGS['SMTP_SERVER'],
                                      MAIL_SETTINGS['SMTP_PORT'])
            else:
                server = smtplib.SMTP(MAIL_SETTINGS['SMTP_SERVER'])

            if "SMTP_STARTTLS_MODE" in MAIL_SETTINGS and MAIL_SETTINGS['SMTP_STARTTLS_MODE']:
                server.starttls()
            if "SMTP_EHLO_MODE" in MAIL_SETTINGS and MAIL_SETTINGS['SMTP_EHLO_MODE']:
                server.ehlo()

            if "SMTP_LOGIN" in MAIL_SETTINGS and "SMTP_PWD" in MAIL_SETTINGS:
                server.login(MAIL_SETTINGS['SMTP_LOGIN'], MAIL_SETTINGS['SMTP_PWD'])

            text = msg.as_string()
            status = server.sendmail(MAIL_SETTINGS['MAIL_SENDER'], receivers, text)
            server.quit()
            return status

    else:
        log.warning("no mail receivers")
        return False
