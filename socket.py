from things import TransportLayer


class Socket(TransportLayer):
    def open(self, ip, port):
        pass

    def close(self):
        pass

    def on_open(self):
        pass

    def on_close(self):
        pass

    def on_message(self, data):
        pass


class WebSocket(Socket):
    def open(self, host, port):
        pass

    def close(self, host, port):
        pass

    def handle_send(self, data):
        pass

    def handle_recieve(self, data):
        pass


class TCPSocket(Socket):
    def open(self, host, port):
        pass

    def close(self, host, port):
        pass

    def handle_send(self, data):
        pass

    def handle_recieve(self, data):
        pass


class UDPSocket(Socket):
    def open(self, host, port):
        pass

    def close(self, host, port):
        pass

    def handle_send(self, data):
        pass

    def handle_recieve(self, data):
        pass
