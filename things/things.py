"""
TODO synchronous behavior for non-actor calls.
TODO This actor not this/that object
"""

from greenlet import greenlet
from functools import wraps
from queue import Queue
from threading import Thread
from uuid import uuid1
from functools import partial


###############################################################################
# Configuration
###############################################################################


GREENLET_ACTOR_ATTR = 'actor'
DAEMON_THREADS = True


if DAEMON_THREADS:
    Thread = partial(Thread, daemon=True)


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


###############################################################################
# Message data structures and methods
###############################################################################


#
# Address messages.
#


# Data that will be transported to an actor
MESSAGE_DATA = 0

# Where to send return data if requested to do so.
MESSAGE_RETURN_ACTOR = 1

# The context of the calling microthread within the calling actor.
MESSAGE_CURRENT_CONTEXT = 2

# A microthread that needs to be resumed when recieved from the queue.
MESSAGE_RESUME_CONTEXT = 3


def create_message(data, return_actor=None, current_context=None,
                   resume_context=None):
    '''
    Generates a message that can be passed to an actor.
    '''

    return (data, return_actor, current_context, resume_context)


#
# Microthread messages.
#


# Is the greenlet waiting for a result?
RESULT_WAITING = 0

# Data that's being returned
RESULT_DATA = 1


def create_result(waiting, data):
    '''
    This represents the data structure passed between greenlets.
    '''

    return (waiting, data)


###############################################################################
# Actor classes
###############################################################################


class Actor(object):
    '''
    A variation of the actor model in Python.
    See: http://en.wikipedia.org/wiki/Actor_model

    TODO Should public methods represent the actor and private methods
         represent an external actor?

    Abstract methods
    ----------------
        on_message

    Public methods
    --------------
        subscribe
        broadcast
        put

    Internal methods
    ----------------
        send
        call
    '''

    def __init__(self, target=None, subscribed_to=[], spawn_as=Thread):
        if callable(target):
            self.on_message = lambda s, *a, **k: target(*a, **k)

        # Add subscribers if listed
        for actor in subscribed_to:
            self.listen(actor)

        # A list of actors subscribed to this actor.
        self.subscribers = []
        self.__main = spawn_as(target=self._event_loop)
        self.__main.start()

    def __lshift__(self, data):
        self.put(data)

    def _event_loop(self):
        '''
        Starts the event loop method as a greenlet.
        '''

        self.__event_loop_context = greenlet(self.__start_event_loop)
        self.__event_loop_context.switch()

    def __start_event_loop(self):
        '''
        Microthreaded event loop. The loop waits for a message to get put in
        the queue. Upon recieving a message, it checks to see if it's a return
        value from a call statement in an existing microthread or a new
        message. After retrieving the return value from that microthread, the
        initial message is checked for the presence of a return actor. If a
        return actor and corresponding microthread exist, then push it onto
        the queue of the calling actor. The loop is then resumed.

        TODO clean this up a bit, separate the methods out maybe?
        '''

        while 1:
            # Wait for an item on the queue.
            message = self._queue.get()
            switch_data = message[MESSAGE_DATA]
            resume_context = message[MESSAGE_RESUME_CONTEXT]
            return_actor = message[MESSAGE_RETURN_ACTOR]
            current_context = message[MESSAGE_CURRENT_CONTEXT]

            # Set the context to an existing microthread if one was passed in,
            # otherwise create a new one.
            if resume_context:
                context = resume_context
                switch_data = message[MESSAGE_DATA]
            else:
                context = self._create_microthread(self.handle_message)
                switch_data = message

            # Enter the context's frame and retrieve a result.
            result = context.switch(switch_data)

            # Determine if the microthread is waiting for a result
            waiting = result[RESULT_WAITING]
            # Get the output of the microthread.
            data = result[RESULT_DATA]

            # Send a message to the return actor if the message was recieved
            # from another actor.
            if return_actor and current_context and not waiting:
                message = create_message(data, resume_context=current_context)
                return_actor._put(message)

    def _create_microthread(self, target):
        microthread = greenlet(target)
        # Add the current actor as an attribute to the greenlet
        setattr(microthread, GREENLET_ACTOR_ATTR, self)

        return microthread

    def call(self, data):
        '''
        Puts a message this actor's mailbox with a corresponding return
        actor and reference to the current microthread. The microthread is
        then switched off and execution returns to the event loop until a
        result comes back. Upon recieving the result, the microthread is
        switched back on and the value is returned to whatever called this
        method.

        TODO what about external calls from non-actors, probably should
             generate a queue and block with a timeout until we recieve a
             response
        TODO should call reflect this actor instead of an external actor?
        TODO use current greenlet instead of data being passed in, handle
             non-actor calls.
        '''

        context = greenlet.getcurrent()
        actor = getattr(context, GREENLET_ACTOR_ATTR, None)

        # Check if the current frame has an actor associated with it.
        if actor:
            # Behaviour for cross-actor calling
            message = create_message(data, return_actor=actor,
                                     current_context=context)
            self._put(message)
            context_result = create_result(True, None)
            result = actor.__event_loop_context.switch(context_result)

            return result
        else:
            # TODO Non-actor calling (bad)
            pass

    def on_message(self, data):
        '''
        Override this method to implement functionality for recieving a
        message. Arguments are arbitrary.
        '''

        pass

    def subscribe(self, actor):
        '''
        Subscribe to this actor.
        '''

        if actor not in self.subscribers:
            self.subscribers.append(actor)

    def listen(self, actor):
        '''
        Listen to another actor.
        '''

        if self not in actor.subscribers:
            actor.subscribers.append(self)

    def broadcast(self, data):
        '''
        Send a message to all actor subscribed to this actor.
        '''

        for subscriber in self.subscribers:
            subscriber._put(create_message(data))

    def handle_message(self, message):
        '''
        Handles recieving a raw message and returning a response, this is
        called before on_message.

        TODO Handle errors
        '''
        result = self.on_message(message[MESSAGE_DATA])
        return create_result(False, result)

    def put(self, message):
        '''
        Put a message in this actor's mailbox.
        '''

        self._put(create_message(message))

    def _put(self, message):
        '''
        Put a message in this actor's mailbox, do not generate a generic
        message data structure.
        '''

        # TODO handle errors for this
        # TODO should this create a message or recieve raw data? Both perhaps?
        self._queue.put(message)

    @lazy_property
    def _queue(self):
        '''
        Object for handling queues.
        '''

        return Queue()


