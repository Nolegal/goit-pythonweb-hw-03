from datetime import datetime
import json
import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
STORAGE_DIR = BASE_DIR / 'storage'
STORAGE_DIR.mkdir(exist_ok=True)
DATA_FILE = STORAGE_DIR / 'data.json'

jinja = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case '/read':
                self.render_template('read.jinja')
            case _:
                file = (BASE_DIR / route.path.lstrip('/')).resolve()
                if BASE_DIR in file.parents and file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('error.html', 404)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(size).decode('utf-8')
        parsed_data = dict(urllib.parse.parse_qsl(body))

        message_data = {
            datetime.now().isoformat(): {
                "username": parsed_data.get("username", ""),
                "message": parsed_data.get("message", ""),
            }
        }

        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        data.update(message_data)

        with open(DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def render_template(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}

        template = jinja.get_template(filename)
        content = template.render(messages=data)
        self.wfile.write(content.encode())

    def send_html_file(self, filename, status=200):
        file_path = TEMPLATES_DIR / filename
        if not file_path.exists():
            self.send_error(404, "File not found")
            return

        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status=200):
        self.send_response(status)

        mime_type, _ = mimetypes.guess_type(filename)
        self.send_header('Content-type', mime_type or 'text/plain')
        self.end_headers()

        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def run():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, HTTPRequestHandler)
    print("Starting server...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Server is shutting down...')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run()