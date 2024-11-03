import os
import subprocess

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


class TestHTTPRequestHandler(SimpleHTTPRequestHandler):
    pass


def main(server_address=("127.0.0.1", 5678)):
    httpd = ThreadingHTTPServer(server_address, TestHTTPRequestHandler)
    host, port = httpd.server_address
    server_url = f"http://{host}:{port}/"
    print(f"Serving HTTP on: {server_url}")
    try:
        subprocess.check_call(("xdg-open", server_url))
    except Exception as e:
        print(f"Failed to open browser: {e}")
    os.chdir(os.path.join(os.path.dirname(__file__), "vane_webui"))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
