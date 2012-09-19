#!/usr/bin/python
import httplib2
import json
import sys

from local_settings import *

base_url = "https://api.trello.com/1/"
base_get = "?key=%s&token=%s" % (TKEY, TOKEN)

urlgetter = httplib2.Http()

class TrelloQuerier:
  def __init__(self):
    pass

  def buscar_trello(self, consulta):
    query_busqueda = "&query=%s&modeltypes=cards" % consulta
    url_armada = "%s%s/%s%s" % (
        base_url,
        "search",
        base_get,
        query_busqueda
        )

    resp, conte = urlgetter.request(url_armada)
    dict_rect = json.loads(conte)
    return dict_rect

  def buscar_carta(self, carta):
    """
      Busca una carta por ID con formato

        :<#ID>

    """

    result = self.buscar_trello(carta)
    try:
      return "%s <https://trello.com/card/%s/%d>" % (
          result['cards'][0]['name'],
          result['cards'][0]['idBoard'],
          result['cards'][0]['idShort']
          )
    except IndexError:
      return "Tarjeta no encontrada"
    except Exception, e:
      print str(e)
      return "ERROR"


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print "Falta parametro"
    sys.exit(-1)
  a = TrelloQuerier()
  print a.buscar_carta(sys.argv[1])

# vim: syn=python ts=4 tw=4
