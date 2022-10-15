import base64
import modules.auth.config
import datetime
import hashlib
import json
import secrets
from server import ServiceRequestHandler
from typing import Callable

class Session:
	def __init__(self, token: str, username: str) -> None:
		self.token = token
		self.username = username
		self.last_refresh = datetime.datetime.now()

	def refresh(self) -> None:
		self.last_refresh = datetime.datetime.now()

	def check(self) -> bool:
		return (datetime.datetime.now() - self.last_refresh).total_seconds() < 900

SESSIONS: dict[str, Session] = {}

cache = None

def init(api_handlers: dict[str, Callable[[ServiceRequestHandler], None]], authorization_modules: list[Callable[[ServiceRequestHandler], bool]], **kwargs) -> None:
	api_handlers["/auth/register"] = lambda request: any_handler(modules.auth.config.provider.create_user, request)
	api_handlers["/auth/login"] = lambda request: any_handler(modules.auth.config.provider.validate_user, request)
	api_handlers["/auth/modify"] = lambda request: any_handler(modules.auth.config.provider.update_user, request)
	api_handlers["/auth/delete"] = lambda request: any_handler(modules.auth.config.provider.delete_user, request)
	api_handlers["/auth/ping"] = success_handler
	authorization_modules.append(refresh_token)

def get_html(**kwargs):
	global cache
	if cache == None:
		with open("./modules/auth/index.html", "r") as stream:
			cache = stream.read()
	return cache

def success_handler(request: ServiceRequestHandler) -> None:
	if request.authenticated:
		request.send_response_only(200, "OK")
		request.end_headers()
	else:
		request.error_unauthorized()

def hash_and_salt(username: str, password: bytes) -> bytes:
	return hashlib.sha512((modules.auth.config.salt + ":osuite:" + username).encode("UTF-8") + password).digest()

def any_handler(target: Callable[[str, bytes], bool], request: ServiceRequestHandler) -> None:
	try:
		password_length = int(request.headers.get("Content-Length"))
		if password_length > 1024: raise Exception()
		username = request.get_params()["username"][0]
		password = hash_and_salt(username, request.rfile.read(password_length))
	except:
		request.error_bad_request()
		return

	success = target(username, password)
	token = None

	if success:
		token = base64.b64encode(secrets.token_bytes(512)).decode("UTF-8")
		SESSIONS[token] = Session(token, username)

	body = json.dumps({ "success": success, "token": token }).encode("UTF-8")
	request.send_response_only(200, "OK")
	request.send_header("Content-Type", "application/json")
	request.send_header("Content-Length", len(body))
	request.end_headers()
	request.wfile.write(body)

def refresh_token(request: ServiceRequestHandler) -> bool:
	token = request.get_token()
	request.authenticated = False
	request.user = None
	if token != None:
		if token in SESSIONS:
			session = SESSIONS[token]
			if session.check():
				session.refresh()
				request.authenticated = True
				request.user = session.username
			else:
				SESSIONS.pop(token)
				request.error_unauthorized()
				return False
		else:
			request.error_unauthorized()
			return False
	return True