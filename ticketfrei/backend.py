#!/usr/bin/env python3
from bot import Bot
import active_bots
from config import config
from db import db
import logging
from sendmail import sendmail


def shutdown():
    try:
        sendmail(config['web']['contact'], 'Ticketfrei Shutdown')
    except Exception:
        logger.error('Could not inform admin.', exc_info=True)
    exit(1)


if __name__ == '__main__':
    logger = logging.getLogger()
    fh = logging.FileHandler(config["log"]["log_backend"])
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)


    bots = []
    for ActiveBot in active_bots.__dict__.values():
        if isinstance(ActiveBot, type) and issubclass(ActiveBot, Bot):
            bots.append(ActiveBot())

    try:
        while True:
            for user in db.active_users:
                for bot in bots:
                    reports = bot.crawl(user)
                    for status in reports:
                        if not user.is_appropriate(status):
                            logger.info("Inaproppriate message: %d %s %s" % (user.uid, status.author, status.text))
                            continue
                        for bot2 in bots:
                            bot2.post(user, status)
                            logger.info("Resent: %d %s %s" % (user.uid, status.author, status.text))
    except Exception:
        logger.error("Shutdown.", exc_info=True)
        shutdown()
