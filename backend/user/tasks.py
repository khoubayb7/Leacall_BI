import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_welcome_email(client_id: int, raw_password: str) -> None:
    """Send a welcome email with login credentials to a newly created client."""
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


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def discover_client_campaigns(self, client_id: int) -> dict:
    """
    Query LeaCall BI API for all campaigns and create datasources for the client.
    Called when client is created or synced.
    Returns dict with created_count, updated_count, error_message.
    """
    try:
        client = User.objects.get(pk=client_id, role=User.Role.CLIENT)
    except User.DoesNotExist:
        logger.error("discover_client_campaigns: client %s not found", client_id)
        return {"error_message": f"Client {client_id} not found"}

    # Import here to avoid circular imports
    from user.leacall_client import LeacallBIClient, LeacallAPIError
    from ETL.models import ClientDataSource

    try:
        bi_client = LeacallBIClient(client)
    except LeacallAPIError as e:
        logger.warning("discover_client_campaigns: cannot create BI client for %s: %s", client_id, e)
        return {"error_message": str(e)}

    # Fetch all campaigns from BI API (handles pagination)
    try:
        campaigns = bi_client.get_all_campaigns()
    except LeacallAPIError as e:
        logger.warning("discover_client_campaigns: BI API error for client %s: %s", client_id, e)
        return {"error_message": f"BI API error: {e}"}

    if not campaigns:
        logger.info("discover_client_campaigns: no campaigns found for client %s", client_id)
        return {"created_count": 0, "updated_count": 0, "message": "No campaigns in BI API"}

    created_count = 0
    updated_count = 0
    skipped_count = 0

    for campaign in campaigns:
        campaign_id = campaign.get('id')
        campaign_name = campaign.get('name', campaign_id)
        status = campaign.get('status')

        if not campaign_id:
            logger.warning("discover_client_campaigns: campaign missing id, skipping: %s", campaign)
            skipped_count += 1
            continue

        # Create or update datasource
        try:
            _, was_created = ClientDataSource.objects.update_or_create(
                client_id=client_id,
                campaign_id=campaign_id,
                defaults={
                    'campaign_name': campaign_name,
                    'campaign_type': 'leacall_campaign',
                    'is_active': status != 'stopped',
                    'api_endpoint': '/api/bi/campaigns/{}/leads/'.format(campaign_id),
                    'record_id_field': 'id',
                    'field_mapping': {},
                }
            )
            if was_created:
                created_count += 1
                logger.info("Created datasource: client=%s campaign=%s", client_id, campaign_id)
            else:
                updated_count += 1
                logger.info("Updated datasource: client=%s campaign=%s", client_id, campaign_id)
        except Exception as e:
            logger.error("discover_client_campaigns: failed to create/update datasource for %s: %s", campaign_id, e)
            skipped_count += 1

    result = {
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "message": f"Discovered {created_count + updated_count} campaigns"
    }
    logger.info("discover_client_campaigns: client=%s result=%s", client_id, result)
    return result

