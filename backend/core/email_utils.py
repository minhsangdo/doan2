import os
import ssl
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

logger = logging.getLogger(__name__)

RESET_SUBJECT = "Yêu cầu khôi phục mật khẩu - DNC Chatbot"


def is_smtp_configured() -> bool:
    """Gmail SMTP: MAIL_USERNAME + MAIL_PASSWORD."""
    u = (os.environ.get("MAIL_USERNAME") or "").strip()
    p = (os.environ.get("MAIL_PASSWORD") or "").strip()
    return bool(u and p)


def is_resend_configured() -> bool:
    """Gửi qua HTTPS — chạy được trên Hugging Face Space (SMTP thường bị chặn/treo)."""
    return bool((os.environ.get("RESEND_API_KEY") or "").strip())


def is_email_sending_configured() -> bool:
    return is_resend_configured() or is_smtp_configured()


def _build_reset_bodies(reset_link: str) -> tuple[str, str]:
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
    return text, html


def _send_via_resend(to_email: str, subject: str, html: str, text: str, api_key: str) -> None:
    """
    https://resend.com/docs/api-reference/emails/send-email
    Trên HF Space nên dùng Resend thay SMTP (cổng 587 tới Gmail thường timeout).
    """
    from_addr = (os.environ.get("RESEND_FROM") or "DNC Chatbot <onboarding@resend.dev>").strip()
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "html": html,
            "text": text,
        },
        timeout=25.0,
    )
    if r.status_code >= 400:
        logger.error("Resend API %s: %s", r.status_code, r.text)
        # Trả lỗi rõ ràng cho API (Resend trả JSON message)
        try:
            err_body = r.json()
            err_msg = err_body.get("message") or err_body.get("name") or r.text
        except Exception:
            err_msg = r.text or str(r.status_code)
        raise RuntimeError(f"RESEND_{r.status_code}: {err_msg}")
    r.raise_for_status()


def send_reset_email(to_email: str, reset_link: str) -> None:
    """
    Ưu tiên RESEND_API_KEY (HTTPS). Nếu không có thì dùng SMTP Gmail.
    """
    text, html = _build_reset_bodies(reset_link)

    resend_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if resend_key:
        _send_via_resend(to_email, RESET_SUBJECT, html, text, resend_key)
        logger.info("Đã gửi email đặt lại mật khẩu (Resend) tới %s", to_email)
        return

    if not is_smtp_configured():
        raise RuntimeError("SMTP_NOT_CONFIGURED")

    smtp_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com").strip()
    port = int(os.environ.get("MAIL_PORT", "587"))
    sender_email = os.environ.get("MAIL_USERNAME", "").strip()
    password = os.environ.get("MAIL_PASSWORD", "").strip()

    message = MIMEMultipart("alternative")
    message["Subject"] = RESET_SUBJECT
    message["From"] = sender_email
    message["To"] = to_email

    part1 = MIMEText(text, "plain", "utf-8")
    part2 = MIMEText(html, "html", "utf-8")
    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    server = None
    try:
        # Timeout ngắn để không treo UI quá lâu khi mạng chặn SMTP
        server = smtplib.SMTP(smtp_server, port, timeout=15)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, message.as_string())
        logger.info("Đã gửi email đặt lại mật khẩu (SMTP) tới %s", to_email)
    except Exception as e:
        logger.exception("Lỗi gửi email SMTP: %s", e)
        raise
    finally:
        if server is not None:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass
