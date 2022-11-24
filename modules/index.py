from server import ModuleInterface, ServerExtensionInterface, ServiceRequestHandler

class Module(ModuleInterface):
	def init(self, server: ServerExtensionInterface) -> None:
		server.api_handlers["/"] = self.handle_redirect

	def handle_redirect(self, request: ServiceRequestHandler) -> None:
		request.send_response_only(302, "Found")
		request.send_header("Location", "/dashboard/index.html")
		request.end_headers()