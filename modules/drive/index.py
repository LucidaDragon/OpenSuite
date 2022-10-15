import io
import json
import shutil
import modules.drive.config
from server import ServiceRequestHandler
from typing import Callable

cache = None
icon_cache = None

def init(api_handlers: dict[str, Callable[[ServiceRequestHandler], None]], **kwargs):
	api_handlers["/drive/directory/create"] = handle_create_directory
	api_handlers["/drive/directory/children"] = handle_get_children
	api_handlers["/drive/delete"] = handle_delete
	api_handlers["/drive/file"] = handle_file_request
	api_handlers["/drive/rename"] = handle_rename
	api_handlers["/drive/publish"] = handle_publish
	api_handlers["/drive/path"] = handle_get_path

def get_html(**kwargs):
	global cache
	if cache == None:
		with open("./modules/drive/index.html", "r") as stream:
			cache = stream.read()
	return cache

def get_icon_html(request: ServiceRequestHandler) -> str:
	global icon_cache
	if icon_cache == None:
		with open("./modules/drive/icon.svg", "r") as stream:
			icon_cache = stream.read()
	return icon_cache

def get_default_settings() -> dict[str, str]:
	return {
		"icon-button-size": "\"8em\"",
		"icon-center-size": "\"6em\""
	}

def get_entry_info(entry: int) -> dict[str, bool | str | int | None]:
	owner = modules.drive.config.provider.get_owner(entry)
	return { "name": modules.drive.config.provider.get_name(owner, entry), "owner": owner, "id": entry, "created": modules.drive.config.provider.get_creation_date(owner, entry), "parent": modules.drive.config.provider.get_parent(owner, entry), "directory": modules.drive.config.provider.is_directory(owner, entry), "public": modules.drive.config.provider.is_public_file(owner, entry) }

def expand_request(request: ServiceRequestHandler, handler: Callable) -> None:
	handler(request, **request.get_params())

def handle_create_directory(request: ServiceRequestHandler) -> None:
	if not request.authenticated:
		request.error_unauthorized()
		return
	try:
		params = request.get_params()
		name = params["name"]
		try: parent = params["parent"]
		except: parent = []
		directory_id = None if len(parent) == 0 else int(parent[0])
		if directory_id == None or modules.drive.config.provider.is_directory(request.user, directory_id):
			directory_id = modules.drive.config.provider.create_directory(request.user, name[0], directory_id)
			result = json.dumps({ "success": True, "directory": get_entry_info(directory_id) }).encode("UTF-8")
			request.send_response_only(200, "OK")
			request.send_header("Content-Type", "application/json")
			request.send_header("Content-Length", len(result))
			request.end_headers()
			request.wfile.write(result)
		else:
			request.error_bad_request()
	except: request.error_bad_request()

def handle_get_children(request: ServiceRequestHandler) -> None:
	if not request.authenticated:
		request.error_unauthorized()
		return
	try:
		params = request.get_params()
		directory_id = int(params["parent"][0]) if "parent" in params else None
		result = json.dumps({ "success": True, "children": [get_entry_info(entry) for entry in modules.drive.config.provider.get_entries(request.user, directory_id)] }).encode("UTF-8")
		request.send_response_only(200, "OK")
		request.send_header("Content-Type", "application/json")
		request.send_header("Content-Length", len(result))
		request.end_headers()
		request.wfile.write(result)
	except: request.error_bad_request()

def handle_file_request(request: ServiceRequestHandler) -> None:
	if request.method == "GET": handle_file_get_request(**request.get_params())
	elif request.method == "POST": handle_file_post_request(**request.get_params())
	else: request.error_bad_request()

def string_to_unicode_escapes(value: str) -> str:
	return "".join([hex(ord(c)).replace("0x", "%") for c in value])

