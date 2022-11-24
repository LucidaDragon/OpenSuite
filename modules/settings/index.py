import json
import modules.settings.config
from server import ServerExtensionInterface, ServiceRequestHandler, SettingsModuleInterface

class Module(SettingsModuleInterface):
	def __init__(self) -> None:
		self.cache = None
		self.icon_cache = None

	def init(self, server: ServerExtensionInterface) -> None:
		server.api_handlers["/settings/get_all"] = self.handle_get_all_settings
		server.api_handlers["/settings/get"] = self.handle_get_setting
		server.api_handlers["/settings/set"] = self.handle_set_setting
		server.api_handlers["/settings/delete"] = self.handle_delete_setting
		server.api_handlers["/settings/clear"] = self.handle_clear_setting
		server.api_handlers["/settings/theme"] = self.handle_get_theme

	def is_dashboard_module(self) -> bool: return True

	def get_html(self, request: ServiceRequestHandler):
		if self.cache == None:
			with open("./modules/settings/index.html", "r") as stream:
				self.cache = stream.read()
		return self.cache

	def get_icon_html(self, request: ServiceRequestHandler) -> str:
		if self.icon_cache == None:
			with open("./modules/settings/icon.svg", "r") as stream:
				self.icon_cache = stream.read()
		return self.icon_cache

	def get_default_settings(self) -> dict[str, str]:
		return {
			"text-color": "\"#DDDDDD\"",
			"accent-color": "\"#1E90FF\"",
			"panel-color": "\"#333333\"",
			"panel-header-color": "\"#444444\"",
			"background-color": "\"#222222\"",
			"accept-color": "\"#22AA22\"",
			"decline-color": "\"#FF2222\""
		}

	def set_default_settings(self, request: ServiceRequestHandler, settings: dict[str, dict[str, str]]) -> None:
		if request.authenticated:
			for module in settings.keys():
				for name in settings[module].keys():
					if not modules.settings.config.provider.has_setting(request.user, module, name):
						modules.settings.config.provider.set_setting(request.user, module, name, settings[module][name])

	def handle_get_theme(self, request: ServiceRequestHandler) -> None:
		if not request.authenticated:
			request.error_unauthorized()
			return
		try:
			result = ":root { "
			for name in self.get_default_settings().keys():
				value = json.loads(modules.settings.config.provider.get_setting(request.user, "settings", name))
				if value != None: result += f"--{name}: {value}; "
			result = (result + "}").encode("UTF-8")
			request.send_response_only(200, "OK")
			request.send_header("Content-Type", "text/css")
			request.send_header("Content-Length", len(result))
			request.end_headers()
			request.wfile.write(result)
		except: request.error_not_found()

	def handle_get_all_settings(self, request: ServiceRequestHandler) -> None:
		if not request.authenticated: request.error_unauthorized()
		try:
			result = json.dumps(modules.settings.config.provider.get_all_settings(request.user)).encode("UTF-8")
			if result == None:
				request.error_not_found()
			else:
				request.send_response_only(200, "OK")
				request.send_header("Content-Length", len(result))
				request.send_header("Content-Type", "application/octet-stream")
				request.end_headers()
				request.wfile.write(result)
		except: request.error_bad_request()

	def handle_get_setting(self, request: ServiceRequestHandler) -> None:
		if not request.authenticated:
			request.error_unauthorized()
			return
		params = request.get_params()
		try:
			result = modules.settings.config.provider.get_setting(request.user, params["module"][0], params["name"][0]).encode("UTF-8")
			if result == None:
				request.error_not_found()
			else:
				request.send_response_only(200, "OK")
				request.send_header("Content-Length", len(result))
				request.send_header("Content-Type", "application/octet-stream")
				request.end_headers()
				request.wfile.write(result)
		except: request.error_bad_request()

	def handle_set_setting(self, request: ServiceRequestHandler) -> None:
		if not request.authenticated: request.error_unauthorized()
		params = request.get_params()
		try:
			modules.settings.config.provider.set_setting(request.user, params["module"][0], params["name"][0], request.rfile.read().decode("UTF-8"))
			request.send_response_only(200, "OK")
			request.end_headers()
		except Exception as ex: print(vars(request)); print(ex); request.error_bad_request()

	def handle_delete_setting(self, request: ServiceRequestHandler) -> None:
		if not request.authenticated: request.error_unauthorized()
		params = request.get_params()
		try:
			modules.settings.config.provider.delete_setting(request.user, params["module"][0], params["name"][0])
			request.send_response_only(200, "OK")
			request.end_headers()
		except: request.error_bad_request()

	def handle_clear_setting(self, request: ServiceRequestHandler) -> None:
		if not request.authenticated: request.error_unauthorized()
		params = request.get_params()
		try:
			modules.settings.config.provider.clear_settings(request.user, params["module"][0])
			request.send_response_only(200, "OK")
			request.end_headers()
		except: request.error_bad_request()