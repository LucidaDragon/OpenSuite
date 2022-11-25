from server import ModuleInterface, ServerExtensionInterface, ServiceRequestHandler

class Module(ModuleInterface):
	def __init__(self) -> None:
		self.cache = None
		self.icon_cache = None

	def get_html(self, request: ServiceRequestHandler) -> str:
		if self.cache == None:
			with open("./modules/calendar/index.html", "r") as stream:
				self.cache = stream.read()
		return self.cache

	def is_dashboard_module(self) -> bool:
		return True

	def get_icon_html(self, request: ServiceRequestHandler) -> str:
		if self.icon_cache == None:
			with open("./modules/calendar/icon.svg", "r") as stream:
				self.icon_cache = stream.read()
		return self.icon_cache