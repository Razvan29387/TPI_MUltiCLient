import argparse
import selectors
import socket
from dataclasses import dataclass, field


MAX_MESSAGE_SIZE = 65536
MAX_PENDING_BYTES = 1048576


@dataclass
class Client:
	input_buffer: bytearray = field(default_factory=bytearray)
	output_buffer: bytearray = field(default_factory=bytearray)


def main():
	parser = argparse.ArgumentParser(description="TCP multi-client chat server")
	parser.add_argument("--host", default="127.0.0.1")
	parser.add_argument("--port", type=int, default=5000)
	args = parser.parse_args()

	selector = selectors.DefaultSelector()
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.bind((args.host, args.port))
	server.listen()
	server.setblocking(False)
	selector.register(server, selectors.EVENT_READ)
	clients = {}

	def update_events(connection):
		client = clients.get(connection)
		if client is None:
			return
		events = selectors.EVENT_READ
		if client.output_buffer:
			events |= selectors.EVENT_WRITE
		selector.modify(connection, events, data=client)

	def close_client(connection):
		clients.pop(connection, None)
		try:
			selector.unregister(connection)
		except (KeyError, ValueError):
			pass
		connection.close()

	def broadcast(message):
		encoded = message.encode("utf-8")
		slow_clients = []
		for connection, client in list(clients.items()):
			if len(client.output_buffer) + len(encoded) > MAX_PENDING_BYTES:
				slow_clients.append(connection)
				continue
			client.output_buffer.extend(encoded)
			update_events(connection)
		for connection in slow_clients:
			close_client(connection)

	def accept_connection():
		connection, address = server.accept()
		connection.setblocking(False)
		client = Client()
		clients[connection] = client
		selector.register(connection, selectors.EVENT_READ, data=client)
		client.output_buffer.extend(b"Connected to the chat. Type /quit to leave.\n")
		update_events(connection)
		print(f"Client connected: {address[0]}:{address[1]}")

	def read_from_client(connection):
		client = clients[connection]
		try:
			data = connection.recv(4096)
		except ConnectionError:
			data = b""

		if not data:
			close_client(connection)
			broadcast("A client disconnected.\n")
			return

		client.input_buffer.extend(data)
		if len(client.input_buffer) > MAX_MESSAGE_SIZE and b"\n" not in client.input_buffer:
			close_client(connection)
			broadcast("A client sent an oversized message and disconnected.\n")
			return

		while b"\n" in client.input_buffer:
			raw_message, _, remainder = client.input_buffer.partition(b"\n")
			client.input_buffer = bytearray(remainder)
			message = raw_message.decode("utf-8", errors="replace").rstrip("\r")
			if message == "/quit":
				close_client(connection)
				broadcast("A client disconnected.\n")
				return
			if message:
				broadcast(message + "\n")

	def write_to_client(connection):
		client = clients[connection]
		try:
			sent = connection.send(client.output_buffer)
		except BlockingIOError:
			return
		except ConnectionError:
			close_client(connection)
			return
		if sent:
			del client.output_buffer[:sent]
			update_events(connection)
		else:
			close_client(connection)

	print(f"Server listening on {args.host}:{args.port}")
	try:
		while True:
			for key, mask in selector.select():
				if key.fileobj is server:
					accept_connection()
					continue
				connection = key.fileobj
				if mask & selectors.EVENT_READ and connection in clients:
					read_from_client(connection)
				if mask & selectors.EVENT_WRITE and connection in clients:
					write_to_client(connection)
	except KeyboardInterrupt:
		print("\nServer shutting down.")
	finally:
		for connection in list(clients):
			close_client(connection)
		selector.unregister(server)
		server.close()
		selector.close()


if __name__ == "__main__":
	main()
