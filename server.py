import base64
import datetime
import http.server
import importlib.util
import io
import os
import pathlib
import re
import shutil
from types import ModuleType
from typing import Callable
import urllib.parse

MIME_TYPES = {
	"": "api",
	".html": "text/html",
	".css": "text/css",
	".js": "application/javascript",
	".svg": "image/svg+xml"
}

AUTHORIZATION_COOKIE_REGEX = re.compile(r"Authorization=([\d\w\+\/=]+)")

def get_mime_type(extension: str) -> str:
	return MIME_TYPES[extension] if extension in MIME_TYPES else "application/octet-stream"

class Events:
	def __init__(self) -> None:
		self.events: dict[str, list[Callable]] = {}

	def raise_event(self, event: str, **kwargs) -> None:
		if event in self.events: self.events[event](**kwargs)

	def add_handler(self, event: str, handler: Callable) -> None:
		if not event in self.events: self.events[event] = []
		self.events[event].append(handler)

	def remove_handler(self, event: str, handler: Callable) -> None:
		if event in self.events: self.events[event].remove(handler)

class NullResponseStream:
	def write(buffer: bytes) -> None: pass

class ServiceRequestHandler(http.server.BaseHTTPRequestHandler):
	def __init__(self, request, client_address, server) -> None:
		super().__init__(request, client_address, server)
		self.method: str = None
		self.authenticated = False
		self.user: str | None = None

	def execute_module(self, path: pathlib.Path) -> str:
		start = datetime.datetime.now()
		module = MODULE_INTERFACES[path.parent.name]
		html = module.get_html(self)
		end = datetime.datetime.now()
		print("Executed", path.parent.name, "module in", (end - start).total_seconds() * 1000, "ms")
		return html

	def error_not_found(self) -> None:
		self.send_response_only(404, "Not Found")
		self.end_headers()

	def error_unauthorized(self) -> None:
		self.send_response_only(401, "Unauthorized")
		self.end_headers()

	def error_bad_request(self) -> None:
		self.send_response_only(400, "Bad Request")
		self.end_headers()

	def get_dashboard_modules(self) -> dict[str, Callable[["ServiceRequestHandler"], str]]:
		return DASHBOARD_MODULES

	def get_events(self) -> Events:
		return EVENTS

	def get_uri(self) -> urllib.parse.ParseResult:
		return urllib.parse.urlparse("http://localhost" + self.path)

	def get_params(self) -> dict[str, list[str]]:
		result = urllib.parse.parse_qs(self.get_uri().query)
		result["request"] = self
		return result

	def get_path(self) -> pathlib.Path:
		path = "./modules" + self.get_uri().path.replace("..", "")
		return pathlib.Path(path).absolute()

	def get_mime_type(self) -> str:
		return get_mime_type(self.get_path().suffix)

	def get_token(self) -> str | None:
		if "Authorization" in self.headers: return self.headers["Authorization"]
		elif "Cookie" in self.headers:
			match = AUTHORIZATION_COOKIE_REGEX.match(self.headers["Cookie"])
			if match != None: return base64.b64decode(match[1], validate=True).decode("UTF-16")
		return None

	def has_token(self) -> bool:
		return self.get_token() != None

	def api_handler(self) -> None:
		endpoint = self.get_uri().path
		if endpoint in API_HANDLERS: API_HANDLERS[endpoint](self)
		else: self.error_not_found()

	def html_file_handler(self) -> None:
		try:
			path = self.get_path().with_suffix(".py")
			html = self.execute_module(path).encode("UTF-8")
			self.send_response_only(200, "OK")
			self.send_header("Content-Type", "text/html")
			self.send_header("Content-Length", len(html))
			self.end_headers()
			self.wfile.write(html)
		except TypeError:
			self.error_bad_request()
		except:
			self.error_not_found()

	def default_file_handler(self) -> None:
		try:
			path = self.get_path()
			with path.open("rb") as stream:
				stream.seek(0, io.SEEK_END)
				length = stream.tell()
				stream.seek(0, io.SEEK_SET)

				self.send_response_only(200, "OK")
				self.send_header("Content-Type", MIME_TYPES[path.suffix])
				self.send_header("Content-Length", length)
				self.end_headers()
				shutil.copyfileobj(stream, self.wfile, length)
		except:
			self.error_not_found()

	def process_authentication(self) -> bool:
		for handler in AUTHORIZATION_MODULES:
			if not handler(self): return False
		if settings_module != None: settings_module.set_default_settings(self, DEFAULT_SETTINGS)
		return True

	def do_GET(self):
		self.log_request()
		self.method = "GET"
		if not self.process_authentication(): return
		mime = self.get_mime_type()
		handler = MIME_HANDLERS[mime] if mime in MIME_HANDLERS else ServiceRequestHandler.error_not_found
		handler(self)

	def do_HEAD(self):
		self.wfile = NullResponseStream()
		self.do_GET()

	def do_POST(self):
		self.log_request()
		self.method = "POST"
		if not self.process_authentication(): return
		self.api_handler()

	def do_OPTIONS(self):
		self.log_request()
		self.send_response_only(204, "No Content")
		self.send_header("Allow", "OPTIONS, GET, HEAD, POST")

