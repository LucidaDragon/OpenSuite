import json
from server import ServiceRequestHandler
from typing import Callable

cache = None

def init(api_handlers: dict[str, Callable[[ServiceRequestHandler], None]], **kwargs) -> None:
	api_handlers["/dashboard/icons"] = handle_icon_request

def handle_icon_request(request: ServiceRequestHandler) -> None:
	result = json.dumps(get_all_icons(request)).encode("UTF-8")
	request.send_response_only(200, "OK")
	request.send_header("Content-Type", "application/json")
	request.send_header("Content-Length", len(result))
	request.end_headers()
	request.wfile.write(result)

def get_all_icons(request: ServiceRequestHandler) -> dict[str, str]:
	modules = request.get_dashboard_modules()
	result: dict[str, str] = {}
	for module in modules: result[module] = modules[module](request)
	return result

def get_default_settings() -> dict[str, str]:
	return {
		"icon-button-size": "\"8em\"",
		"icon-center-size": "\"6em\""
	}

def get_html(**kwargs) -> str:
	global cache
	if cache == None:
		with open("./modules/dashboard/index.html", "r") as stream:
			cache = stream.read()
	return cache