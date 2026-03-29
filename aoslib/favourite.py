from twisted.internet.defer import Deferred
from twisted.internet import reactor
import json


def favourite_check(adr):

    defer = Deferred()

    def favourite_check_func(adr):
        file = json.loads(open('server_favorites.json').read())
        if adr in file:
            return True
        else:
            return False
    
    reactor.callLater(0, defer.callback, adr)
    defer.addCallback(favourite_check_func)
    return defer

def favourite_add(adr):
    defer = Deferred()

    def favourite_add_func(adr):
        with open('server_favorites.json', 'r') as f:
            file = json.load(f)
        file.append(adr)
        with open('server_favorites.json', 'w') as f:
            json.dump(file, f)

    reactor.callLater(0, defer.callback, adr)
    defer.addCallback(favourite_add_func)
    return defer

def favourite_del(adr):
    defer = Deferred()

    def favourite_del_func(adr):
        with open('server_favorites.json', 'r') as f:
            file = json.load(f)
        file.pop(file.index(adr))
        with open('server_favorites.json', 'w') as f:
            json.dump(file, f)

    reactor.callLater(0, defer.callback, adr)
    defer.addCallback(favourite_del_func)
    return defer