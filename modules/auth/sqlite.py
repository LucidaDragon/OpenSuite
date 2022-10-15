import os
import sqlite3

AUTH_DB = "./modules/auth/users.db"

is_new = not os.path.exists(AUTH_DB)

DB = sqlite3.connect(AUTH_DB)

if is_new:
	DB.execute("create table Users (Id integer primary key autoincrement, Username varchar(255), Password blob)")
	DB.commit()

def create_user(username: str, password: bytes) -> bool:
	if len(DB.execute("select * from Users where Username = :Username", { "Username": username }).fetchall()) > 0:
		return False
	
	DB.execute("insert into Users (Username, Password) values (:Username, :Password)", { "Username": username, "Password": password })
	DB.commit()
	return True

def validate_user(username: str, password: bytes) -> bool:
	result = DB.execute("select Password from Users where Username = :Username", { "Username": username }).fetchall()
	return len(result) > 0 and len(result[0]) == 1 and result[0][0] == password

def update_user(username: str, old_password: bytes, new_password: bytes) -> bool:
	if not validate_user(username, old_password): return False
	DB.execute("update Users set Password = :Password where Username = :Username", { "Username": username, "Password": new_password })
	DB.commit()

def delete_user(username: str, password: bytes) -> bool:
	if not validate_user(username, password): return False
	DB.execute("delete from Users where Username = :Username", { "Username": username })
	DB.commit()

def reset_user(username: str) -> bool:
	DB.execute("update Users set Password = :Password where Username = :Username", { "Username": username, "Password": None })
	DB.commit()