#!/usr/bin/python
# coding: utf-8
import os
import sys
import logging
import logging.handlers
import daemon

from local_settings import *
from ceejay import TrelloBot

if __name__ == "__main__":

    if len(sys.argv) < 2 or sys.argv[1] not in [
            "start", "stop", "restart", "status"]:

        print "Usage: %s start|stop|restart|status" % sys.argv[0]
        sys.exit()

    with daemon.DaemonContext() as daecon:
        if sys.argv[1] == "start":
            LOGGING_DATE_FORMAT = '%Y%m%d'
            logging.basicConfig(
                    level = logging.DEBUG,
                    datefmt=LOGGING_DATE_FORMAT
                    )
            root_logger = logging.getLogger('')
            logger = logging.handlers.TimedRotatingFileHandler(LOG_DEST,
                    "midnight", 1)
            root_logger.addHandler(logger)
            # Create an instance of the bot
            trello_bot = TrelloBot()
            trello_bot.conectarse()
            trello_bot.identificacion_nickserv()
            # Start running the bot
            trello_bot.start()
        elif sys.argv[1] == "stop":
            daecon.stop()
        elif sys.argv[1] == "restart":
            pass
        elif sys.argv[1] == "status":
            pass

# vim: foldmethod=marker ts=4 sw=4 syn=python expandtab
