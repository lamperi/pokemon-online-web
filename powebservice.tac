# Twisted configuration file
# Run with
# twistd -y powebservice.tac

import os
from twisted.application import service, internet
from twisted.web import static, server

from websocket import WebSocketSite
from server import POhandler

def getWebService():
    root = static.File('.')
    site = WebSocketSite(root)
    site.addHandler('/test', POhandler)
    return internet.TCPServer(8080, site)

application = service.Application("Pokemon Online Web Gateway")

service = getWebService()
service.setServiceParent(application)
