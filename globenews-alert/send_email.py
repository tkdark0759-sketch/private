"""
Gmail SMTP를 이용한 이메일 전송 모듈.
Gmail 계정에서 '앱 비밀번호'를 발급받아 사용해야 합니다.
(일반 로그인 비밀번호는 보안 정책상 SMTP에서 거부됩니다)

앱 비밀번호 발급: https://myaccount.google.com/apppasswords
(2단계 인증이 켜져 있어야 앱 비밀번호 메뉴가 보입니다)
"""
import os
import smtplib
from email.mime.text import MIMEText

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
TO_ADDRESS = os.environ.get("ALERT_TO_EMAIL", GMAIL_ADDRESS)


def send_email(subject: str, html_body: str):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("[이메일 전송 스킵] GMAIL_ADDRESS / GMAIL_APP_PASSWORD 환경변수가 없습니다.")
        return

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_ADDRESS

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [TO_ADDRESS], msg.as_string())

    print("이메일 전송 성공")
