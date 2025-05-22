import io
import os
import sqlite3
import uuid
import threading
from typing import Optional, List, TypeVar, Type
from enum import Enum
import msgpack
import yaml
from io import BytesIO

T = TypeVar('T')

class DataFormat(Enum):
    MessagePack = 0
    Yaml = 1

class SqliteUserData:
    Illegal = set("`´'\"^[]\\//")
    
    def __init__(self, real, module, user_data_root=None, version="2.0.0.0", db_name=None):
        self.GlobalLock = threading.Lock()
        self.real_module = f"{real}.{module}"
        self.module = module
        
        self._userDataRoot = user_data_root
        self._dbName = db_name or "main.db"
        
        self.DBPath = os.path.join(self.UserDataRoot, self.DBName)
        self._Batch = threading.local()

        self.Version = version
        
        if not os.path.exists(self.UserDataRoot):
            os.makedirs(self.UserDataRoot)
            
        if not os.path.exists(self.DBPath):
            self._initialize_database()
    
    @property
    def UserDataRoot(self):
        return self._userDataRoot
    
    @property
    def DBName(self):
        return self._dbName or "main.db"
    
    @property
    def Batch(self):
        if not hasattr(self._Batch, 'value'):
            self._Batch.value = BatchContext(self)
        return self._Batch.value
    
    def _initialize_database(self):
        with self.Open(sqlite3.PARSE_DECLTYPES) as conn:
            conn.execute("""
                CREATE TABLE [meta] (
                    iid INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid VARCHAR(255) UNIQUE,
                    key VARCHAR(255),
                    keyfull VARCHAR(255),
                    registered BOOLEAN
                );
            """)
            conn.execute("""
                CREATE TABLE [data] (
                    iid INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) UNIQUE,
                    real VARCHAR(255) UNIQUE,
                    type VARCHAR(255) UNIQUE
                );
            """)
            conn.execute("""
                CREATE TABLE [file] (
                    iid INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) UNIQUE,
                    real VARCHAR(255) UNIQUE
                );
            """)
            conn.commit()
    
    def Open(self, mode=sqlite3.PARSE_DECLTYPES):
        """打开数据库连接"""
        conn = sqlite3.connect(self.DBPath, detect_types=mode)
        return conn
    
    def GetAllTables(self) -> List[str]:
        """获取所有表名"""
        with self.Open() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
            return [row[0] for row in cursor.fetchall()]
    
    def GetDataTable(self, type_name, create: bool) -> str:
        """获取或创建数据表"""
        real_name = f"{self.real_module}.{type_name}"
        name = f"data.{real_name}".translate(str.maketrans('', '', ''.join(self.Illegal)))
        full_type = f"{real_name}, {self.module}, Version={self.Version}, Culture=neutral, PublicKeyToken=null"
        
        if create:
            with self.Open() as conn:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS [{name}] (
                        iid INTEGER PRIMARY KEY AUTOINCREMENT,
                        uid VARCHAR(255) UNIQUE,
                        format INTEGER,
                        value BLOB
                    )
                """)
                conn.execute("""
                    INSERT OR IGNORE INTO data (name, real, type)
                    VALUES (?, ?, ?)
                """, (name, real_name, full_type))
                conn.commit()
        return name
    
    def GetFileTable(self, name: str, create: bool) -> str:
        """获取或创建文件表"""
        real_name = name
        table_name = f"file.{real_name}".translate(str.maketrans('', '', ''.join(self.Illegal)))
        
        if create:
            with self.Open() as conn:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS [{table_name}] (
                        iid INTEGER PRIMARY KEY AUTOINCREMENT,
                        uid VARCHAR(255) UNIQUE,
                        value BLOB
                    )
                """)
                conn.execute("""
                    INSERT OR IGNORE INTO file (name, real)
                    VALUES (?, ?)
                """, (table_name, real_name))
                conn.commit()
        return table_name
    
    def GetUID(self, key: str) -> str:
        """通过key获取UID"""
        if not key:
            return ""
        
        with self.Open() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uid FROM meta WHERE key = ? LIMIT 1", (key,))
            row = cursor.fetchone()
            return row[0] if row else ""
    
    def GetKey(self, uid: str) -> str:
        """通过UID获取key"""
        if not uid:
            return ""
        
        with self.Open() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key FROM meta WHERE uid = ? LIMIT 1", (uid,))
            row = cursor.fetchone()
            return row[0] if row else ""
    
    def CheckCleanup(self, uid: str) -> None:
        """检查并清理无用的UID数据"""
        with self.Open() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT registered FROM meta WHERE uid = ? LIMIT 1", (uid,))
            row = cursor.fetchone()
            
            if not row or row[0]:
                return
            
            # 检查其他表中是否还有该UID的数据
            for table in self.GetAllTables():
                if table == "meta":
                    continue
                
                cursor.execute(f"SELECT iid FROM [{table}] WHERE uid = ? LIMIT 1", (uid,))
                if cursor.fetchone():
                    return
            
            # 如果没有数据，则完全删除
            self.Wipe(uid)
    
    def Wipe(self, uid: str) -> None:
        """完全删除UID的所有数据"""
        try:
            with self.Open() as conn:
                for table in self.GetAllTables():
                    try:
                        conn.execute(f"DELETE FROM [{table}] WHERE uid = ?", (uid,))
                    except sqlite3.OperationalError:
                        continue
                conn.commit()
            return True
        except Exception as e:
            print(f"用户注销失败: {e}")
            return False
    
    def Create(self, uid: str, force_new_key: bool = False) -> str:
        """创建用户&Yaml或获取现有密钥"""
        with self.GlobalLock:
            key = self.GetKey(uid)
            if key and not force_new_key:
                return key
            
            while True:
                key_full = str(uuid.uuid4()).replace("-", "")
                key = key_full[:16]
                if not self.GetUID(key):
                    break
            
            os.makedirs(f"{self.UserDataRoot}/User/{uid}", exist_ok=True)
            with open(f"{self.UserDataRoot}/User/{uid}/BasicUserInfo.yaml", 'w') as f:
                yaml.dump({
                    "Name": uid,
                    "Discrim": "",
                    "Tags": ["user"]
                }, f)
            
            with self.Open() as conn:
                conn.execute("""
                    REPLACE INTO meta (uid, key, keyfull, registered)
                    VALUES (?, ?, ?, 1)
                """, (uid, key, key_full))
                conn.commit()

            return key
    
    def RegetKey(self, uid: str) -> None:
        """重新获取密钥"""
        with self.Open() as conn:
            new_key_full = str(uuid.uuid4()).replace("-", "")
            new_key = new_key_full[:16]
            conn.execute("""
                UPDATE meta SET keyfull = ? WHERE uid = ?
            """, (new_key_full, uid))
            conn.execute("""
                UPDATE meta SET key = ? WHERE uid = ?
            """, (new_key, uid))
            conn.commit()
        return new_key

    def insert_data(self, uid: str, name: str, data_type: Optional[Type], stream: io.IOBase) -> None:
        """初始化用户信息"""
        stream.seek(0)
        yaml_data = yaml.safe_load(stream)
    
        msgpack_data = msgpack.packb(yaml_data, use_bin_type=True)
        table = self.GetDataTable(name, create=True)

        with self.Open() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                REPLACE INTO [{table}] (uid, format, value)
                VALUES (?, ?, ?)
                """,
                (uid, "msgpack", msgpack_data)
            )
            if cursor.rowcount == 0:
                print(f"ERROR: InsertData: Failed to insert {table} for UID {uid}")
                return
            
    def write_file(self, uid, name):
        """
        BytesIO 流 sqlite接口
        """
        buffer = BytesIO()

        def save_to_db():
            buffer.seek(0)
            table = self.GetFileTable(name, create=True)
            with self.Open() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    REPLACE INTO '{table}' (uid, value)
                    VALUES (?, zeroblob(?))
                """, (uid, len(buffer.getvalue())))
                rowid = cursor.lastrowid
                if not rowid:
                    raise ValueError("Failed to get rowid")
                blob = conn.blobopen(table, "value", rowid)
                blob.write(buffer.getvalue())
                blob.close()
                conn.commit()

        buffer.close = lambda: (save_to_db(), buffer.__class__.close(buffer))
        return buffer

    def read_file(self, uid, name):
        """读取文件数据，返回 BytesIO 流"""
        table = self.GetFileTable(name, create=False)
        with self.Open() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT value FROM {table} WHERE uid = ?
            """, (uid,))
            row = cursor.fetchone()
            if not row:
                return None
            return BytesIO(row[0])

class BatchContext:
    def __init__(self, user_data: SqliteUserData):
        self.UserData = user_data
        self.Mode = None
        self.Connection = None
        self.Command = None
        self.Transaction = None
        self.Count = 0
    
    def Open(self, mode):
        if self.Connection and self.Command and (not self.Mode or self.Mode <= mode):
            return self.Connection
        
        if self.Connection:
            if self.Transaction:
                self.Transaction.commit()
                self.Transaction = None
            self.Command = None
            self.Connection.close()
            self.Connection = None
        
        self.Mode = mode
        self.Connection = self.UserData.Open(mode)
        self.Command = self.Connection.cursor()
        
        if mode <= sqlite3.PARSE_DECLTYPES:
            self.Transaction = self.Connection
        
        return self.Connection
    
    def Dispose(self):
        self.Count -= 1
        if self.Count <= 0:
            if self.Transaction:
                self.Transaction.commit()
                self.Transaction = None
            if self.Command:
                self.Command.close()
                self.Command = None
            if self.Connection:
                self.Connection.close()
                self.Connection = None
