#!/usr/bin/env python3

import logging
from sendmail import sendmail
import datetime
import mailbox
import email
import report
from bot import Bot
from config import config
from db import db

logger = logging.getLogger(__name__)


class Mailbot(Bot):

    # returns a list of Report objects
    def crawl(self, user):
        reports = []
        # todo: adjust to actual mailbox
        try:
            mails = mailbox.mbox("/var/mail/" + config['mail']['mbox_user'])
        except FileNotFoundError:
            logger.error("No mbox file found.")
            return reports
        for msg in mails:
            if get_date_from_header(msg['Date']) > user.get_seen_mail():
                if user.get_city().lower() in msg['To'].lower():
                    reports.append(make_report(msg, user))
        return reports

    # post/boost Report object
    def post(self, user, report):
        recipients = user.get_mailinglist()
        for rec in recipients:
            rec = rec[0]
            unsubscribe_text = "\n_______\nYou don't want to receive those messages? Unsubscribe with this link: "
            body = report.text + unsubscribe_text + config['web']['host'] + "/city/mail/unsubscribe/" \
                   + db.mail_subscription_token(rec, user.get_city())
            if rec not in report.author:
                try:
                    city = user.get_city()
                    sendmail(rec, "Ticketfrei " + city + " Report",
                                      city=city, body=body)
                except Exception:
                    logger.error("Sending Mail failed.", exc_info=True)


def make_report(msg, user):
    """
    generates a report out of a mail

    :param msg: email.parser.Message object
    :return: post: report.Report object
    """
    # get a comparable date out of the email
    date = get_date_from_header(msg['Date'])

    author = msg['From']  # get mail author from email header

    if msg.is_multipart():
        text = []
        for part in msg.get_payload():
            if part.get_content_type() == "text":
                text.append(part.get_payload())
            elif part.get_content_type() == "application/pgp-signature":
                pass  # ignore PGP signatures
            elif part.get_content_type() == "multipart/mixed":
                for p in part:
                    if isinstance(p, str):
                        text.append(p)
                    elif p.get_content_type() == "text":
                        text.append(part.get_payload())
                    else:
                        logger.error("unknown MIMEtype: " +
                                     p.get_content_type())
            else:
                logger.error("unknown MIMEtype: " +
                             part.get_content_type())
        text = '\n'.join(text)
    else:
        text = msg.get_payload()
    post = report.Report(author, "mail", text, None, date)
    user.save_seen_mail(date)
    return post


def get_date_from_header(header):
    """
    :param header: msg['Date']
    :return: float: total seconds
    """
    date_tuple = email.utils.parsedate_tz(header)
    date_tuple = datetime.datetime.fromtimestamp(
        email.utils.mktime_tz(date_tuple)
    )
    return (date_tuple - datetime.datetime(1970, 1, 1)).total_seconds()
