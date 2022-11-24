import json
from server import ModuleInterface, ServerExtensionInterface, ServiceRequestHandler

class Module(ModuleInterface):
	def __init__(self) -> None:
		self.cache = None

	def init(self, server: ServerExtensionInterface) -> None:
		server.api_handlers["/dashboard/icons"] = self.handle_icon_request

	def handle_icon_request(self, request: ServiceRequestHandler) -> None:
		result = json.dumps(self.get_all_icons(request)).encode("UTF-8")
		request.send_response_only(200, "OK")
		request.send_header("Content-Type", "application/json")
		request.send_header("Content-Length", len(result))
		request.end_headers()
		request.wfile.write(result)

	def get_all_icons(self, request: ServiceRequestHandler) -> dict[str, str]:
		modules = request.get_dashboard_modules()
		result: dict[str, str] = {}
		for module in modules: result[module] = modules[module](request)
		return result

	def get_default_settings(self) -> dict[str, str]:
		return {
			"icon-button-size": "\"8em\"",
			"icon-center-size": "\"6em\""
		}

	def get_html(self, request: ServiceRequestHandler) -> str:
		if self.cache == None:
			with open("./modules/dashboard/index.html", "r") as stream:
				self.cache = stream.read()
		return self.cache