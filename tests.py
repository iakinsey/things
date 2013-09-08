import things
import unittest
from queue import Queue
from random import randint


class TestActorEventLoop(unittest.TestCase):
    def test_single_item_in_queue(self):
        '''
        Create an actor, start it. Send a message to it and verify that it
        recieved and handled the message successfully.
        '''
        # use a queue
        queue = Queue()
        message = "hello world"

        class Actor(things.Actor):
            def on_message(self, data):
                queue.put(data)

        actor = Actor()
        actor.put(message)
        result = queue.get(timeout=5)

        assert result == message

    def test_multiple_items_in_queue(self):
        queue = Queue()
        messages = list(range(100))

        class Actor(things.Actor):
            def on_message(self, data):
                queue.put(data)

        actor = Actor()
        for message in messages:
            actor.put(message)
            result = queue.get(timeout=5)

            assert result == message

            if result == messages[-1]:
                break


class TestActorCommunication(unittest.TestCase):
    def test_send(self):
        '''
        Send 1000 messages from one actor to another.
        '''

        queue = Queue()

        class FirstActor(things.Actor):
            def on_message(self, data):
                data['actor'].put(data['message'])

        class SecondActor(things.Actor):
            def on_message(self, data):
                queue.put(data)

        first_actor = FirstActor()
        second_actor = SecondActor()

        for n in range(1000):
            first_actor.put({
                'actor': second_actor,
                'message': n
            })

            result = queue.get(timeout=5)

            assert result == n

    def test_call(self):
        '''
        Pretty much a copy of self.test_send, except we use Actor.call.
        '''

        queue = Queue()

        class FirstActor(things.Actor):
            def on_message(self, data):
                data['actor'].call(data['message'])

        class SecondActor(things.Actor):
            def on_message(self, data):
                queue.put(data)

        first_actor = FirstActor()
        second_actor = SecondActor()

        for n in range(1000):
            first_actor.put({
                'actor': second_actor,
                'message': n
            })

            result = queue.get(timeout=5)

            assert result == n

    def test_listen(self):
        '''
        Generate 100 actors and link them together on a one-dimensional path.
        Pass 1000 messages from the starting point and check to make sure they
        reach the end point properly.
        '''

        queue = Queue()
        actors = []

        class Actor(things.Actor):
            def on_message(self, data):
                self.broadcast(data)

        class Endpoint(things.Actor):
            def on_message(self, data):
                queue.put(data)

        for n in range(randint(1, 100)):
            actor = Actor()
            actors.append(actor)

            if n == 0:
                continue
            else:
                actor.listen(actors[n - 1])

        endpoint = Endpoint()
        endpoint.listen(actors[-1])
        actors.append(endpoint)

        for data in range(1000):
            actors[0].put(data)
            result = queue.get(timeout=5)
            assert result == data

    def test_broadcast(self):
        '''
        Generate a tree structure of actors, broadcast 100 messages from the
        root of the tree and verify that the data reached the leafs.
        '''

        queue = Queue()

        class Actor(things.Actor):
            def on_message(self, data):
                self.broadcast(data)

        class Leaf(things.Actor):
            def on_message(self, data):
                queue.put(data)

        # Create actors
        root = Actor()
        level_1 = [Actor() for i in range(2)]
        level_2 = [Actor() for i in range(4)]
        level_3 = [Leaf() for i in range(8)]

        child = 0
        parent = 1
        tree_range = lambda n: enumerate(sorted(list(range(n))
                                                + list(range(n)))[:n])

        # Link them together
        # TODO Clean this up a bit
        for n in tree_range(8):
            level_3[n[child]].listen(level_2[n[parent]])

        for n in tree_range(4):
            level_2[n[child]].listen(level_1[n[parent]])

        for n in range(2):
            level_1[n].listen(root)

        for data in range(1000):
            root.put(data)

            for n in range(len(level_3)):
                result = queue.get(timeout=5)
                assert result == data


if __name__ == '__main__':
    unittest.main()
