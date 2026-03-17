import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email(client_id: int, raw_password: str) -> None:
    """Send a welcome email with login credentials to a newly created client."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        client = User.objects.get(pk=client_id)
    except User.DoesNotExist:
        logger.error("send_welcome_email: client %s not found", client_id)
        return

    if not client.email:
        logger.warning("send_welcome_email: client %s has no email address", client_id)
        return

    subject = "Welcome to BI System — Your Account is Ready"
    message = (
        f"Hello {client.username},\n\n"
        f"Your account has been created on BI System. Here are your login credentials:\n\n"
        f"  Username : {client.username}\n"
        f"  Password : {raw_password}\n\n"
        f"Please log in and change your password as soon as possible.\n\n"
        f"Best regards,\n"
        f"The BI System Team"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[client.email],
        fail_silently=False,
    )
    logger.info("Welcome email sent to %s (client_id=%s)", client.email, client_id)
