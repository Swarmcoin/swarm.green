"""Confirmation mail. MAIL_MODE=off (the default) sends nothing at all.

In smtp mode one plain-text message goes out per new entry, in a background
thread so the visitor does not wait for the mail server. Failures are logged
by exception class only: never the recipient, the links or the credentials.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
import threading
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

log = logging.getLogger("waitlist.mail")

SUBJECT = "Confirm your place on the SWARM waiting list"

BODY = """Hello,

This email address was put on the SWARM waiting list for public mining.

To confirm it, open this link:
{confirm_url}

To remove yourself from the list, with your email and SWARM address, open this link:
{remove_url}

If you did not ask for this, use the second link or ignore this message. An
entry that is not confirmed does not count on the leaderboard. If several
entries were made with this email address, the first one confirmed keeps it
and the others are removed.

A place on the list means early access: the node download from
31 October 2026, 15:42 UTC, in leaderboard order during that day, 24 hours
before everyone else. It is not a promise of coins, earnings or a price.

SWARM
https://swarm.green
"""


def compose(cfg, to_addr, confirm_token, key):
    base = cfg.public_base_url
    msg = EmailMessage()
    msg["Subject"] = SUBJECT
    msg["From"] = cfg.mail_from
    msg["To"] = to_addr
    msg["Date"] = formatdate(usegmt=True)
    msg["Message-ID"] = make_msgid(domain=base.split("//", 1)[-1])
    # The token and the key travel after "#": the browser never sends that part
    # to a server, so neither ends up in an access log or in analytics.
    msg.set_content(BODY.format(confirm_url=f"{base}/waitlist#confirm={confirm_token}",
                                remove_url=f"{base}/waitlist#remove={key}"))
    return msg


def send_smtp(cfg, msg):
    if cfg.smtp_ssl:
        client = smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=20,
                                  context=ssl.create_default_context())
    else:
        client = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20)
    try:
        if not cfg.smtp_ssl and cfg.smtp_starttls:
            client.starttls(context=ssl.create_default_context())
        if cfg.smtp_user:
            client.login(cfg.smtp_user, cfg.smtp_password)
        client.send_message(msg)
    finally:
        try:
            client.quit()
        except Exception:
            pass


class Mailer:
    def __init__(self, cfg, sender=send_smtp):
        self.cfg = cfg
        self.sender = sender

    def confirmation(self, to_addr, confirm_token, key, wait=False):
        if not self.cfg.mail_on:
            return None
        msg = compose(self.cfg, to_addr, confirm_token, key)

        def run():
            try:
                self.sender(self.cfg, msg)
                log.info("confirmation mail sent")
            except Exception as exc:  # never log the message, recipient or credentials
                log.warning("confirmation mail failed: %s", type(exc).__name__)

        t = threading.Thread(target=run, name="mail", daemon=True)
        t.start()
        if wait:
            t.join()
        return t
