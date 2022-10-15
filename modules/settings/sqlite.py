import os
import sqlite3

SETTINGS_DB = "./modules/settings/settings.db"

is_new = not os.path.exists(SETTINGS_DB)

DB = sqlite3.connect(SETTINGS_DB)

if is_new:
	DB.execute("create table Settings (Owner varchar(255), Module varchar(255), Name varchar(255), Value blob, primary key (Owner, Module, Name))")
	DB.commit()

def get_all_settings(owner: str) -> dict[str, dict[str, str]]:
	result: dict[str, dict[str, str]] = {}
	for module, name, value in DB.execute("select Module, Name, Value from Settings where Owner = :Owner", { "Owner": owner }).fetchall():
		if not module in result: result[module] = {}
		result[module][name] = value.decode("UTF-8")
	return result

def has_setting(owner: str, module: str, name: str) -> bool:
	return len(DB.execute("select Value from Settings where Owner = :Owner and Module = :Module and Name = :Name", { "Owner": owner, "Module": module, "Name": name }).fetchall()) > 0

def get_setting(owner: str, module: str, name: str) -> str | None:
	result = DB.execute("select Value from Settings where Owner = :Owner and Module = :Module and Name = :Name", { "Owner": owner, "Module": module, "Name": name }).fetchall()
	if len(result) > 0 and len(result[0]) > 0: return result[0][0].decode("UTF-8")
	else: return None

def set_setting(owner: str, module: str, name: str, value: str) -> None:
	DB.execute("replace into Settings (Owner, Module, Name, Value) values (:Owner, :Module, :Name, :Value)", { "Owner": owner, "Module": module, "Name": name, "Value": value.encode("UTF-8") })
	DB.commit()

def delete_setting(owner: str, module: str, name: str) -> None:
	DB.execute("delete from Settings where Owner = :Owner and Module = :Module and Name = :Name", { "Owner": owner, "Module": module, "Name": name })
	DB.commit()

def clear_settings(owner: str, module: str) -> None:
	DB.execute("delete from Settings where Owner = :Owner and Module = :Module", { "Owner": owner, "Module": module })
	DB.commit()