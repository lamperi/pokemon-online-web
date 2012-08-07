# Twisted configuration file
# Run with
# twistd -y powebservice.tac

import os
from twisted.application import service, internet
from twisted.web import static, server

from txsockjs.factory import SockJSFactory
from server import POFactory

def getWebService():
    web_service = service.MultiService()

    root = static.File('static')
    factory = server.Site(root)
    internet.TCPServer(8080, factory).setServiceParent(web_service)

    factory = POFactory()
    factory = SockJSFactory(factory)
    internet.TCPServer(8081, factory).setServiceParent(web_service)

    return web_service

application = service.Application("Pokemon Online Web Gateway")

service = getWebService()
service.setServiceParent(application)
