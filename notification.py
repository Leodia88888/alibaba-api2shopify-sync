import smtplib
from email.mime.text import MIMEText
import logging
from config import EMAIL_ALERT

def send_email_alert(subject, message, to_email=EMAIL_ALERT):
    # 示例：使用 SMTP 发送报警邮件
    try:
        smtp_server = "smtp.example.com"
        smtp_port = 587
        smtp_user = "your_email@example.com"
        smtp_password = "your_password"

        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
        logging.info("报警邮件已发送到 %s", to_email)
    except Exception as e:
        logging.error("发送报警邮件失败: %s", e)