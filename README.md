# Things
## An Actor framework for Python

### Introduction

Things.py is a actor framework that emphasizes readability.

### Setting up an environment
Things requires greenlet and (optionally) nose.

    pip install -r requirements.txt

### Usage

#### Actor
Setting up an actor is relatively simple. There is very little convention
beyond the on_message method, which handles messages recieved from the mailbox.

    from things import Actor

    class Thingy(Actor):
        def on_message(self, data):
            return data

Instantiating the actor is like any other object.

    actor = Thingy()

To put a message in the actor's mailbox, call the .put() method.

    actor.put(10)

Alternatively, you can use the bitwise shift operator.

    actor << 10

If you would like to recieve a return value from an actor, use the .call()
method. This reads like synchronous code while being asynchronous under the
hood. Using .call() will not block other operations while waiting for a result.
This method does not currenty work when called outside of an actor.

    stuff = actor.call(10)
    print(stuff)

Actors can also subscribe to other actors. When this happens, anything sent
through the broadcast() method is put into the subject's mailbox.

    class AnotherThingy(Actor):
        pass

    another_actor = AnotherThingy()
    another_actor.subscribe(actor)
    another_actor.broadcast(10)
    >> 10

#### Bus
A bus is an actor with subscribers. Use the @subscriber decorator to indicate
that a method is a subscriber.

    from things import Bus
    from things import subscriber

    class Thingy(Bus):
        @subscriber
        def any_name_goes_here(self, data):
            return data

        @subscriber
        def another_handler(self, data):
            return 10

    bus = Thingy()

Convention for calling a subscriber or putting a message in the subscriber's
mailbox is the same.

    bus.another_handler << 10
    bus.another_handler.put(10)

    bus.another_handler.call(10)
