from bot import Bot
import logging
from report import Report
from twx.botapi import TelegramBot as Telegram


logger = logging.getLogger(__name__)


class TelegramBot(Bot):
    def crawl(self, user):
        tb = Telegram(user.get_telegram_credentials())
        seen_tg = user.get_seen_tg()
        try:
            updates = tb.get_updates(offset=seen_tg + 1,
                                     allowed_updates="message").wait()
        except TypeError:
            updates = tb.get_updates().wait()
        reports = []
        if updates == None:
            return reports
        for update in updates:
            # return when telegram returns an error code
            if update in [303, 404, 420, 500, 502]:
                return reports
            if isinstance(update, int):
                logger.error("Unknown Telegram error code: " + str(update))
                return reports
            user.save_seen_tg(update.update_id)
            if update.message.text.lower() == "/start":
                user.add_telegram_subscribers(update.message.sender.id)
                tb.send_message(
                    update.message.sender.id,
                    "You are now subscribed to report notifications.")
                # TODO: /start message should be set in frontend
            elif update.message.text.lower() == "/stop":
                user.remove_telegram_subscribers(update.message.sender.id)
                tb.send_message(
                    update.message.sender.id,
                    "You are now unsubscribed from report notifications.")
                # TODO: /stop message should be set in frontend
            elif update.message.text.lower() == "/help":
                tb.send_message(
                    update.message.sender.id,
                    "Send reports here to share them with other users. Use /start and /stop to get reports or not.")
                # TODO: /help message should be set in frontend
            else:
                # set report.author to "" to avoid mailbot crash
                if update.message.sender.username is None:
                    update.message.sender.username = ""

                reports.append(Report(update.message.sender.username, self,
                                      update.message.text, None,
                                      update.message.date))
        return reports

    def post(self, user, report):
        tb = Telegram(user.get_telegram_credentials())
        text = report.text
        if len(text) > 4096:
            text = text[:4096 - 4] + u' ...'
        try:
            for subscriber_id in user.get_telegram_subscribers():
                tb.send_message(subscriber_id, text).wait()
        except Exception:
            logger.error('Error telegramming: ' + user.get_city() + ': '
                         + str(report.id), exc_info=True)
