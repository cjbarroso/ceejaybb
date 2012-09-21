import re
from ircutils import bot
from trellocards import TrelloQuerier

from local_settings import *
import os
import logging
import logging.handlers

LOG_DEST=os.path.expanduser("~/irclogs/machinalis-cpi.log")

class TrelloBot(bot.SimpleBot):

    def __init__(self, *args, **kwargs):
        super(TrelloBot, self).__init__(*args, **kwargs)
        self.querier = TrelloQuerier()

    def on_welcome(self, event):
        self.join(CANAL)

    def on_channel_message(self, event):
        logging.debug("<%s> %s" % (event.source, event.message))
        m = re.findall("\s(:\d+)", event.message)
        for e in m:
            jeje = self.querier.buscar_carta(e)
            self.send_message(event.target, str(jeje))


if __name__ == "__main__":
    LOGGING_DATE_FORMAT     = '%Y-%m-%d'
    logging.basicConfig(
            level = logging.DEBUG,
            datefmt=LOGGING_DATE_FORMAT
            )
    root_logger = logging.getLogger('')
    logger = logging.handlers.TimedRotatingFileHandler(LOG_DEST,
            "midnight", 1)
    root_logger.addHandler(logger)
    # Create an instance of the bot
    # We set the bot's nickname here
    trello_bot = TrelloBot(BOTNAME)

    # Let's connect to the host
    trello_bot.connect(IRCNET)
    trello_bot.identify("caquita00")

    # Start running the bot
    trello_bot.start()
