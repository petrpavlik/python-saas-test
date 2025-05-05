import logging
from typing import Protocol

from indiepitcher import EmailBodyFormat, SendEmail

from app.indiepitcher import (
    get_async_indiepitcher_client,
    is_async_indiepitcher_client_initialized,
)


class EmailServiceProtocol(Protocol):
    async def send_email(
        self,
        to: str,
        subject: str,
        markdownBody: str,
    ) -> None: ...


class MockEmailService(EmailServiceProtocol):
    async def send_email(
        self,
        to: str,
        subject: str,
        markdownBody: str,
    ) -> None:
        logger = logging.getLogger(__name__)
        logger.info(
            f"Mock sendEmail called with to: {to}, subject: {subject}, markdownBody: {markdownBody}"
        )


class IndiePitcherEmailService(EmailServiceProtocol):
    async def send_email(
        self,
        to: str,
        subject: str,
        markdownBody: str,
    ) -> None:
        client = get_async_indiepitcher_client()
        await client.send_email(
            SendEmail(
                to=to,
                subject=subject,
                body=markdownBody,
                body_format=EmailBodyFormat.MARKDOWN,
            )
        )


def get_email_service() -> EmailServiceProtocol:
    if is_async_indiepitcher_client_initialized():
        return IndiePitcherEmailService()
    else:
        return MockEmailService()


__all__ = ["EmailServiceProtocol", "get_email_service"]
