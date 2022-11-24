import datetime
import http.client
import json
import os
import modules.settings.config
import re
import urllib.parse
import urllib.request

from server import ModuleInterface, ServerExtensionInterface, ServiceRequestHandler

DDG_SPICE_FORECAST_URL = "https://duckduckgo.com/js/spice/forecast/"
DDG_WEATHER_ICONS_URL = "https://duckduckgo.com/assets/weather/icons/"
COLOR_REGEX = re.compile(r"[A-Fa-f0-9]+")

class Module(ModuleInterface):
	def __init__(self) -> None:
		self.cache = None
		self.request_cache: dict | None = None
		self.request_time: datetime.datetime | None = None

	def init(self, server: ServerExtensionInterface) -> None:
		server.api_handlers["/weather/get"] = self.handle_weather

	def is_dashboard_module(self) -> bool: return True

	def get_html(self, request: ServiceRequestHandler) -> str:
		if self.cache == None:
			with open("./modules/weather/index.html", "r") as stream:
				self.cache = stream.read()
		return self.cache

	def get_icon_html(self, request: ServiceRequestHandler) -> str:
		if not request.authenticated:
			request.error_unauthorized()
			return ""
		city = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "city"))
		province = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "region"))
		country = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "country"))
		lang = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "language-code"))
		weather = self.get_weather_info(city, province, country, lang)
		src = ""
		if "currently" in weather and "icon" in weather["currently"]:
			src = self.get_weather_icon(weather["currently"]["icon"])
		return f"<img src=\"{src}\" style=\"width: var(--icon-center-size); height: var(--icon-center-size);\">"

	def get_default_settings(self) -> dict[str, str]:
		return {
			"city": "\"Toronto\"",
			"region": "\"Ontario\"",
			"country": "\"Canada\"",
			"language-code": "\"en\"",
			"temperature-unit": "\"C\""
		}

	def handle_weather(self, request: ServiceRequestHandler) -> None:
		if not request.authenticated:
			request.error_unauthorized()
			return
		city = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "city"))
		province = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "region"))
		country = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "country"))
		lang = json.loads(modules.settings.config.provider.get_setting(request.user, "weather", "language-code"))
		tempF = None
		tempC = None
		weather = self.get_weather_info(city, province, country, lang)
		if "currently" in weather:
			current = weather["currently"]
			if "icon" in current: current["icon-path"] = self.get_weather_icon(current["icon"])
			if "temperature" in current:
				tempF = current["temperature"]
				tempC = (tempF - 32.0) * (5.0 / 9.0)
				current["temperature-f"] = tempF
				current["temperature-c"] = tempC
		result = json.dumps(weather).encode("UTF-8")
		request.send_response_only(200, "OK")
		request.send_header("Content-Type", "application/json")
		request.send_header("Content-Length", len(result))
		request.end_headers()
		request.wfile.write(result)

	def get_weather_info(self, city: str, province: str, country: str, lang: str) -> dict:
		if self.request_time != None and (datetime.datetime.now() - self.request_time).total_seconds() < 300: return self.request_cache
		json_str = ""
		try:
			location = f"{city} {province} {country}/{lang}"
			response: http.client.HTTPResponse = urllib.request.urlopen(DDG_SPICE_FORECAST_URL + urllib.parse.quote(location))
			json_str = f"[{response.read().decode('UTF-8')[19:-3]}]"
			response.close()
			self.request_cache = json.loads(json_str)[0]
			self.request_time = datetime.datetime.now()
			return self.request_cache
		except Exception as ex:
			self.request_cache = None
			self.request_time = None
			return { "error": ex, "content": json_str }

	def get_weather_icon(self, icon: str) -> str:
		file = f"./modules/weather/icons/{icon}.svg"
		if not os.path.isfile(file):
			try:
				response: http.client.HTTPResponse = urllib.request.urlopen(DDG_WEATHER_ICONS_URL + urllib.parse.quote(icon) + ".svg")
				with open(file, "wb") as stream: stream.write(response.read())
			except: pass
		return f"/weather/icons/{icon}.svg"