###############################################################################
# Bus classes
###############################################################################


BUS_SUBSCRIBER = 0
BUS_MESSAGE = 1


def create_bus_message(handler, message):
    return (handler, message)


def subscriber(fn):
    @lazy_property
    def func(self):
        return Subscriber(self, fn)

    return func


class Subscriber(object):
    def __init__(self, parent, method):
        # The bus actor associated with this method.
        self.parent = parent
        self.method = method

    def put(self, data):
        self.parent.put(create_bus_message(self.method, data))

    def call(self, data):
        result = self.parent.call(create_bus_message(self.method, data))

        return result

    def __lshift__(self, other):
        '''
        Sugar syntax for putting a message.
        '''

        self.put(other)


class Bus(Actor):
    '''
    An actor which emulates bus behavior with its method names. Any method
    subclassed with Bus will handle recieving a message addressed to that name.

    To add a subscriber, add the @subscriber decorator to a method in this
    object.

    Put symantics
    -------------

    Bus.publish (<name of handler>, <data>)
    Bus.<handler>.put(data)
    Bus.<handler> << data

    Call symantics
    --------------

    Bus.<handler>.call(data)

    Public methods
    --------------

    on_invalid_call
    '''

    def handle_message(self, message):
        bus_data = message[MESSAGE_DATA]
        subscriber = bus_data[BUS_SUBSCRIBER]

        result = subscriber(self, bus_data[BUS_MESSAGE])

        return create_result(False, result)
