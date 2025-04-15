import base64
import logging
from email.message import EmailMessage

from google.auth.external_account_authorized_user import Credentials as ExternalCredentials
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def build_gmail_service(creds: Credentials | ExternalCredentials):
    """Build the service to Google Mail for e-mail sending.

    :param creds: the credentials to access Google API
    """

    return build(
        "gmail",
        "v1",
        credentials=creds,
    )


def send_email(
    gmail_service,
    subject: str,
    body: str,
    to_addresses: str | None = None,
    cc_addresses: str | None = None,
    bcc_addresses: str | None = None,
):
    """Send an email via GMail.

    Recipients are either in "To", "CC" or "BCC".

    :param subject: the subject of the e-mail
    :param body: the message in the e-mail
    :param to_addresses: a comma-separated list of the recipients' email
        addresses who will receive the e-mail as "to"
    :param cc_addresses: a comma-separated list of the recipients' email
        addresses who will receive the e-mail as "cc"
    :param bcc_addresses: a comma-separated list of the recipients' email
        addresses who will receive the e-mail as "bcc"
    """
    message = EmailMessage()
    message["Subject"] = subject

    if to_addresses:
        message["To"] = to_addresses
    if cc_addresses:
        message["Cc"] = cc_addresses
    if bcc_addresses:
        message["Bcc"] = bcc_addresses

    message.add_header("Content-Type", "text/html")
    message.set_payload(body)

    email = (
        gmail_service.users()
        .messages()
        .send(
            userId="me",
            body={
                "raw": base64.urlsafe_b64encode(message.as_string().encode()).decode(),
            },
        )
        .execute()
    )
    logging.info("Sent email with id: %s", (email.get("id", "N/A")))
