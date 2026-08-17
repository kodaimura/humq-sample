from abc import ABC, abstractmethod
import smtplib
from email.message import EmailMessage
from typing import Iterable

from app.core.config import config


def _normalize_recipients(value: str | Iterable[str] | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


class Mailer(ABC):
    @abstractmethod
    def send(
        self,
        to: str | Iterable[str],
        subject: str,
        body: str,
        cc: str | Iterable[str] | None = None,
    ) -> None:
        pass


class SMTPMailer(Mailer):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        use_tls: bool,
        from_address: str,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address

    def send(
        self,
        to: str | Iterable[str],
        subject: str,
        body: str,
        cc: str | Iterable[str] | None = None,
    ) -> None:
        recipients = _normalize_recipients(to)
        cc_recipients = _normalize_recipients(cc)

        if not recipients:
            return

        message = EmailMessage()
        message["From"] = self.from_address
        message["To"] = ", ".join(recipients)
        if cc_recipients:
            message["Cc"] = ", ".join(cc_recipients)
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.send_message(message)


class MailHogMailer(SMTPMailer):
    def __init__(self):
        super().__init__(
            host="mailhog",
            port=1025,
            username=None,
            password=None,
            use_tls=False,
            from_address="no-reply@example.local",
        )


def get_mailer() -> Mailer:
    if config.MAIL_PROVIDER == "mailhog":
        return MailHogMailer()

    if config.MAIL_PROVIDER == "smtp":
        if not config.SMTP_HOST:
            raise ValueError("SMTP_HOST is required when MAIL_PROVIDER=smtp")
        return SMTPMailer(
            host=config.SMTP_HOST,
            port=config.SMTP_PORT,
            username=config.SMTP_USERNAME,
            password=config.SMTP_PASSWORD,
            use_tls=config.SMTP_USE_TLS,
            from_address=config.MAIL_FROM,
        )

    raise ValueError(f"unsupported mail provider: {config.MAIL_PROVIDER}")
