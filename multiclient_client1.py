import argparse
import select
import socket
import sys


def run_client(name):
	parser = argparse.ArgumentParser(description=f"{name} for the multi-client chat")
	parser.add_argument("--host", default="127.0.0.1")
	parser.add_argument("--port", type=int, default=5000)
	args = parser.parse_args()

	try:
		connection = socket.create_connection((args.host, args.port))
	except OSError as error:
		print(f"Could not connect to {args.host}:{args.port}: {error}", file=sys.stderr)
		return 1

	print(f"Connected to {args.host}:{args.port}. Enter /quit to leave.")
	with connection:
		inputs = [connection, sys.stdin]
		while True:
			readable, _, _ = select.select(inputs, [], [])
			if connection in readable:
				data = connection.recv(4096)
				if not data:
					print("Server disconnected.")
					break
				sys.stdout.write(data.decode("utf-8", errors="replace"))
				sys.stdout.flush()

			if sys.stdin in readable:
				line = sys.stdin.readline()
				if not line:
					line = "/quit\n"
				message = line.rstrip("\r\n")
				if message == "/quit":
					connection.sendall(b"/quit\n")
					break
				if message:
					connection.sendall(f"{name}: {message}\n".encode("utf-8"))

	return 0


if __name__ == "__main__":
	raise SystemExit(run_client("Client 1"))
