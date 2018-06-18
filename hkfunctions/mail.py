import smtplib
from email.message import EmailMessage


def send_mail(server, from_, to, subject, **kwargs):
    """
    write docstring
    """
    messageHeader = kwargs.pop("messageHeader", None)
    messageBody = kwargs.pop("messageBody", None)
    if messageHeader and messageBody:
        message = messageHeader + "\n\n" + messageBody
    elif messageHeader:
        message = messageHeader
    elif messageBody:
        message = messageBody
    else:
        message = ""
    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = subject
    msg["From"] = from_
    msg["To"] = to
    s = smtplib.SMTP(server)
    try:
        s.send_message(msg)
    except Exception:
        s.quit()
    s.quit()
