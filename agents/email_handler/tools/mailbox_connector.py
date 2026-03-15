"""agents/email_handler/tools/mailbox_connector.py — mock mailbox connector."""
from __future__ import annotations
import time
from shared import utc_now, new_id


class MailboxConnector:
    """Abstract mailbox connector (IMAP / Graph API / Gmail API).
    Consumer replaces with concrete implementation via agent_config['mailbox'].
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.protocol = config.get("protocol", "mock")  # imap | graph_api | gmail_api

    def fetch_unread(self, max_count: int = 10) -> list[dict]:
        """Fetch unread emails. Returns mock data in offline mode."""
        if self.protocol == "mock":
            return [
                {
                    "id": new_id("email"),
                    "subject": "Invoice #INV-2024-0091 from Vendor Corp",
                    "sender": "ap@vendorcorp.com",
                    "received_at": utc_now(),
                    "body": (
                        "Please find attached invoice INV-2024-0091 for services rendered "
                        "in November 2024. Amount due: £4,200.00. Due date: 30 days from receipt."
                    ),
                    "attachments": [{"name": "INV-2024-0091.pdf", "type": "application/pdf"}],
                    "headers": {"from": "ap@vendorcorp.com", "to": "invoices@company.com"},
                }
            ]
        raise NotImplementedError(f"Protocol {self.protocol} not yet implemented.")

    def send_reply(self, original_id: str, reply_body: str, subject: str = None) -> dict:
        """Send a reply. Returns mock delivery receipt."""
        return {
            "message_id": new_id("msg"),
            "original_id": original_id,
            "status": "DELIVERED",
            "sent_at": utc_now(),
        }
