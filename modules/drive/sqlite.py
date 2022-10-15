import datetime
import io
import os
import sqlite3

DRIVE_FILES = "./modules/drive/files"
DRIVE_DB = "./modules/drive/files.db"
TYPE_FILE = 0
TYPE_PUBLIC_FILE = 1
TYPE_DIRECTORY = 2
BLOCK_SIZE = 1048576

is_new = not os.path.exists(DRIVE_DB)

DB = sqlite3.connect(DRIVE_DB)

if not os.path.isdir(DRIVE_FILES): os.mkdir(DRIVE_FILES)

if is_new:
	DB.execute("create table Files (Id integer primary key autoincrement, Type integer, Owner varchar(255), Name varchar(255), Created datetime, Parent integer, Data integer, foreign key (Id) references Files (Id))")
	DB.commit()

available_slots: list[int] = []
top_available_slot: int = 0

def get_next_file_slot() -> int:
	global top_available_slot
	if len(available_slots) > 0: return available_slots.pop()
	result = top_available_slot
	while os.path.isfile(get_path_from_slot(result)): result += 1
	top_available_slot = result
	return result

def get_path_from_slot(slot: int) -> str:
	return f"{DRIVE_FILES}/{slot}"

def get_next_file_info() -> tuple[str, int]:
	slot = get_next_file_slot()
	return get_path_from_slot(slot), slot

def create_directory(owner: str, name: str, parent: int | None) -> int:
	result = DB.execute("insert into Files (Type, Owner, Name, Created, Parent) values (:Type, :Owner, :Name, :Created, :Parent)", { "Type": TYPE_DIRECTORY, "Owner": owner, "Name": name, "Created": datetime.datetime.utcnow(), "Parent": parent }).lastrowid
	DB.commit()
	return result

def create_file(owner: str, name: str, parent: int, length: int, data: io.IOBase) -> int:
	path, slot = get_next_file_info()
	try:
		with open(path, "wb") as stream:
			while length > BLOCK_SIZE:
				stream.write(data.read(BLOCK_SIZE))
				length -= BLOCK_SIZE
			stream.write(data.read(length))
	except Exception as ex:
		try: os.remove(path)
		except: pass
		raise ex
	result = DB.execute("insert into Files (Type, Owner, Name, Created, Parent, Data) values (:Type, :Owner, :Name, :Created, :Parent, :Data)", { "Type": TYPE_FILE, "Owner": owner, "Name": name, "Created": datetime.datetime.utcnow(), "Parent": parent, "Data": slot }).lastrowid
	DB.commit()
	return result

def is_file(owner: str, directory_or_file: int) -> bool:
	result = DB.execute("select Type from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return False
	return result[0][0] == TYPE_FILE or result[0][0] == TYPE_PUBLIC_FILE

def is_private_file(owner: str, directory_or_file: int) -> bool:
	result = DB.execute("select Type from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return False
	return result[0][0] == TYPE_FILE

def is_public_file(owner: str, directory_or_file: int) -> bool:
	result = DB.execute("select Type from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return False
	return result[0][0] == TYPE_PUBLIC_FILE

def is_directory(owner: str, directory_or_file: int) -> bool:
	result = DB.execute("select Type from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return False
	return result[0][0] == TYPE_DIRECTORY

def get_name(owner: str, directory_or_file: int) -> str | None:
	result = DB.execute("select Name from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return None
	return result[0][0]

def get_owner(directory_or_file: int) -> str | None:
	result = DB.execute("select Owner from Files where Id = :Id", { "Id": directory_or_file }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return None
	return result[0][0]

def get_creation_date(owner: str, directory_or_file: int) -> datetime.datetime | None:
	result = DB.execute("select Created from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return None
	return result[0][0]

def get_parent(owner: str, directory_or_file: int) -> int | None:
	result = DB.execute("select Parent from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return None
	return result[0][0]

def get_data(owner: str, file: int) -> io.IOBase | None:
	result = DB.execute("select Data from Files where Id = :Id and Owner = :Owner", { "Id": file, "Owner": owner }).fetchall()
	if len(result) == 0 or len(result[0]) == 0: return None
	return open(get_path_from_slot(result[0][0]), "rb")

def get_entries(owner: str, directory: int | None) -> list[int]:
	result = DB.execute("select Id from Files where ((Parent is null and :Parent is null) or (Parent = :Parent)) and Owner = :Owner", { "Parent": directory, "Owner": owner }).fetchall()
	for i in range(len(result)): result[i] = result[i][0]
	return result

def get_files(owner: str, directory: int | None) -> list[int]:
	result = DB.execute("select Id from Files where (Type = :TypeA or Type = :TypeB) and ((Parent is null and :Parent is null) or (Parent = :Parent)) and Owner = :Owner", { "TypeA": TYPE_FILE, "TypeB": TYPE_PUBLIC_FILE, "Parent": directory, "Owner": owner }).fetchall()
	for i in range(len(result)): result[i] = result[i][0]
	return result

def get_directories(owner: str, directory: int | None) -> list[int]:
	result = DB.execute("select Id from Files where Type = :Type and ((Parent is null and :Parent is null) or (Parent = :Parent)) and Owner = :Owner", { "Type": TYPE_DIRECTORY, "Parent": directory, "Owner": owner }).fetchall()
	for i in range(len(result)): result[i] = result[i][0]
	return result

def delete_entry(owner: str, directory_or_file: int) -> None:
	for child in get_entries(owner, directory_or_file): delete_entry(owner, child)
	for slot in DB.execute("select Data from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner }).fetchall():
		path = get_path_from_slot(slot[0])
		if os.path.isfile(path): os.remove(path)
	DB.execute("delete from Files where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner })
	DB.commit()

def rename_entry(owner: str, directory_or_file: int, name: str) -> None:
	DB.execute("update Files set Name = :Name where Id = :Id and Owner = :Owner", { "Id": directory_or_file, "Owner": owner, "Name": name })
	DB.commit()

def set_entry_public(owner: str, file: int, state: bool) -> None:
	DB.execute("update Files set Type = :Type where Id = :Id and Owner = :Owner and (Type = :PublicType or Type = :PrivateType)", { "Id": file, "Owner": owner, "Type": TYPE_PUBLIC_FILE if state else TYPE_FILE, "PublicType": TYPE_PUBLIC_FILE, "PrivateType": TYPE_FILE })
	DB.commit()

def get_entry_path(owner: str, directory_or_file: int) -> str | None:
	parent_id = get_parent(owner, directory_or_file)
	if parent_id == None: prefix = "/"
	else: prefix = get_entry_path(owner, parent_id) + "/"
	name = get_name(owner, directory_or_file)
	if name == None: return None
	return prefix + name