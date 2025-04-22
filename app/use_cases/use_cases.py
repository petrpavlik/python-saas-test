from app.models.profile import Profile
from app.service.email_service import EmailServiceProtocol


async def sendWelcomeEmail(profile: Profile, emailService: EmailServiceProtocol):
    await emailService.send_email(
        to=profile.email,
        subject="Welcome to our IndiePitcher!",
        markdownBody=f"""
        # Welcome to IndiePitcher!
        Hi {profile.name or "there"},
        Thank you for signing up for IndiePitcher! We're excited to have you on board.
        If you have any questions or need assistance, feel free to reach out to us.
        Best,
        The IndiePitcher Team
        """,
    )
