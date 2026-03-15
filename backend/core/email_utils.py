import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import ssl

def send_reset_email(to_email: str, reset_link: str):
    smtp_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    port = int(os.environ.get("MAIL_PORT", 587))
    sender_email = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD", "yqsr kynw tzqh jbyr")
    
    if not sender_email:
        print("Cảnh báo: MAIL_USERNAME chưa được cấu hình!")
        sender_email = "your_email@gmail.com" # Placeholder

    message = MIMEMultipart("alternative")
    message["Subject"] = "Yêu cầu khôi phục mật khẩu - DNC Chatbot"
    message["From"] = sender_email
    message["To"] = to_email

    text = f"""\
Xin chào,
Bạn vừa yêu cầu khôi phục mật khẩu cho tài khoản tại DNC Chatbot.
Vui lòng truy cập đường link sau để đặt lại mật khẩu của bạn:
{reset_link}

Nếu bạn không yêu cầu, vui lòng bỏ qua email này.
"""
    
    html = f"""\
    <html>
      <body>
        <p>Xin chào,<br><br>
           Bạn vừa yêu cầu khôi phục mật khẩu cho tài khoản tại <b>DNC Chatbot</b>.
        </p>
        <p>
           Vui lòng click vào nút bên dưới để đặt lại mật khẩu:
        </p>
        <p>
            <a href="{reset_link}" style="padding: 10px 20px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px;">Đặt lại mật khẩu</a>
        </p>
        <p>Hoặc truy cập link sau: {reset_link}</p>
        <p><i>Nếu bạn không yêu cầu, vui lòng bỏ qua email này.</i></p>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, message.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        raise e
    finally:
        server.quit()
