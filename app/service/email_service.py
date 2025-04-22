import logging
from typing import Protocol


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


def get_email_service() -> EmailServiceProtocol:
    # In a real-world scenario, you would return an instance of the actual email service
    # For example, if you're using SendGrid:
    # return SendGridEmailService()
    return MockEmailService()


__all__ = ["EmailServiceProtocol", "get_email_service"]
