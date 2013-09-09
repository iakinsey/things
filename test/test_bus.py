import things
import unittest
from queue import Queue


class TestBus(unittest.TestCase):
    def test_put(self):
        '''
        Send 1000 messages to a bus subscriber.
        '''

        queue = Queue()

        class Bus(things.Bus):
            @things.subscriber
            def subscriber(self, data):
                queue.put(data)

        bus = Bus()

        for n in range(1000):
            bus.subscriber.put(n)
            result = queue.get(timeout=5)

            assert result == n

    def test_call(self):
        '''
        Pretty much a copy of self.test_send, except we use Actor.call.
        '''

        queue = Queue()

        class Bus(things.Bus):
            @things.subscriber
            def subscriber(self, data):
                return data

        class Actor(things.Actor):
            def on_message(self, data):
                bus = data['bus']
                message = data['message']
                result = bus.subscriber.call(message)
                queue.put(result)

        bus = Bus()
        actor = Actor()

        for n in range(1000):
            actor.put({
                'bus': bus,
                'message': n
            })

            result = queue.get(timeout=5)

            assert result == n
