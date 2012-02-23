from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_base64
from smtplib import SMTP


def send_email(send_from, send_to, text, subject, files=[], server='localhost'):

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = ', '.join(send_to)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    for f in files:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(f, 'rb').read())
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % basename(f))
        encode_base64(part)
        msg.attach(part)

    smtp = SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
