import things
import unittest
from queue import Queue


class TestPutOperator(unittest.TestCase):
    def test_put(self):
        '''
        Send a message to an actor using the put sugar syntax.
        '''

        # use a queue
        queue = Queue()
        message = "hello world"

        class Actor(things.Actor):
            def on_message(self, data):
                queue.put(data)

        actor = Actor()
        actor << message
        result = queue.get(timeout=5)

        assert result == message

    def test_bus_put(self):
        '''
        Send a message to a bus using the put sugar syntax.
        '''

        queue = Queue()
        message = "hello world"

        class Bus(things.Bus):
            @things.subscriber
            def subscriber(self, data):
                queue.put(data)

        bus = Bus()
        bus.subscriber << message
        result = queue.get(timeout=5)

        assert result == message