def handle_file_get_request(request: ServiceRequestHandler, owner: list[str], file: list[str], embed: list[str] = [], **kwargs) -> None:
	try:
		owner = owner[0]
		file_id = int(file[0])
		embed = len(embed) > 0 and embed[0].lower() == "true"
		if not modules.drive.config.provider.is_file(owner, file_id):
			request.error_not_found()
			return
		elif modules.drive.config.provider.is_private_file(owner, file_id):
			if not (request.authenticated and modules.drive.config.provider.get_owner(file_id) == request.user):
				request.error_unauthorized()
				return
		with modules.drive.config.provider.get_data(owner, file_id) as stream:
			stream.seek(0, io.SEEK_END)
			file_size = stream.tell()
			stream.seek(0, io.SEEK_SET)
			request.send_response_only(200, "OK")
			request.send_header("Content-Type", "application/octet-stream")
			request.send_header("Content-Length", file_size)
			request.send_header("Content-Disposition", "inline" if embed else f"attachment; filename*=UTF-8''{string_to_unicode_escapes(modules.drive.config.provider.get_name(owner, file_id))}")
			request.end_headers()
			shutil.copyfileobj(stream, request.wfile)
	except: request.error_bad_request()

def handle_file_post_request(request: ServiceRequestHandler, name: list[str], parent: list[int] = [], **kwargs) -> None:
	if not request.authenticated:
		request.error_unauthorized()
		return
	if not "Content-Length" in request.headers:
		request.error_bad_request()
		return
	try:
		directory_id = None if len(parent) == 0 else int(parent[0])
		file_size = int(request.headers["Content-Length"])
		if directory_id == None or modules.drive.config.provider.is_directory(request.user, directory_id):
			file_id = modules.drive.config.provider.create_file(request.user, name[0], directory_id, file_size, request.rfile)
			try:
				result = json.dumps({ "success": True, "file": get_entry_info(file_id) }).encode("UTF-8")
				request.send_response_only(200, "OK")
				request.send_header("Content-Type", "application/json")
				request.send_header("Content-Length", len(result))
				request.end_headers()
				request.wfile.write(result)
			except Exception as ex:
				modules.drive.config.provider.delete_entry(request.user, file_id)
				raise ex
		else:
			request.error_unauthorized()
	except: request.error_bad_request()

def handle_delete(request: ServiceRequestHandler) -> None:
	if not request.authenticated:
		request.error_unauthorized()
		return
	try:
		params = request.get_params()
		entry_id = int(params["id"][0])
		modules.drive.config.provider.delete_entry(request.user, entry_id)
		request.send_response_only(200, "OK")
		request.end_headers()
	except:
		request.error_bad_request()

def handle_rename(request: ServiceRequestHandler) -> None:
	if not request.authenticated:
		request.error_unauthorized()
		return
	try:
		params = request.get_params()
		entry_id = int(params["id"][0])
		entry_name = params["name"][0]
		modules.drive.config.provider.rename_entry(request.user, entry_id, entry_name)
		request.send_response_only(200, "OK")
		request.end_headers()
	except:
		request.error_bad_request()

def handle_publish(request: ServiceRequestHandler) -> None:
	if not request.authenticated:
		request.error_unauthorized()
		return
	try:
		params = request.get_params()
		entry_id = int(params["id"][0])
		entry_state = params["public"][0].lower()
		if modules.drive.config.provider.is_file(request.user, entry_id) and (entry_state == "true" or entry_state == "false"):
			modules.drive.config.provider.set_entry_public(request.user, entry_id, entry_state == "true")
			request.send_response_only(200, "OK")
			request.end_headers()
		else:
			request.error_bad_request()
	except:
		request.error_bad_request()

def handle_get_path(request: ServiceRequestHandler) -> None:
	if not request.authenticated:
		request.error_unauthorized()
		return
	try:
		entry_id = int(request.get_params()["id"][0])
		result = json.dumps(modules.drive.config.provider.get_entry_path(request.user, entry_id)).encode("UTF-8")
		request.send_response_only(200, "OK")
		request.send_header("Content-Type", "application/json")
		request.send_header("Content-Length", len(result))
		request.end_headers()
		request.wfile.write(result)
	except:
		request.error_bad_request()