class Actor(object):
    def __init__(self):
        self.return_addresses = {}
        # TODO Use bisect to turn subjects/subscribers into binary search trees
        self.subjects = []
        self.subscribers = []

    def on_message(self, data):
        pass

    def broadcast(self, data):
        for subscriber in self.subscribers:
            subscriber.call(data)

    def call(self, address, data, timeout=None):
        address.call(data)

    def handle_message(self, data):
        self.on_message(data)


class Bus(Actor):
    def on_message(self, data):
        pass

    def on_invalid_call(self, data):
        pass

    def handle_message(self, data):
        self.on_message(data)


class Address(object):
    def __init__(self, key):
        self.key = key

    def call(self):
        pass


class Message(object):
    def __init__(self, data):
        self.data = data


class TransportLayer(Actor):
    def __init__(self):
        pass

    def handle_send(self, data):
        pass

    def handle_recieve(self, data):
        pass

    def serialize(self, data):
        pass

    def deserialize(self, data):
        pass
