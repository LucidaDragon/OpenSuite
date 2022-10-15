import http.server
from config import HTTP_ADDR, HTTP_PORT
from server import init_modules, ServiceRequestHandler

init_modules()
http.server.HTTPServer((HTTP_ADDR, HTTP_PORT), ServiceRequestHandler).serve_forever()