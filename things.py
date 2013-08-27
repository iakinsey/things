from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from queue import Queue
from threading import Thread, Event
from uuid import uuid1

# TODO executor for greenlets

# TODO Shape or args/kwargs?
message = namedtuple('message', (
    'data',
    'return_address',
    'event_id'
))


def create_message(data, return_address=None, event_id=None):
    '''
    Generates a message that can be passed to an actor.
    '''

    return message(data, return_address, event_id)


def lazy_property(fn):
    '''
    A decorator for lazily-loaded evaluate-once class properties.
    '''

    name = uuid1().hex

    @property
    @wraps(fn)
    def getter(self):
        if not hasattr(self, name):
            setattr(self, name, fn(self))

        return getattr(self, name)

    return getter


class Actor(object):
    '''
    A variation of the actor model in Python.
    See: http://en.wikipedia.org/wiki/Actor_model

    Abstract methods
    ----------------
        on_message

    Public methods
    --------------
        subscribe
        broadcast
        address
        put
    '''

    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.return_addresses = {}
        # A list of addresses for actors subscribed to this actor.
        # TODO Use bisect to turn subscribers into binary search trees?
        self.subscribers = []
        # TODO make main modular so we can use greenlets and processes
        self.__main = Thread(target=self._event_loop, daemon=True)
        self.__main.start()

    def on_message(self, data):
        '''
        Override this method to implement functionality for recieving a
        message. Arguments are arbitrary.
        '''

        pass

    def subscribe(self, address):
        '''
        Have an address subscribe to this actor.
        '''

        self.subscribers.append(address)

    def broadcast(self, data):
        '''
        Send a message to all addresses subscribed to this actor.
        '''

        for subscriber in self.subscribers:
            subscriber.put(data)

    def handle_message(self, message):
        '''
        Handles recieving a message and returning a response, this is called
        before on_message.
        '''

        # TODO handle errors
        result = self.on_message(message.data)

        if message.return_address and message.event_id:
            message.return_address.handle_response(result, message)

    def _event_loop(self):
        '''
        Main event loop for this actor.
        '''

        with self._executor(max_workers=self.max_workers) as e:
            while 1:
                task = self._queue.get()
                e.submit(self.handle_message, task)

    def put(self, message):
        '''
        Put a message in this actor's mailbox.
        '''

        # TODO handle errors for this
        self._queue.put(create_message(message))

    @lazy_property
    def address(self):
        '''
        Address for this actor.
        '''

        return Address(self)

    @lazy_property
    def _queue(self):
        '''
        Object for handling queues.
        '''

        return Queue()

    @property
    def _executor(self):
        '''
        Executor object.
        TODO remove
        '''

        return ThreadPoolExecutor


class RemoteActor(Actor):
    '''
    Implements actor behavior for actors that do not exist within the current
    program (eg. socket, memory address, etc)
    '''

    def __init__(self, transport_layer, *args, **kwargs):
        self.transport_layer = transport_layer
        super().__init__(*args, **kwargs)

    def on_message(self, data):
        self.transport_layer.handle_send(data)


class Bus(Actor):
    '''
    An actor which emulates bus behavior with its method names. Any method
    subclassed with Bus will handle recieving a message addressed to that name.

    Public methods
    --------------
        on_invalid_call
    '''

    def on_message(self, data):
        pass

    def on_invalid_call(self, data):
        pass

    def handle_message(self, data):
        self.on_message(data)


class Address(object):
    '''
    Points to an actor.

    Public methods
    --------------
        call
        handle_response
        put
        subscribe
    '''

    def __init__(self, actor, key=None):
        self.actor = actor
        self.key = key
        self.events = {}
        self.results = {}

    def call(self, data, timeout=None):
        '''
        THIS WILL BLOCK
        ---------------

        Put a message in the actor's mailbox and wait until a response is
        recieved or times out. This is used to emulate synchronous syntax.

        TODO
        ----

        Remove the fucking ugly thread blocking bullshit. What if we called
        handle_message directly? There's no real reason to use up another
        thread, we could just branch the frame into another actor. There would
        still need to be some form of blocking or callback thingy if we want to
        wait for responses from multiple actors. Does that require an entire
        method on its own?

        However, there's also switching and cooperative multitasking. This
        would make the application single-threaded, unless we did magic with
        the frame of the actor.

        '''

        # Generate unique identifier for the return signature
        event_id = uuid1().int
        event = Event()
        message = create_message(data, self, event_id)

        self.events[event_id] = event
        self.actor.put(message)
        # Block until a response is recieved, or it times out.
        event.wait(timeout)

        # TODO handle timeouts

        result = self.results.get(event_id)

        if result:
            del self.results[event_id]

        del self.events[event_id]

        return result

    def handle_response(self, result, original_message):
        '''
        Handles triggering the response event in the calling thread.

        Which is more clear, putting this method in Address or Actor?
        '''

        event_id = original_message.event_id
        event = self.events.get(event_id)

        if event:
            event.set()
        else:
            # TODO error handling
            pass

    def put(self, data):
        '''
        Puts a message in the addressed actor's mailbox.
        '''

        self.actor.put(data)

    def subscribe(self, actor):
        '''
        Subscribes an actor (subject) to the addressed actor. When the
        addressed actor's broadcast() method is called, the subject will
        recieve the data.
        '''

        self.actor.subscribe(actor.address)


class TransportLayer(Actor):
    '''
    Defines behavior for transporting data between a local and remote actor.
    TODO use async socket.

    Abstract methods
    ----------------
        handle_send
        handle_recieve
        serialize
        deserialize
    '''

    def __init__(self, *args, **kwargs):
        pass

    def handle_send(self, data):
        pass

    def handle_recieve(self, data):
        pass

    def serialize(self, data):
        pass

    def deserialize(self, data):
        pass