class ServerExtensionInterface:
	def __init__(self, mime_handlers: dict[str, Callable[[ServiceRequestHandler], None]], mime_types: dict[str, str], api_handlers: dict[str, Callable[[ServiceRequestHandler], None]], authorization_modules: list[Callable[[ServiceRequestHandler], bool]], events: Events) -> None:
		self.mime_handlers = mime_handlers
		self.mime_types = mime_types
		self.api_handlers = api_handlers
		self.authorization_modules = authorization_modules
		self.events = events

class ModuleInterface:
	def init(self, server: ServerExtensionInterface) -> None: ...
	def is_dashboard_module(self) -> bool: return False
	def get_icon_html(self, request: ServiceRequestHandler) -> str: ...
	def get_html(self, request: ServiceRequestHandler) -> str: ...
	def get_default_settings(self) -> dict[str, str]: return {}

class SettingsModuleInterface(ModuleInterface):
	def set_default_settings(self, request: ServiceRequestHandler, settings: dict[str, dict[str, str]]) -> None: ...

MODULE_INTERFACES: dict[str, ModuleInterface] = {}

MIME_HANDLERS: dict[str, Callable[[ServiceRequestHandler], None]] = {
	"api": ServiceRequestHandler.api_handler,
	"text/html": ServiceRequestHandler.html_file_handler,
	"text/css": ServiceRequestHandler.default_file_handler,
	"image/svg+xml": ServiceRequestHandler.default_file_handler,
	"application/javascript": ServiceRequestHandler.default_file_handler
}

API_HANDLERS: dict[str, Callable[[ServiceRequestHandler], None]] = {}

AUTHORIZATION_MODULES: list[Callable[[ServiceRequestHandler], bool]] = []

DASHBOARD_MODULES: dict[str, Callable[[ServiceRequestHandler], str]] = {}

EVENTS = Events()

DEFAULT_SETTINGS: dict[str, dict[str, str]] = {}
settings_module: SettingsModuleInterface | None = None

PYTHON_CACHE: dict[str, ModuleType] = {}

def load_module(path: str, name: str) -> ModuleType:
	if path in PYTHON_CACHE: return PYTHON_CACHE[path]
	module_spec = importlib.util.spec_from_file_location(name, path)
	module = importlib.util.module_from_spec(module_spec)
	module_spec.loader.exec_module(module)
	PYTHON_CACHE[path] = module
	return module

def init_modules():
	if len(PYTHON_CACHE) > 0: return
	extensions = ServerExtensionInterface(MIME_HANDLERS, MIME_TYPES, API_HANDLERS, AUTHORIZATION_MODULES, EVENTS)
	def add_directory(directory):
		global settings_module
		path = pathlib.Path("./modules/" + directory).joinpath("./index.py").absolute()
		try:
			module = load_module(str(path), path.parent.name)
			for obj in vars(module).values():
				if isinstance(obj, type) and issubclass(obj, ModuleInterface) and obj != ModuleInterface and obj != SettingsModuleInterface:
					module_interface = obj()
					module_interface.init(extensions)
					if module_interface.is_dashboard_module(): DASHBOARD_MODULES[path.parent.name] = module_interface.get_icon_html
					default_settings = module_interface.get_default_settings()
					if len(default_settings) > 0: DEFAULT_SETTINGS[path.parent.name] = default_settings
					if isinstance(module_interface, SettingsModuleInterface): settings_module = module_interface
					MODULE_INTERFACES[path.parent.name] = module_interface
					break
		except Exception as ex:
			print(f"Error loading {directory} module:", ex)
	add_directory("../modules")
	for _, directories, _ in os.walk("./modules"):
		for directory in directories:
			if directory.startswith(".") or directory.startswith("_"): continue
			add_directory(directory)
		break