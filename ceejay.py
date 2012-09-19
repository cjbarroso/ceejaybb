import re
from ircutils import bot
from trellocards import TrelloQuerier

from local_settings import *

class TrelloBot(bot.SimpleBot):

    def __init__(self, *args, **kwargs):
        super(TrelloBot, self).__init__(*args, **kwargs)
        self.querier = TrelloQuerier()

    def on_welcome(self, event):
        self.join(CANAL)

    def on_channel_message(self, event):
        m = re.findall("\s(:\d+)", event.message)
        for e in m:
            jeje = self.querier.buscar_carta(e)
            self.send_message(event.target, str(jeje))


if __name__ == "__main__":
    # Create an instance of the bot
    # We set the bot's nickname here
    trello_bot = TrelloBot(BOTNAME)

    # Let's connect to the host
    trello_bot.connect(IRCNET)

    # Start running the bot
    trello_bot.start()
