# """
# DNACryptDB Core Engine
# Handles MySQL and MongoDB operations with custom query language
# """

# import mysql.connector
# from mysql.connector import Error
# from pymongo import MongoClient
# from pymongo.errors import PyMongoError
# import json
# import re
# from typing import Dict, Any, List
# from datetime import datetime
# import os

# class DNACryptDB:
#     """Core DNACryptDB Engine"""
    
#     def __init__(self, config_file: str = "dnacdb.config.json", verbose: bool = True):
#         """
#         Initialize DNACryptDB with configuration file
        
#         Args:
#             config_file: Path to JSON configuration file
#             verbose: Print connection status messages
#         """
#         self.mysql_conn = None
#         self.mysql_cursor = None
#         self.mongo_client = None
#         self.mongo_db = None
#         self.schema_registry = {}
#         self.verbose = verbose
        
#         if os.path.exists(config_file):
#             self._load_config(config_file)
#         else:
#             raise FileNotFoundError(
#                 f"Config file not found: {config_file}\n"
#                 f"Run 'dnacryptdb init' to create one."
#             )
    
#     def _load_config(self, config_file: str):
#         """Load database configuration from JSON file"""
#         with open(config_file, 'r') as f:
#             config = json.load(f)
        
#         mysql_config = config.get('mysql', {})
#         mongo_config = config.get('mongodb', {})
        
#         # Connect to MySQL
#         try:
#             # Create database if doesn't exist
#             temp_conn = mysql.connector.connect(
#                 host=mysql_config['host'],
#                 user=mysql_config['user'],
#                 password=mysql_config['password']
#             )
#             temp_cursor = temp_conn.cursor()
#             temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_config['database']}")
#             temp_cursor.close()
#             temp_conn.close()
            
#             # Connect to database
#             self.mysql_conn = mysql.connector.connect(**mysql_config)
#             self.mysql_cursor = self.mysql_conn.cursor(dictionary=True)
            
#             if self.verbose:
#                 print(f"✓ MySQL connected: {mysql_config['database']}")
#         except Error as e:
#             if self.verbose:
#                 print(f"⚠ MySQL connection failed: {e}")
        
#         # Connect to MongoDB
#         try:
#             self.mongo_client = MongoClient(
#                 mongo_config['uri'], 
#                 serverSelectionTimeoutMS=5000
#             )
#             self.mongo_client.admin.command('ping')
#             self.mongo_db = self.mongo_client[mongo_config['database']]
            
#             if self.verbose:
#                 print(f"✓ MongoDB connected: {mongo_config['database']}")
#         except Exception as e:
#             if self.verbose:
#                 print(f"⚠ MongoDB connection failed: {e}")
    
#     def execute(self, query: str) -> Dict[str, Any]:
#         """
#         Execute single DNACryptDB query
        
#         Args:
#             query: DNACryptDB query string
            
#         Returns:
#             Dict with status and results
#         """
#         query = query.strip()
        
#         # Skip comments and empty lines
#         if not query or query.startswith('#') or query.startswith('--'):
#             return {"status": "comment"}
        
#         try:
#             if query.upper().startswith('MAKE TABLE'):
#                 return self._make_table(query)
#             elif query.upper().startswith('MAKE COLLECTION'):
#                 return self._make_collection(query)
#             elif query.upper().startswith('PUT INTO'):
#                 return self._put_data(query)
#             elif query.upper().startswith('FETCH FROM'):
#                 return self._fetch_data(query)
#             elif query.upper().startswith('CHANGE IN'):
#                 return self._change_data(query)
#             elif query.upper().startswith('REMOVE FROM'):
#                 return self._remove_data(query)
#             elif query.upper().startswith('SHOW TABLES'):
#                 return self._show_tables()
#             elif query.upper().startswith('SHOW COLLECTIONS'):
#                 return self._show_collections()
#             elif query.upper().startswith('DROP'):
#                 return self._drop(query)
#             else:
#                 return {
#                     "error": "Unknown command",
#                     "hint": "Available: MAKE TABLE, MAKE COLLECTION, PUT INTO, FETCH FROM, CHANGE IN, REMOVE FROM, SHOW TABLES, SHOW COLLECTIONS, DROP"
#                 }
#         except Exception as e:
#             return {"error": str(e)}
    
#     def execute_file(self, filepath: str) -> List[Dict]:
#         """
#         Execute all queries in a .dnacdb file
        
#         Args:
#             filepath: Path to .dnacdb script file
            
#         Returns:
#             List of result dictionaries
#         """
#         if not os.path.exists(filepath):
#             raise FileNotFoundError(f"File not found: {filepath}")
        
#         with open(filepath, 'r') as f:
#             lines = f.readlines()
        
#         # Parse queries properly - handle multi-line and comments
#         queries = []
#         current_query = []
        
#         for line in lines:
#             line = line.strip()
            
#             # Skip empty lines and comments
#             if not line or line.startswith('#') or line.startswith('--'):
#                 continue
            
#             # Add line to current query
#             current_query.append(line)
            
#             # If line ends with semicolon, complete the query
#             if line.endswith(';'):
#                 full_query = ' '.join(current_query).rstrip(';')
#                 queries.append(full_query)
#                 current_query = []
        
#         # Add last query if no semicolon at end
#         if current_query:
#             full_query = ' '.join(current_query)
#             queries.append(full_query)
        
#         # Execute all queries
#         results = []
#         for i, query in enumerate(queries, 1):
#             query = query.strip()
#             if not query:
#                 continue
            
#             if self.verbose:
#                 print(f"\n[Query {i}] {query[:60]}{'...' if len(query) > 60 else ''}")
            
#             result = self.execute(query)
#             results.append(result)
            
#             if self.verbose:
#                 if result.get('status') == 'success':
#                     print(f"  ✓ Success")
#                 elif result.get('error'):
#                     print(f"  ✗ Error: {result['error']}")
        
#         return results
    
#     def _make_table(self, query: str) -> Dict:
#         """Create MySQL table (relational)"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(r'MAKE TABLE (\w+) WITH\s*\((.*?)\)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax. Use: MAKE TABLE name WITH (field:type, ...)"}
            
#             table_name = match.group(1)
#             fields_str = match.group(2)
            
#             # Type mapping
#             type_mapping = {
#                 'int': 'INT',
#                 'integer': 'INT',
#                 'text': 'VARCHAR(255)',
#                 'string': 'VARCHAR(255)',
#                 'float': 'FLOAT',
#                 'double': 'DOUBLE',
#                 'date': 'DATE',
#                 'datetime': 'DATETIME',
#                 'timestamp': 'TIMESTAMP',
#                 'bool': 'BOOLEAN',
#                 'boolean': 'BOOLEAN'
#             }
            
#             fields = ['id INT AUTO_INCREMENT PRIMARY KEY']
#             field_schema = {}
            
#             for field in fields_str.split(','):
#                 field = field.strip()
#                 if ':' in field:
#                     name, ftype = field.split(':')
#                     name = name.strip()
#                     ftype = ftype.strip().lower()
                    
#                     if name.lower() != 'id':
#                         sql_type = type_mapping.get(ftype, 'VARCHAR(255)')
#                         fields.append(f"{name} {sql_type}")
#                         field_schema[name] = ftype
            
#             # Create table
#             create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(fields)})"
#             self.mysql_cursor.execute(create_sql)
#             self.mysql_conn.commit()
            
#             # Register schema
#             self.schema_registry[table_name] = {
#                 'backend': 'mysql',
#                 'type': 'table',
#                 'fields': field_schema
#             }
            
#             return {
#                 "status": "success",
#                 "message": f"Table '{table_name}' created",
#                 "backend": "MySQL",
#                 "table": table_name,
#                 "fields": field_schema
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": f"MySQL error: {str(e)}"}
    
#     def _make_collection(self, query: str) -> Dict:
#         """Create MongoDB collection (document store)"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(r'MAKE COLLECTION (\w+)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax. Use: MAKE COLLECTION name"}
            
#             coll_name = match.group(1)
            
#             # Create collection
#             if coll_name not in self.mongo_db.list_collection_names():
#                 self.mongo_db.create_collection(coll_name)
            
#             # Create index on created_at
#             self.mongo_db[coll_name].create_index("created_at")
            
#             # Register schema
#             self.schema_registry[coll_name] = {
#                 'backend': 'mongodb',
#                 'type': 'collection'
#             }
            
#             return {
#                 "status": "success",
#                 "message": f"Collection '{coll_name}' created",
#                 "backend": "MongoDB",
#                 "collection": coll_name
#             }
            
#         except PyMongoError as e:
#             return {"error": f"MongoDB error: {str(e)}"}
    
#     def _put_data(self, query: str) -> Dict:
#         """Insert data into table or collection"""
#         try:
#             match = re.search(r'PUT INTO (\w+) DATA\s*({.*?})$', 
#                             query, re.IGNORECASE | re.DOTALL)
#             if not match:
#                 return {"error": "Invalid syntax. Use: PUT INTO target DATA {json}"}
            
#             target = match.group(1)
#             data_str = match.group(2)
            
#             # Parse JSON
#             data_str = data_str.replace("'", '"')
#             data = json.loads(data_str)
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist. Create it first."}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 return self._put_into_mysql(target, data)
#             else:
#                 return self._put_into_mongo(target, data)
                
#         except json.JSONDecodeError as e:
#             return {"error": f"Invalid JSON: {str(e)}"}
#         except Exception as e:
#             return {"error": f"Insert failed: {str(e)}"}
    
#     def _put_into_mysql(self, table: str, data: Dict) -> Dict:
#         """Insert into MySQL table"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             fields = list(data.keys())
#             placeholders = ', '.join(['%s' for _ in fields])
#             values = [data[f] for f in fields]
            
#             insert_sql = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
#             self.mysql_cursor.execute(insert_sql, values)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "backend": "MySQL",
#                 "inserted_id": self.mysql_cursor.lastrowid,
#                 "data": data
#             }
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": f"MySQL insert failed: {str(e)}"}
    
#     def _put_into_mongo(self, collection: str, data: Dict) -> Dict:
#         """Insert into MongoDB collection"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             # Add timestamp
#             data['created_at'] = datetime.utcnow()
            
#             result = self.mongo_db[collection].insert_one(data)
            
#             return {
#                 "status": "success",
#                 "backend": "MongoDB",
#                 "inserted_id": str(result.inserted_id),
#                 "data": data
#             }
#         except PyMongoError as e:
#             return {"error": f"MongoDB insert failed: {str(e)}"}
    
#     def _fetch_data(self, query: str) -> Dict:
#         """Fetch data from table or collection"""
#         try:
#             match = re.search(r'FETCH FROM (\w+)\s+(?:WHERE\s+(.*)|ALL)', 
#                             query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax. Use: FETCH FROM source WHERE condition or FETCH FROM source ALL"}
            
#             source = match.group(1)
#             condition = match.group(2)
            
#             if source not in self.schema_registry:
#                 return {"error": f"Source '{source}' does not exist"}
            
#             backend = self.schema_registry[source]['backend']
            
#             if backend == 'mysql':
#                 return self._fetch_from_mysql(source, condition)
#             else:
#                 return self._fetch_from_mongo(source, condition)
                
#         except Exception as e:
#             return {"error": f"Fetch failed: {str(e)}"}
    
#     def _fetch_from_mysql(self, table: str, condition: str) -> Dict:
#         """Fetch from MySQL"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             if condition:
#                 query_sql = f"SELECT * FROM {table} WHERE {condition}"
#             else:
#                 query_sql = f"SELECT * FROM {table}"
            
#             self.mysql_cursor.execute(query_sql)
#             results = self.mysql_cursor.fetchall()
            
#             return {
#                 "status": "success",
#                 "backend": "MySQL",
#                 "count": len(results),
#                 "data": results
#             }
#         except Error as e:
#             return {"error": f"MySQL fetch failed: {str(e)}"}
    
#     def _fetch_from_mongo(self, collection: str, condition: str) -> Dict:
#         """Fetch from MongoDB"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             if condition:
#                 mongo_filter = self._parse_condition(condition)
#             else:
#                 mongo_filter = {}
            
#             results = list(self.mongo_db[collection].find(mongo_filter))
            
#             # Convert ObjectId and datetime to string
#             for r in results:
#                 r['_id'] = str(r['_id'])
#                 if 'created_at' in r:
#                     r['created_at'] = r['created_at'].isoformat()
            
#             return {
#                 "status": "success",
#                 "backend": "MongoDB",
#                 "count": len(results),
#                 "data": results
#             }
#         except PyMongoError as e:
#             return {"error": f"MongoDB fetch failed: {str(e)}"}
    
#     def _change_data(self, query: str) -> Dict:
#         """Update data in table or collection"""
#         try:
#             match = re.search(r'CHANGE IN (\w+) SET\s+(.*?)\s+WHERE\s+(.*)', 
#                             query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax. Use: CHANGE IN target SET field=value WHERE condition"}
            
#             target = match.group(1)
#             set_clause = match.group(2)
#             condition = match.group(3)
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 return self._change_in_mysql(target, set_clause, condition)
#             else:
#                 return self._change_in_mongo(target, set_clause, condition)
                
#         except Exception as e:
#             return {"error": f"Update failed: {str(e)}"}
    
#     def _change_in_mysql(self, table: str, set_clause: str, condition: str) -> Dict:
#         """Update MySQL table"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             update_sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
#             self.mysql_cursor.execute(update_sql)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "backend": "MySQL",
#                 "updated": self.mysql_cursor.rowcount
#             }
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": f"MySQL update failed: {str(e)}"}
    
#     def _change_in_mongo(self, collection: str, set_clause: str, condition: str) -> Dict:
#         """Update MongoDB collection"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             # Parse SET clause
#             parts = set_clause.split('=')
#             field = parts[0].strip()
#             value = parts[1].strip().strip('"\'')
            
#             # Try numeric conversion
#             try:
#                 value = float(value) if '.' in value else int(value)
#             except:
#                 pass
            
#             mongo_filter = self._parse_condition(condition)
#             result = self.mongo_db[collection].update_many(
#                 mongo_filter,
#                 {"$set": {field: value}}
#             )
            
#             return {
#                 "status": "success",
#                 "backend": "MongoDB",
#                 "updated": result.modified_count
#             }
#         except PyMongoError as e:
#             return {"error": f"MongoDB update failed: {str(e)}"}
    
#     def _remove_data(self, query: str) -> Dict:
#         """Delete data from table or collection"""
#         try:
#             match = re.search(r'REMOVE FROM (\w+) WHERE\s+(.*)', 
#                             query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax. Use: REMOVE FROM target WHERE condition"}
            
#             target = match.group(1)
#             condition = match.group(2)
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 return self._remove_from_mysql(target, condition)
#             else:
#                 return self._remove_from_mongo(target, condition)
                
#         except Exception as e:
#             return {"error": f"Delete failed: {str(e)}"}
    
#     def _remove_from_mysql(self, table: str, condition: str) -> Dict:
#         """Delete from MySQL"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             delete_sql = f"DELETE FROM {table} WHERE {condition}"
#             self.mysql_cursor.execute(delete_sql)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "backend": "MySQL",
#                 "deleted": self.mysql_cursor.rowcount
#             }
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": f"MySQL delete failed: {str(e)}"}
    
#     def _remove_from_mongo(self, collection: str, condition: str) -> Dict:
#         """Delete from MongoDB"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             mongo_filter = self._parse_condition(condition)
#             result = self.mongo_db[collection].delete_many(mongo_filter)
            
#             return {
#                 "status": "success",
#                 "backend": "MongoDB",
#                 "deleted": result.deleted_count
#             }
#         except PyMongoError as e:
#             return {"error": f"MongoDB delete failed: {str(e)}"}
    
#     def _show_tables(self) -> Dict:
#         """List all MySQL tables"""
#         tables = [name for name, info in self.schema_registry.items() 
#                  if info.get('backend') == 'mysql']
        
#         return {
#             "status": "success",
#             "backend": "MySQL",
#             "tables": tables,
#             "count": len(tables)
#         }
    
#     def _show_collections(self) -> Dict:
#         """List all MongoDB collections"""
#         collections = [name for name, info in self.schema_registry.items() 
#                       if info.get('backend') == 'mongodb']
        
#         return {
#             "status": "success",
#             "backend": "MongoDB",
#             "collections": collections,
#             "count": len(collections)
#         }
    
#     def _drop(self, query: str) -> Dict:
#         """Drop table or collection"""
#         try:
#             match = re.search(r'DROP (\w+)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax. Use: DROP name"}
            
#             target = match.group(1)
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 self.mysql_cursor.execute(f"DROP TABLE {target}")
#                 self.mysql_conn.commit()
#             else:
#                 self.mongo_db[target].drop()
            
#             del self.schema_registry[target]
            
#             return {
#                 "status": "success",
#                 "message": f"Dropped '{target}' from {backend}"
#             }
            
#         except Exception as e:
#             return {"error": f"Drop failed: {str(e)}"}
    
#     def _parse_condition(self, condition: str) -> Dict:
#         """Parse WHERE condition to MongoDB filter"""
#         if not condition:
#             return {}
        
#         operators = {
#             '>=': '$gte',
#             '<=': '$lte',
#             '>': '$gt',
#             '<': '$lt',
#             '!=': '$ne',
#             '=': '$eq'
#         }
        
#         for op, mongo_op in operators.items():
#             if op in condition:
#                 parts = condition.split(op)
#                 field = parts[0].strip()
#                 value = parts[1].strip().strip('"\'')
                
#                 # Try numeric conversion
#                 try:
#                     value = float(value) if '.' in value else int(value)
#                 except:
#                     pass
                
#                 if mongo_op == '$eq':
#                     return {field: value}
#                 else:
#                     return {field: {mongo_op: value}}
        
#         return {}
    
#     def close(self):
#         """Close all database connections"""
#         if self.mysql_cursor:
#             self.mysql_cursor.close()
#         if self.mysql_conn:
#             self.mysql_conn.close()
#         if self.mongo_client:
#             self.mongo_client.close()
        
#         if self.verbose:
#             print("✓ Database connections closed")
# """
# DNACryptDB Core Engine
# Handles MySQL and MongoDB operations with custom query language
# """

# import mysql.connector
# from mysql.connector import Error
# from pymongo import MongoClient
# from pymongo.errors import PyMongoError
# import json
# import re
# from typing import Dict, Any, List
# from datetime import datetime
# import os
# import uuid

# class DNACryptDB:
#     """Core DNACryptDB Engine"""
    
#     def __init__(self, config_file: str = "dnacdb.config.json", verbose: bool = True):
#         """Initialize DNACryptDB with configuration file"""
#         self.mysql_conn = None
#         self.mysql_cursor = None
#         self.mongo_client = None
#         self.mongo_db = None
#         self.schema_registry = {}
#         self.verbose = verbose
        
#         if os.path.exists(config_file):
#             self._load_config(config_file)
#         else:
#             raise FileNotFoundError(
#                 f"Config file not found: {config_file}\n"
#                 f"Run 'dnacryptdb init' to create one."
#             )
    
#     def _load_config(self, config_file: str):
#         """Load database configuration from JSON file"""
#         with open(config_file, 'r') as f:
#             config = json.load(f)
        
#         mysql_config = config.get('mysql', {})
#         mongo_config = config.get('mongodb', {})
        
#         # Connect to MySQL
#         try:
#             temp_conn = mysql.connector.connect(
#                 host=mysql_config['host'],
#                 user=mysql_config['user'],
#                 password=mysql_config['password']
#             )
#             temp_cursor = temp_conn.cursor()
#             temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_config['database']}")
#             temp_cursor.close()
#             temp_conn.close()
            
#             self.mysql_conn = mysql.connector.connect(**mysql_config)
#             self.mysql_cursor = self.mysql_conn.cursor(dictionary=True)
            
#             if self.verbose:
#                 print(f"✓ MySQL connected: {mysql_config['database']}")
#         except Error as e:
#             if self.verbose:
#                 print(f"⚠ MySQL connection failed: {e}")
        
#         # Connect to MongoDB
#         try:
#             self.mongo_client = MongoClient(
#                 mongo_config['uri'], 
#                 serverSelectionTimeoutMS=5000
#             )
#             self.mongo_client.admin.command('ping')
#             self.mongo_db = self.mongo_client[mongo_config['database']]
            
#             if self.verbose:
#                 print(f"✓ MongoDB connected: {mongo_config['database']}")
#         except Exception as e:
#             if self.verbose:
#                 print(f"⚠ MongoDB connection failed: {e}")
    
#     def execute(self, query: str) -> Dict[str, Any]:
#         """Execute single DNACryptDB query"""
#         query = query.strip()
        
#         if not query or query.startswith('#') or query.startswith('--'):
#             return {"status": "comment"}
        
#         try:
#             # DNACrypt-specific syntax
#             if query.upper().startswith('CREATE TABLE') and 'FOR ROLE' in query.upper():
#                 return self._create_table_for_role(query)
#             elif query.upper().startswith('CREATE COLLECTION') and 'FOR ROLE' in query.upper():
#                 return self._create_collection_for_role(query)
#             elif query.upper().startswith('SEND MESSAGE'):
#                 return self._send_message(query)
#             elif query.upper().startswith('ADD ALGORITHM'):
#                 return self._add_algorithm(query)
#             elif query.upper().startswith('ADD KEY'):
#                 return self._add_key(query)
#             elif query.upper().startswith('ADD HASH'):
#                 return self._add_hash(query)
#             elif query.upper().startswith('STORE SEQUENCE'):
#                 return self._store_sequence(query)
#             elif query.upper().startswith('GET MESSAGE'):
#                 return self._get_message(query)
#             elif query.upper().startswith('GET SEQUENCE'):
#                 return self._get_sequence(query)
#             elif query.upper().startswith('LINK DATA'):
#                 return self._link_data(query)
#             elif query.upper().startswith('JOIN'):
#                 return self._polyglot_join(query)
#             elif query.upper().startswith('LIST MESSAGES'):
#                 return self._list_messages(query)
#             # Legacy syntax
#             elif query.upper().startswith('MAKE TABLE'):
#                 return self._make_table(query)
#             elif query.upper().startswith('MAKE COLLECTION'):
#                 return self._make_collection(query)
#             elif query.upper().startswith('PUT INTO'):
#                 return self._put_data(query)
#             elif query.upper().startswith('FETCH FROM'):
#                 return self._fetch_data(query)
#             elif query.upper().startswith('CHANGE IN'):
#                 return self._change_data(query)
#             elif query.upper().startswith('REMOVE FROM'):
#                 return self._remove_data(query)
#             elif query.upper().startswith('SHOW TABLES'):
#                 return self._show_tables()
#             elif query.upper().startswith('SHOW COLLECTIONS'):
#                 return self._show_collections()
#             elif query.upper().startswith('DROP'):
#                 return self._drop(query)
#             else:
#                 return {"error": "Unknown command"}
#         except Exception as e:
#             return {"error": str(e)}
    
#     def execute_file(self, filepath: str) -> List[Dict]:
#         """Execute all queries in a .dnacdb file"""
#         if not os.path.exists(filepath):
#             raise FileNotFoundError(f"File not found: {filepath}")
        
#         with open(filepath, 'r') as f:
#             lines = f.readlines()
        
#         queries = []
#         current_query = []
        
#         for line in lines:
#             line = line.strip()
#             if not line or line.startswith('#') or line.startswith('--'):
#                 continue
#             current_query.append(line)
#             if line.endswith(';'):
#                 full_query = ' '.join(current_query).rstrip(';')
#                 queries.append(full_query)
#                 current_query = []
        
#         if current_query:
#             full_query = ' '.join(current_query)
#             queries.append(full_query)
        
#         results = []
#         for i, query in enumerate(queries, 1):
#             query = query.strip()
#             if not query:
#                 continue
            
#             if self.verbose:
#                 print(f"\n[Query {i}] {query[:60]}{'...' if len(query) > 60 else ''}")
            
#             result = self.execute(query)
#             results.append(result)
            
#             if self.verbose:
#                 if result.get('status') == 'success':
#                     print(f"  ✓ Success")
#                 elif result.get('error'):
#                     print(f"  ✗ Error: {result['error']}")
        
#         return results
    
#     # ========================================================================
#     # DNACrypt-Specific Methods
#     # ========================================================================
    
#     def _create_table_for_role(self, query: str) -> Dict:
#         """CREATE TABLE messages FOR ROLE admin AGE adult"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'CREATE TABLE (\w+) FOR ROLE (\w+)(?:\s+AGE\s+(\w+))?',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_type = match.group(1).lower()
#             role = match.group(2).lower()
#             age_group = match.group(3).lower() if match.group(3) else None
            
#             templates = {
#                 'messages': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         message_id VARCHAR(36) PRIMARY KEY,
#                         content_text TEXT NOT NULL,
#                         sender VARCHAR(255) NOT NULL,
#                         receiver VARCHAR(255) NOT NULL,
#                         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#                         urgency ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
#                         status ENUM('pending', 'sent', 'delivered', 'read') DEFAULT 'pending',
#                         link_id VARCHAR(36) UNIQUE NOT NULL,
#                         role VARCHAR(50),
#                         age_group VARCHAR(50),
#                         INDEX idx_sender (sender),
#                         INDEX idx_receiver (receiver),
#                         INDEX idx_timestamp (timestamp),
#                         INDEX idx_link (link_id)
#                     )
#                 """,
#                 'algorithms': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         algo_id INT AUTO_INCREMENT PRIMARY KEY,
#                         message_id VARCHAR(36) NOT NULL,
#                         algorithm_name VARCHAR(100) NOT NULL,
#                         algorithm_type ENUM('encryption', 'hashing', 'encoding', 'compression') NOT NULL,
#                         parameters JSON,
#                         execution_order INT,
#                         role VARCHAR(50),
#                         INDEX idx_message (message_id)
#                     )
#                 """,
#                 'keys': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         key_id INT AUTO_INCREMENT PRIMARY KEY,
#                         message_id VARCHAR(36) NOT NULL,
#                         public_key TEXT NOT NULL,
#                         key_type ENUM('RSA', 'ECC', 'lattice', 'DNA_based') NOT NULL,
#                         key_size INT,
#                         role VARCHAR(50),
#                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                         INDEX idx_message (message_id)
#                     )
#                 """,
#                 'hashes': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         hash_id INT AUTO_INCREMENT PRIMARY KEY,
#                         message_id VARCHAR(36) NOT NULL,
#                         hash_value VARCHAR(512) NOT NULL,
#                         hash_algorithm ENUM('SHA256', 'SHA512', 'Blake2', 'DNA_hash') NOT NULL,
#                         salt VARCHAR(255),
#                         role VARCHAR(50),
#                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                         INDEX idx_message (message_id),
#                         INDEX idx_hash (hash_value(255))
#                     )
#                 """
#             }
            
#             if table_type not in templates:
#                 return {"error": f"Invalid table type: {table_type}"}
            
#             if age_group:
#                 table_name = f"{table_type}_{role}_{age_group}"
#             else:
#                 table_name = f"{table_type}_{role}"
            
#             create_sql = templates[table_type].format(name=table_name)
#             self.mysql_cursor.execute(create_sql)
#             self.mysql_conn.commit()
            
#             self.schema_registry[table_name] = {
#                 'backend': 'mysql',
#                 'type': table_type,
#                 'role': role,
#                 'age_group': age_group
#             }
            
#             return {
#                 "status": "success",
#                 "table": table_name,
#                 "backend": "MySQL (ACID, 3NF)"
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _create_collection_for_role(self, query: str) -> Dict:
#         """CREATE COLLECTION sequences FOR ROLE admin"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(
#                 r'CREATE COLLECTION (\w+) FOR ROLE (\w+)',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_type = match.group(1).lower()
#             role = match.group(2).lower()
            
#             coll_name = f"{coll_type}_{role}"
            
#             if coll_name not in self.mongo_db.list_collection_names():
#                 self.mongo_db.create_collection(coll_name)
            
#             self.mongo_db[coll_name].create_index("link_id", unique=True)
#             self.mongo_db[coll_name].create_index("created_at")
            
#             self.schema_registry[coll_name] = {
#                 'backend': 'mongodb',
#                 'type': coll_type,
#                 'role': role
#             }
            
#             return {
#                 "status": "success",
#                 "collection": coll_name,
#                 "backend": "MongoDB (BASE)"
#             }
            
#         except PyMongoError as e:
#             return {"error": str(e)}
    
#     def _send_message(self, query: str) -> Dict:
#         """SEND MESSAGE TO messages_admin_adult {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'SEND MESSAGE TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             message_id = str(uuid.uuid4())
#             link_id = str(uuid.uuid4())
            
#             parts = table_name.split('_')
#             role = parts[1] if len(parts) > 1 else None
#             age_group = parts[2] if len(parts) > 2 else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, content_text, sender, receiver, urgency, link_id, role, age_group)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 message_id,
#                 data['content'],
#                 data['sender'],
#                 data['receiver'],
#                 data.get('urgency', 'medium'),
#                 link_id,
#                 role,
#                 age_group
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "message_id": message_id,
#                 "link_id": link_id
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
#         except json.JSONDecodeError as e:
#             return {"error": f"Invalid JSON: {str(e)}"}
    
#     def _add_algorithm(self, query: str) -> Dict:
#         """ADD ALGORITHM TO algorithms_admin {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'ADD ALGORITHM TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             role = table_name.split('_')[1] if '_' in table_name else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, algorithm_name, algorithm_type, parameters, execution_order, role)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 data['message_id'],
#                 data['algorithm'],
#                 data['type'],
#                 json.dumps(data.get('parameters', {})),
#                 data.get('order', 1),
#                 role
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "algo_id": self.mysql_cursor.lastrowid
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _add_key(self, query: str) -> Dict:
#         """ADD KEY TO keys_admin {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'ADD KEY TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             role = table_name.split('_')[1] if '_' in table_name else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, public_key, key_type, key_size, role)
#                 VALUES (%s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 data['message_id'],
#                 data['public_key'],
#                 data['type'],
#                 data.get('size', 2048),
#                 role
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "key_id": self.mysql_cursor.lastrowid
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _add_hash(self, query: str) -> Dict:
#         """ADD HASH TO hashes_admin {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'ADD HASH TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             role = table_name.split('_')[1] if '_' in table_name else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, hash_value, hash_algorithm, salt, role)
#                 VALUES (%s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 data['message_id'],
#                 data['hash'],
#                 data['algorithm'],
#                 data.get('salt', ''),
#                 role
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "hash_id": self.mysql_cursor.lastrowid
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _store_sequence(self, query: str) -> Dict:
#         """STORE SEQUENCE IN sequences_admin {...}"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(
#                 r'STORE SEQUENCE IN (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             sequence_doc = {
#                 "link_id": data['link_id'],
#                 "original_sequence": data.get('original', ''),
#                 "encrypted_sequence": data.get('encrypted', ''),
#                 "digest_sequence": data.get('digest', ''),
#                 "final_sequence": data.get('final', ''),
#                 "metadata": data.get('metadata', {}),
#                 "role": coll_name.split('_')[1] if '_' in coll_name else None,
#                 "created_at": datetime.utcnow()
#             }
            
#             result = self.mongo_db[coll_name].insert_one(sequence_doc)
            
#             return {
#                 "status": "success",
#                 "sequence_id": str(result.inserted_id),
#                 "link_id": data['link_id']
#             }
            
#         except PyMongoError as e:
#             return {"error": str(e)}
    
#     def _get_message(self, query: str) -> Dict:
#         """GET MESSAGE FROM messages_admin_adult WHERE message_id = "..."""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'GET MESSAGE FROM (\w+) WHERE\s+(\w+)\s*=\s*["\']?(.*?)["\']?$',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             field = match.group(2)
#             value = match.group(3).strip('"\'')
            
#             select_query = f"SELECT * FROM {table_name} WHERE {field} = %s"
#             self.mysql_cursor.execute(select_query, (value,))
#             result = self.mysql_cursor.fetchone()
            
#             if not result:
#                 return {"error": "Message not found"}
            
#             if 'timestamp' in result and result['timestamp']:
#                 result['timestamp'] = result['timestamp'].isoformat()
            
#             return {"status": "success", "message": result}
            
#         except Error as e:
#             return {"error": str(e)}
    
#     def _get_sequence(self, query: str) -> Dict:
#         """GET SEQUENCE FROM sequences_admin WHERE link_id = "..."""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(
#                 r'GET SEQUENCE FROM (\w+) WHERE\s+link_id\s*=\s*["\']?(.*?)["\']?$',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_name = match.group(1)
#             link_id = match.group(2).strip('"\'')
            
#             sequence = self.mongo_db[coll_name].find_one({"link_id": link_id})
            
#             if not sequence:
#                 return {"error": "Sequence not found"}
            
#             sequence['_id'] = str(sequence['_id'])
#             if 'created_at' in sequence:
#                 sequence['created_at'] = sequence['created_at'].isoformat()
            
#             return {"status": "success", "sequence": sequence}
            
#         except PyMongoError as e:
#             return {"error": str(e)}
    
#     def _link_data(self, query: str) -> Dict:
#         """LINK DATA WHERE link_id = "uuid"""
#         try:
#             match = re.search(
#                 r'LINK DATA WHERE\s+link_id\s*=\s*["\']?(.*?)["\']?$',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             link_id = match.group(1).strip('"\'')
            
#             result = {
#                 "status": "success",
#                 "link_id": link_id,
#                 "mysql_data": {},
#                 "mongodb_data": {}
#             }
            
#             # Search MySQL tables
#             if self.mysql_cursor:
#                 for table_name, table_info in self.schema_registry.items():
#                     if table_info.get('backend') == 'mysql' and table_info.get('type') == 'messages':
#                         try:
#                             query_sql = f"SELECT * FROM {table_name} WHERE link_id = %s"
#                             self.mysql_cursor.execute(query_sql, (link_id,))
#                             msg = self.mysql_cursor.fetchone()
                            
#                             if msg:
#                                 if 'timestamp' in msg and msg['timestamp']:
#                                     msg['timestamp'] = msg['timestamp'].isoformat()
#                                 result['mysql_data']['message'] = msg
#                                 result['mysql_data']['table'] = table_name
#                                 break
#                         except:
#                             continue
            
#             # Search MongoDB collections
#             if self.mongo_db is not None:
#                 for coll_name, coll_info in self.schema_registry.items():
#                     if coll_info.get('backend') == 'mongodb':
#                         try:
#                             seq = self.mongo_db[coll_name].find_one({"link_id": link_id})
#                             if seq:
#                                 seq['_id'] = str(seq['_id'])
#                                 if 'created_at' in seq:
#                                     seq['created_at'] = seq['created_at'].isoformat()
#                                 result['mongodb_data']['sequence'] = seq
#                                 result['mongodb_data']['collection'] = coll_name
#                                 break
#                         except:
#                             continue
            
#             return result
            
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _polyglot_join(self, query: str) -> Dict:
#         """JOIN messages_admin_adult WITH sequences_admin ON link_id WHERE urgency = "high"""
#         try:
#             match = re.search(
#                 r'JOIN (\w+) WITH (\w+) ON (\w+)(?:\s+WHERE\s+(.*))?',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid JOIN syntax"}
            
#             mysql_table = match.group(1)
#             mongo_collection = match.group(2)
#             join_field = match.group(3)
#             where_clause = match.group(4)
            
#             if where_clause:
#                 mysql_query = f"SELECT * FROM {mysql_table} WHERE {where_clause}"
#             else:
#                 mysql_query = f"SELECT * FROM {mysql_table}"
            
#             self.mysql_cursor.execute(mysql_query)
#             mysql_results = self.mysql_cursor.fetchall()
            
#             joined_results = []
            
#             for mysql_row in mysql_results:
#                 if join_field not in mysql_row:
#                     continue
                
#                 link_value = mysql_row[join_field]
#                 mongo_doc = self.mongo_db[mongo_collection].find_one({join_field: link_value})
                
#                 if mongo_doc:
#                     mongo_doc['_id'] = str(mongo_doc['_id'])
#                     if 'created_at' in mongo_doc:
#                         mongo_doc['created_at'] = mongo_doc['created_at'].isoformat()
                    
#                     joined_row = {
#                         'mysql_data': dict(mysql_row),
#                         'mongodb_data': mongo_doc,
#                         'join_field': join_field,
#                         'join_value': link_value
#                     }
                    
#                     if 'timestamp' in joined_row['mysql_data'] and joined_row['mysql_data']['timestamp']:
#                         joined_row['mysql_data']['timestamp'] = joined_row['mysql_data']['timestamp'].isoformat()
                    
#                     joined_results.append(joined_row)
            
#             return {
#                 "status": "success",
#                 "join_type": "MySQL ⟕ MongoDB",
#                 "mysql_table": mysql_table,
#                 "mongodb_collection": mongo_collection,
#                 "join_field": join_field,
#                 "count": len(joined_results),
#                 "results": joined_results
#             }
            
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _list_messages(self, query: str) -> Dict:
#         """LIST MESSAGES FROM messages_admin_adult WHERE urgency = "high"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'LIST MESSAGES FROM (\w+)(?:\s+WHERE\s+(.*))?',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             where_clause = match.group(2)
            
#             if where_clause:
#                 select_query = f"SELECT * FROM {table_name} WHERE {where_clause} ORDER BY timestamp DESC"
#             else:
#                 select_query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC"
            
#             self.mysql_cursor.execute(select_query)
#             results = self.mysql_cursor.fetchall()
            
#             for result in results:
#                 if 'timestamp' in result and result['timestamp']:
#                     result['timestamp'] = result['timestamp'].isoformat()
            
#             return {
#                 "status": "success",
#                 "count": len(results),
#                 "messages": results
#             }
            
#         except Error as e:
#             return {"error": str(e)}
    
#     # ========================================================================
#     # Legacy Methods (Backward Compatibility)
#     # ========================================================================
    
#     def _make_table(self, query: str) -> Dict:
#         """MAKE TABLE users WITH (name:text, age:int)"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(r'MAKE TABLE (\w+) WITH\s*\((.*?)\)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             fields_str = match.group(2)
            
#             type_mapping = {
#                 'int': 'INT', 'integer': 'INT', 'text': 'VARCHAR(255)',
#                 'float': 'FLOAT', 'date': 'DATE', 'datetime': 'DATETIME',
#                 'bool': 'BOOLEAN'
#             }
            
#             fields = ['id INT AUTO_INCREMENT PRIMARY KEY']
#             field_schema = {}
            
#             for field in fields_str.split(','):
#                 field = field.strip()
#                 if ':' in field:
#                     name, ftype = field.split(':')
#                     name, ftype = name.strip(), ftype.strip().lower()
#                     if name.lower() != 'id':
#                         sql_type = type_mapping.get(ftype, 'VARCHAR(255)')
#                         fields.append(f"{name} {sql_type}")
#                         field_schema[name] = ftype
            
#             create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(fields)})"
#             self.mysql_cursor.execute(create_sql)
#             self.mysql_conn.commit()
            
#             self.schema_registry[table_name] = {'backend': 'mysql', 'fields': field_schema}
#             return {"status": "success", "table": table_name}
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _make_collection(self, query: str) -> Dict:
#         """MAKE COLLECTION logs"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(r'MAKE COLLECTION (\w+)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_name = match.group(1)
#             if coll_name not in self.mongo_db.list_collection_names():
#                 self.mongo_db.create_collection(coll_name)
            
#             self.schema_registry[coll_name] = {'backend': 'mongodb'}
#             return {"status": "success", "collection": coll_name}
            
#         except PyMongoError as e:
#             return {"error": str(e)}
    
#     def _put_data(self, query: str) -> Dict:
#         """PUT INTO target DATA {...}"""
#         try:
#             match = re.search(r'PUT INTO (\w+) DATA\s*({.*?})$', query, re.IGNORECASE | re.DOTALL)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 fields = list(data.keys())
#                 placeholders = ', '.join(['%s' for _ in fields])
#                 values = [data[f] for f in fields]
#                 insert_sql = f"INSERT INTO {target} ({', '.join(fields)}) VALUES ({placeholders})"
#                 self.mysql_cursor.execute(insert_sql, values)
#                 self.mysql_conn.commit()
#                 return {"status": "success", "inserted_id": self.mysql_cursor.lastrowid}
#             else:
#                 data['created_at'] = datetime.utcnow()
#                 result = self.mongo_db[target].insert_one(data)
#                 return {"status": "success", "inserted_id": str(result.inserted_id)}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _fetch_data(self, query: str) -> Dict:
#         """FETCH FROM source WHERE/ALL"""
#         try:
#             match = re.search(r'FETCH FROM (\w+)\s+(?:WHERE\s+(.*)|ALL)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             source = match.group(1)
#             condition = match.group(2)
            
#             if source not in self.schema_registry:
#                 return {"error": f"Source '{source}' does not exist"}
            
#             backend = self.schema_registry[source]['backend']
            
#             if backend == 'mysql':
#                 if condition:
#                     query_sql = f"SELECT * FROM {source} WHERE {condition}"
#                 else:
#                     query_sql = f"SELECT * FROM {source}"
#                 self.mysql_cursor.execute(query_sql)
#                 results = self.mysql_cursor.fetchall()
#                 return {"status": "success", "count": len(results), "data": results}
#             else:
#                 mongo_filter = self._parse_condition(condition) if condition else {}
#                 results = list(self.mongo_db[source].find(mongo_filter))
#                 for r in results:
#                     r['_id'] = str(r['_id'])
#                     if 'created_at' in r:
#                         r['created_at'] = r['created_at'].isoformat()
#                 return {"status": "success", "count": len(results), "data": results}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _change_data(self, query: str) -> Dict:
#         """CHANGE IN target SET field=value WHERE condition"""
#         try:
#             match = re.search(r'CHANGE IN (\w+) SET\s+(.*?)\s+WHERE\s+(.*)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target, set_clause, condition = match.groups()
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 update_sql = f"UPDATE {target} SET {set_clause} WHERE {condition}"
#                 self.mysql_cursor.execute(update_sql)
#                 self.mysql_conn.commit()
#                 return {"status": "success", "updated": self.mysql_cursor.rowcount}
#             else:
#                 parts = set_clause.split('=')
#                 field = parts[0].strip()
#                 value = parts[1].strip().strip('"\'')
#                 try:
#                     value = float(value) if '.' in value else int(value)
#                 except:
#                     pass
#                 mongo_filter = self._parse_condition(condition)
#                 result = self.mongo_db[target].update_many(mongo_filter, {"$set": {field: value}})
#                 return {"status": "success", "updated": result.modified_count}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _remove_data(self, query: str) -> Dict:
#         """REMOVE FROM target WHERE condition"""
#         try:
#             match = re.search(r'REMOVE FROM (\w+) WHERE\s+(.*)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target, condition = match.groups()
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 delete_sql = f"DELETE FROM {target} WHERE {condition}"
#                 self.mysql_cursor.execute(delete_sql)
#                 self.mysql_conn.commit()
#                 return {"status": "success", "deleted": self.mysql_cursor.rowcount}
#             else:
#                 mongo_filter = self._parse_condition(condition)
#                 result = self.mongo_db[target].delete_many(mongo_filter)
#                 return {"status": "success", "deleted": result.deleted_count}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _show_tables(self) -> Dict:
#         """Show all tables"""
#         tables = [name for name, info in self.schema_registry.items() 
#                  if info.get('backend') == 'mysql']
#         return {"status": "success", "tables": tables, "count": len(tables)}
    
#     def _show_collections(self) -> Dict:
#         """Show all collections"""
#         collections = [name for name, info in self.schema_registry.items() 
#                       if info.get('backend') == 'mongodb']
#         return {"status": "success", "collections": collections, "count": len(collections)}
    
#     def _drop(self, query: str) -> Dict:
#         """DROP target"""
#         try:
#             match = re.search(r'DROP (\w+)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target = match.group(1)
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 self.mysql_cursor.execute(f"DROP TABLE {target}")
#                 self.mysql_conn.commit()
#             else:
#                 self.mongo_db[target].drop()
            
#             del self.schema_registry[target]
#             return {"status": "success"}
            
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _parse_condition(self, condition: str) -> Dict:
#         """Parse condition to MongoDB filter"""
#         if not condition:
#             return {}
        
#         operators = {
#             '>=': '$gte', '<=': '$lte', '>': '$gt',
#             '<': '$lt', '!=': '$ne', '=': '$eq'
#         }
        
#         for op, mongo_op in operators.items():
#             if op in condition:
#                 parts = condition.split(op)
#                 field = parts[0].strip()
#                 value = parts[1].strip().strip('"\'')
#                 try:
#                     value = float(value) if '.' in value else int(value)
#                 except:
#                     pass
#                 if mongo_op == '$eq':
#                     return {field: value}
#                 else:
#                     return {field: {mongo_op: value}}
#         return {}
    
#     def close(self):
#         """Close all database connections"""
#         if self.mysql_cursor:
#             self.mysql_cursor.close()
#         if self.mysql_conn:
#             self.mysql_conn.close()
#         if self.mongo_client:
#             self.mongo_client.close()
        
#         if self.verbose:
#             print("✓ Database connections closed")

# """
# DNACryptDB Core Engine
# Handles MySQL and MongoDB operations with custom query language
# """

# import mysql.connector
# from mysql.connector import Error
# from pymongo import MongoClient
# from pymongo.errors import PyMongoError
# import json
# import re
# from typing import Dict, Any, List
# from datetime import datetime
# import os
# import uuid

# class DNACryptDB:
#     """Core DNACryptDB Engine"""
    
#     def __init__(self, config_file: str = "dnacdb.config.json", verbose: bool = True):
#         """Initialize DNACryptDB with configuration file"""
#         self.mysql_conn = None
#         self.mysql_cursor = None
#         self.mongo_client = None
#         self.mongo_db = None
#         self.schema_registry = {}
#         self.verbose = verbose
        
#         if os.path.exists(config_file):
#             self._load_config(config_file)
#         else:
#             raise FileNotFoundError(
#                 f"Config file not found: {config_file}\n"
#                 f"Run 'dnacryptdb init' to create one."
#             )
    
#     def _load_config(self, config_file: str):
#         """Load database configuration from JSON file"""
#         with open(config_file, 'r') as f:
#             config = json.load(f)
        
#         mysql_config = config.get('mysql', {})
#         mongo_config = config.get('mongodb', {})
        
#         # Connect to MySQL
#         try:
#             temp_conn = mysql.connector.connect(
#                 host=mysql_config['host'],
#                 user=mysql_config['user'],
#                 password=mysql_config['password']
#             )
#             temp_cursor = temp_conn.cursor()
#             temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_config['database']}")
#             temp_cursor.close()
#             temp_conn.close()
            
#             self.mysql_conn = mysql.connector.connect(**mysql_config)
#             self.mysql_cursor = self.mysql_conn.cursor(dictionary=True)
            
#             if self.verbose:
#                 print(f"✓ MySQL connected: {mysql_config['database']}")
#         except Error as e:
#             if self.verbose:
#                 print(f"⚠ MySQL connection failed: {e}")
        
#         # Connect to MongoDB
#         try:
#             self.mongo_client = MongoClient(
#                 mongo_config['uri'], 
#                 serverSelectionTimeoutMS=5000
#             )
#             self.mongo_client.admin.command('ping')
#             self.mongo_db = self.mongo_client[mongo_config['database']]
            
#             if self.verbose:
#                 print(f"✓ MongoDB connected: {mongo_config['database']}")
#         except Exception as e:
#             if self.verbose:
#                 print(f"⚠ MongoDB connection failed: {e}")
    
#     def execute(self, query: str) -> Dict[str, Any]:
#         """Execute single DNACryptDB query"""
#         query = query.strip()
        
#         if not query or query.startswith('#') or query.startswith('--'):
#             return {"status": "comment"}
        
#         try:
#             # DNACrypt-specific syntax
#             if query.upper().startswith('CREATE TABLE') and 'FOR ROLE' in query.upper():
#                 return self._create_table_for_role(query)
#             elif query.upper().startswith('CREATE COLLECTION') and 'FOR ROLE' in query.upper():
#                 return self._create_collection_for_role(query)
#             elif query.upper().startswith('SEND MESSAGE'):
#                 return self._send_message(query)
#             elif query.upper().startswith('ADD ALGORITHM'):
#                 return self._add_algorithm(query)
#             elif query.upper().startswith('ADD KEY'):
#                 return self._add_key(query)
#             elif query.upper().startswith('ADD HASH'):
#                 return self._add_hash(query)
#             elif query.upper().startswith('STORE SEQUENCE'):
#                 return self._store_sequence(query)
#             elif query.upper().startswith('GET MESSAGE'):
#                 return self._get_message(query)
#             elif query.upper().startswith('GET SEQUENCE'):
#                 return self._get_sequence(query)
#             elif query.upper().startswith('LINK DATA'):
#                 return self._link_data(query)
#             elif query.upper().startswith('JOIN'):
#                 return self._polyglot_join(query)
#             elif query.upper().startswith('LIST MESSAGES'):
#                 return self._list_messages(query)
#             # Legacy syntax
#             elif query.upper().startswith('MAKE TABLE'):
#                 return self._make_table(query)
#             elif query.upper().startswith('MAKE COLLECTION'):
#                 return self._make_collection(query)
#             elif query.upper().startswith('PUT INTO'):
#                 return self._put_data(query)
#             elif query.upper().startswith('FETCH FROM'):
#                 return self._fetch_data(query)
#             elif query.upper().startswith('CHANGE IN'):
#                 return self._change_data(query)
#             elif query.upper().startswith('REMOVE FROM'):
#                 return self._remove_data(query)
#             elif query.upper().startswith('SHOW TABLES'):
#                 return self._show_tables()
#             elif query.upper().startswith('SHOW COLLECTIONS'):
#                 return self._show_collections()
#             elif query.upper().startswith('DROP'):
#                 return self._drop(query)
#             else:
#                 return {"error": "Unknown command"}
#         except Exception as e:
#             return {"error": str(e)}
    
#     def execute_file(self, filepath: str) -> List[Dict]:
#         """
#         Execute all queries in a .dnacdb file
#         Supports variable storage: $var = query result
#         """
#         if not os.path.exists(filepath):
#             raise FileNotFoundError(f"File not found: {filepath}")
        
#         with open(filepath, 'r') as f:
#             lines = f.readlines()
        
#         queries = []
#         current_query = []
#         variables = {}  # Store variables from query results
        
#         for line in lines:
#             line = line.strip()
#             if not line or line.startswith('#') or line.startswith('--'):
#                 continue
#             current_query.append(line)
#             if line.endswith(';'):
#                 full_query = ' '.join(current_query).rstrip(';')
#                 queries.append(full_query)
#                 current_query = []
        
#         if current_query:
#             full_query = ' '.join(current_query)
#             queries.append(full_query)
        
#         results = []
#         for i, query in enumerate(queries, 1):
#             query = query.strip()
#             if not query:
#                 continue
            
#             # Check for variable assignment: $var = QUERY
#             var_match = re.match(r'\$(\w+)\s*=\s*(.+)', query)
#             if var_match:
#                 var_name = var_match.group(1)
#                 actual_query = var_match.group(2)
                
#                 if self.verbose:
#                     print(f"\n[Query {i}] ${var_name} = {actual_query[:50]}...")
                
#                 result = self.execute(actual_query)
#                 results.append(result)
                
#                 # Store result in variables
#                 if result.get('status') == 'success':
#                     variables[var_name] = result
#                     if self.verbose:
#                         print(f"  ✓ Success - stored in ${var_name}")
#                 elif result.get('error'):
#                     if self.verbose:
#                         print(f"  ✗ Error: {result['error']}")
#                 continue
            
#             # Replace variables in query: ${var.field}
#             original_query = query
#             for var_name, var_value in variables.items():
#                 # Replace ${var.link_id}, ${var.message_id}, etc.
#                 for field in ['link_id', 'message_id', 'sequence_id', 'inserted_id']:
#                     placeholder = f"${{{var_name}.{field}}}"
#                     if placeholder in query:
#                         if field in var_value:
#                             query = query.replace(placeholder, str(var_value[field]))
            
#             if self.verbose:
#                 if query != original_query:
#                     print(f"\n[Query {i}] {original_query[:60]}...")
#                     print(f"         → {query[:60]}...")
#                 else:
#                     print(f"\n[Query {i}] {query[:60]}{'...' if len(query) > 60 else ''}")
            
#             result = self.execute(query)
#             results.append(result)
            
#             if self.verbose:
#                 if result.get('status') == 'success':
#                     print(f"  ✓ Success")
#                 elif result.get('error'):
#                     print(f"  ✗ Error: {result['error']}")
        
#         return results
    
#     # ========================================================================
#     # DNACrypt-Specific Methods
#     # ========================================================================
    
#     def _create_table_for_role(self, query: str) -> Dict:
#         """CREATE TABLE messages FOR ROLE admin AGE adult"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'CREATE TABLE (\w+) FOR ROLE (\w+)(?:\s+AGE\s+(\w+))?',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_type = match.group(1).lower()
#             role = match.group(2).lower()
#             age_group = match.group(3).lower() if match.group(3) else None
            
#             templates = {
#                 'messages': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         message_id VARCHAR(36) PRIMARY KEY,
#                         content_text TEXT NOT NULL,
#                         sender VARCHAR(255) NOT NULL,
#                         receiver VARCHAR(255) NOT NULL,
#                         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#                         urgency ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
#                         status ENUM('pending', 'sent', 'delivered', 'read') DEFAULT 'pending',
#                         link_id VARCHAR(36) UNIQUE NOT NULL,
#                         role VARCHAR(50),
#                         age_group VARCHAR(50),
#                         INDEX idx_sender (sender),
#                         INDEX idx_receiver (receiver),
#                         INDEX idx_timestamp (timestamp),
#                         INDEX idx_link (link_id)
#                     )
#                 """,
#                 'algorithms': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         algo_id INT AUTO_INCREMENT PRIMARY KEY,
#                         message_id VARCHAR(36) NOT NULL,
#                         algorithm_name VARCHAR(100) NOT NULL,
#                         algorithm_type ENUM('encryption', 'hashing', 'encoding', 'compression') NOT NULL,
#                         parameters JSON,
#                         execution_order INT,
#                         role VARCHAR(50),
#                         INDEX idx_message (message_id)
#                     )
#                 """,
#                 'keys': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         key_id INT AUTO_INCREMENT PRIMARY KEY,
#                         message_id VARCHAR(36) NOT NULL,
#                         public_key TEXT NOT NULL,
#                         key_type ENUM('RSA', 'ECC', 'lattice', 'DNA_based') NOT NULL,
#                         key_size INT,
#                         role VARCHAR(50),
#                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                         INDEX idx_message (message_id)
#                     )
#                 """,
#                 'hashes': """
#                     CREATE TABLE IF NOT EXISTS {name} (
#                         hash_id INT AUTO_INCREMENT PRIMARY KEY,
#                         message_id VARCHAR(36) NOT NULL,
#                         hash_value VARCHAR(512) NOT NULL,
#                         hash_algorithm ENUM('SHA256', 'SHA512', 'Blake2', 'DNA_hash') NOT NULL,
#                         salt VARCHAR(255),
#                         role VARCHAR(50),
#                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                         INDEX idx_message (message_id),
#                         INDEX idx_hash (hash_value(255))
#                     )
#                 """
#             }
            
#             if table_type not in templates:
#                 return {"error": f"Invalid table type: {table_type}"}
            
#             if age_group:
#                 table_name = f"{table_type}_{role}_{age_group}"
#             else:
#                 table_name = f"{table_type}_{role}"
            
#             create_sql = templates[table_type].format(name=table_name)
#             self.mysql_cursor.execute(create_sql)
#             self.mysql_conn.commit()
            
#             self.schema_registry[table_name] = {
#                 'backend': 'mysql',
#                 'type': table_type,
#                 'role': role,
#                 'age_group': age_group
#             }
            
#             return {
#                 "status": "success",
#                 "table": table_name,
#                 "backend": "MySQL (ACID, 3NF)"
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _create_collection_for_role(self, query: str) -> Dict:
#         """CREATE COLLECTION sequences FOR ROLE admin"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(
#                 r'CREATE COLLECTION (\w+) FOR ROLE (\w+)',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_type = match.group(1).lower()
#             role = match.group(2).lower()
            
#             coll_name = f"{coll_type}_{role}"
            
#             if coll_name not in self.mongo_db.list_collection_names():
#                 self.mongo_db.create_collection(coll_name)
            
#             self.mongo_db[coll_name].create_index("link_id", unique=True)
#             self.mongo_db[coll_name].create_index("created_at")
            
#             self.schema_registry[coll_name] = {
#                 'backend': 'mongodb',
#                 'type': coll_type,
#                 'role': role
#             }
            
#             return {
#                 "status": "success",
#                 "collection": coll_name,
#                 "backend": "MongoDB (BASE)"
#             }
            
#         except PyMongoError as e:
#             return {"error": str(e)}
    
#     def _send_message(self, query: str) -> Dict:
#         """SEND MESSAGE TO messages_admin_adult {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'SEND MESSAGE TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             message_id = str(uuid.uuid4())
#             link_id = str(uuid.uuid4())
            
#             parts = table_name.split('_')
#             role = parts[1] if len(parts) > 1 else None
#             age_group = parts[2] if len(parts) > 2 else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, content_text, sender, receiver, urgency, link_id, role, age_group)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 message_id,
#                 data['content'],
#                 data['sender'],
#                 data['receiver'],
#                 data.get('urgency', 'medium'),
#                 link_id,
#                 role,
#                 age_group
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "message_id": message_id,
#                 "link_id": link_id
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
#         except json.JSONDecodeError as e:
#             return {"error": f"Invalid JSON: {str(e)}"}
    
#     def _add_algorithm(self, query: str) -> Dict:
#         """ADD ALGORITHM TO algorithms_admin {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'ADD ALGORITHM TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             role = table_name.split('_')[1] if '_' in table_name else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, algorithm_name, algorithm_type, parameters, execution_order, role)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 data['message_id'],
#                 data['algorithm'],
#                 data['type'],
#                 json.dumps(data.get('parameters', {})),
#                 data.get('order', 1),
#                 role
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "algo_id": self.mysql_cursor.lastrowid
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _add_key(self, query: str) -> Dict:
#         """ADD KEY TO keys_admin {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'ADD KEY TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             role = table_name.split('_')[1] if '_' in table_name else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, public_key, key_type, key_size, role)
#                 VALUES (%s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 data['message_id'],
#                 data['public_key'],
#                 data['type'],
#                 data.get('size', 2048),
#                 role
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "key_id": self.mysql_cursor.lastrowid
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _add_hash(self, query: str) -> Dict:
#         """ADD HASH TO hashes_admin {...}"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'ADD HASH TO (\w+)\s*({.*?})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             role = table_name.split('_')[1] if '_' in table_name else None
            
#             insert_query = f"""
#                 INSERT INTO {table_name}
#                 (message_id, hash_value, hash_algorithm, salt, role)
#                 VALUES (%s, %s, %s, %s, %s)
#             """
            
#             params = (
#                 data['message_id'],
#                 data['hash'],
#                 data['algorithm'],
#                 data.get('salt', ''),
#                 role
#             )
            
#             self.mysql_cursor.execute(insert_query, params)
#             self.mysql_conn.commit()
            
#             return {
#                 "status": "success",
#                 "hash_id": self.mysql_cursor.lastrowid
#             }
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _store_sequence(self, query: str) -> Dict:
#         """STORE SEQUENCE IN sequences_admin {...}"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(
#                 r'STORE SEQUENCE IN (\w+)\s*({.*})',
#                 query, re.IGNORECASE | re.DOTALL
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_name = match.group(1)
#             data_str = match.group(2)
            
#             # Better JSON parsing - handle nested objects
#             try:
#                 # Try parsing as-is first
#                 data_str_clean = data_str.replace("'", '"')
#                 data = json.loads(data_str_clean)
#             except json.JSONDecodeError:
#                 # If fails, try manual parsing for simple nested case
#                 # This handles: {"metadata": {...}}
#                 try:
#                     import ast
#                     data = ast.literal_eval(data_str)
#                 except:
#                     return {"error": "Invalid JSON format. Keep metadata on single line without nested newlines."}
            
#             # Build sequence document with explicit metadata handling
#             metadata = data.get('metadata', {})
#             if isinstance(metadata, str):
#                 # If metadata came as string, parse it
#                 try:
#                     metadata = json.loads(metadata)
#                 except:
#                     metadata = {}
            
#             sequence_doc = {
#                 "link_id": data['link_id'],
#                 "original_sequence": data.get('original', ''),
#                 "encrypted_sequence": data.get('encrypted', ''),
#                 "digest_sequence": data.get('digest', ''),
#                 "final_sequence": data.get('final', ''),
#                 "metadata": metadata,
#                 "role": coll_name.split('_')[1] if '_' in coll_name else None,
#                 "created_at": datetime.utcnow()
#             }
            
#             result = self.mongo_db[coll_name].insert_one(sequence_doc)
            
#             return {
#                 "status": "success",
#                 "sequence_id": str(result.inserted_id),
#                 "link_id": data['link_id']
#             }
            
#         except PyMongoError as e:
#             return {"error": str(e)}
#         except KeyError as e:
#             return {"error": f"Missing required field: {str(e)}"}
#         except Exception as e:
#             return {"error": f"Store sequence failed: {str(e)}"}

    
#     def _get_message(self, query: str) -> Dict:
#         """GET MESSAGE FROM messages_admin_adult WHERE message_id = "..."""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'GET MESSAGE FROM (\w+) WHERE\s+(\w+)\s*=\s*["\']?(.*?)["\']?$',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             field = match.group(2)
#             value = match.group(3).strip('"\'')
            
#             select_query = f"SELECT * FROM {table_name} WHERE {field} = %s"
#             self.mysql_cursor.execute(select_query, (value,))
#             result = self.mysql_cursor.fetchone()
            
#             if not result:
#                 return {"error": "Message not found"}
            
#             if 'timestamp' in result and result['timestamp']:
#                 result['timestamp'] = result['timestamp'].isoformat()
            
#             return {"status": "success", "message": result}
            
#         except Error as e:
#             return {"error": str(e)}
    
#     def _get_sequence(self, query: str) -> Dict:
#         """GET SEQUENCE FROM sequences_admin WHERE link_id = "..."""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(
#                 r'GET SEQUENCE FROM (\w+) WHERE\s+link_id\s*=\s*["\']?(.*?)["\']?$',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_name = match.group(1)
#             link_id = match.group(2).strip('"\'')
            
#             sequence = self.mongo_db[coll_name].find_one({"link_id": link_id})
            
#             if not sequence:
#                 return {"error": "Sequence not found"}
            
#             sequence['_id'] = str(sequence['_id'])
#             if 'created_at' in sequence:
#                 sequence['created_at'] = sequence['created_at'].isoformat()
            
#             return {"status": "success", "sequence": sequence}
            
#         except PyMongoError as e:
#             return {"error": str(e)}
    
#     def _link_data(self, query: str) -> Dict:
#         """LINK DATA WHERE link_id = "uuid"""
#         try:
#             match = re.search(
#                 r'LINK DATA WHERE\s+link_id\s*=\s*["\']?(.*?)["\']?$',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             link_id = match.group(1).strip('"\'')
            
#             result = {
#                 "status": "success",
#                 "link_id": link_id,
#                 "mysql_data": {},
#                 "mongodb_data": {}
#             }
            
#             # Search MySQL tables
#             if self.mysql_cursor:
#                 for table_name, table_info in self.schema_registry.items():
#                     if table_info.get('backend') == 'mysql' and table_info.get('type') == 'messages':
#                         try:
#                             query_sql = f"SELECT * FROM {table_name} WHERE link_id = %s"
#                             self.mysql_cursor.execute(query_sql, (link_id,))
#                             msg = self.mysql_cursor.fetchone()
                            
#                             if msg:
#                                 if 'timestamp' in msg and msg['timestamp']:
#                                     msg['timestamp'] = msg['timestamp'].isoformat()
#                                 result['mysql_data']['message'] = msg
#                                 result['mysql_data']['table'] = table_name
#                                 break
#                         except:
#                             continue
            
#             # Search MongoDB collections
#             if self.mongo_db is not None:
#                 for coll_name, coll_info in self.schema_registry.items():
#                     if coll_info.get('backend') == 'mongodb':
#                         try:
#                             seq = self.mongo_db[coll_name].find_one({"link_id": link_id})
#                             if seq:
#                                 seq['_id'] = str(seq['_id'])
#                                 if 'created_at' in seq:
#                                     seq['created_at'] = seq['created_at'].isoformat()
#                                 result['mongodb_data']['sequence'] = seq
#                                 result['mongodb_data']['collection'] = coll_name
#                                 break
#                         except:
#                             continue
            
#             return result
            
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _polyglot_join(self, query: str) -> Dict:
#         """JOIN messages_admin_adult WITH sequences_admin ON link_id WHERE urgency = "high"""
#         try:
#             match = re.search(
#                 r'JOIN (\w+) WITH (\w+) ON (\w+)(?:\s+WHERE\s+(.*))?',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid JOIN syntax"}
            
#             mysql_table = match.group(1)
#             mongo_collection = match.group(2)
#             join_field = match.group(3)
#             where_clause = match.group(4)
            
#             if where_clause:
#                 mysql_query = f"SELECT * FROM {mysql_table} WHERE {where_clause}"
#             else:
#                 mysql_query = f"SELECT * FROM {mysql_table}"
            
#             self.mysql_cursor.execute(mysql_query)
#             mysql_results = self.mysql_cursor.fetchall()
            
#             joined_results = []
            
#             for mysql_row in mysql_results:
#                 if join_field not in mysql_row:
#                     continue
                
#                 link_value = mysql_row[join_field]
#                 mongo_doc = self.mongo_db[mongo_collection].find_one({join_field: link_value})
                
#                 if mongo_doc:
#                     mongo_doc['_id'] = str(mongo_doc['_id'])
#                     if 'created_at' in mongo_doc:
#                         mongo_doc['created_at'] = mongo_doc['created_at'].isoformat()
                    
#                     joined_row = {
#                         'mysql_data': dict(mysql_row),
#                         'mongodb_data': mongo_doc,
#                         'join_field': join_field,
#                         'join_value': link_value
#                     }
                    
#                     if 'timestamp' in joined_row['mysql_data'] and joined_row['mysql_data']['timestamp']:
#                         joined_row['mysql_data']['timestamp'] = joined_row['mysql_data']['timestamp'].isoformat()
                    
#                     joined_results.append(joined_row)
            
#             return {
#                 "status": "success",
#                 "join_type": "MySQL ⟕ MongoDB",
#                 "mysql_table": mysql_table,
#                 "mongodb_collection": mongo_collection,
#                 "join_field": join_field,
#                 "count": len(joined_results),
#                 "results": joined_results
#             }
            
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _list_messages(self, query: str) -> Dict:
#         """LIST MESSAGES FROM messages_admin_adult WHERE urgency = "high"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(
#                 r'LIST MESSAGES FROM (\w+)(?:\s+WHERE\s+(.*))?',
#                 query, re.IGNORECASE
#             )
            
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             where_clause = match.group(2)
            
#             if where_clause:
#                 select_query = f"SELECT * FROM {table_name} WHERE {where_clause} ORDER BY timestamp DESC"
#             else:
#                 select_query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC"
            
#             self.mysql_cursor.execute(select_query)
#             results = self.mysql_cursor.fetchall()
            
#             for result in results:
#                 if 'timestamp' in result and result['timestamp']:
#                     result['timestamp'] = result['timestamp'].isoformat()
            
#             return {
#                 "status": "success",
#                 "count": len(results),
#                 "messages": results
#             }
            
#         except Error as e:
#             return {"error": str(e)}
    
#     # ========================================================================
#     # Legacy Methods (Backward Compatibility)
#     # ========================================================================
    
#     def _make_table(self, query: str) -> Dict:
#         """MAKE TABLE users WITH (name:text, age:int)"""
#         if not self.mysql_cursor:
#             return {"error": "MySQL not connected"}
        
#         try:
#             match = re.search(r'MAKE TABLE (\w+) WITH\s*\((.*?)\)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             table_name = match.group(1)
#             fields_str = match.group(2)
            
#             type_mapping = {
#                 'int': 'INT', 'integer': 'INT', 'text': 'VARCHAR(255)',
#                 'float': 'FLOAT', 'date': 'DATE', 'datetime': 'DATETIME',
#                 'bool': 'BOOLEAN'
#             }
            
#             fields = ['id INT AUTO_INCREMENT PRIMARY KEY']
#             field_schema = {}
            
#             for field in fields_str.split(','):
#                 field = field.strip()
#                 if ':' in field:
#                     name, ftype = field.split(':')
#                     name, ftype = name.strip(), ftype.strip().lower()
#                     if name.lower() != 'id':
#                         sql_type = type_mapping.get(ftype, 'VARCHAR(255)')
#                         fields.append(f"{name} {sql_type}")
#                         field_schema[name] = ftype
            
#             create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(fields)})"
#             self.mysql_cursor.execute(create_sql)
#             self.mysql_conn.commit()
            
#             self.schema_registry[table_name] = {'backend': 'mysql', 'fields': field_schema}
#             return {"status": "success", "table": table_name}
            
#         except Error as e:
#             self.mysql_conn.rollback()
#             return {"error": str(e)}
    
#     def _make_collection(self, query: str) -> Dict:
#         """MAKE COLLECTION logs"""
#         if self.mongo_db is None:
#             return {"error": "MongoDB not connected"}
        
#         try:
#             match = re.search(r'MAKE COLLECTION (\w+)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             coll_name = match.group(1)
#             if coll_name not in self.mongo_db.list_collection_names():
#                 self.mongo_db.create_collection(coll_name)
            
#             self.schema_registry[coll_name] = {'backend': 'mongodb'}
#             return {"status": "success", "collection": coll_name}
            
#         except PyMongoError as e:
#             return {"error": str(e)}
    
#     def _put_data(self, query: str) -> Dict:
#         """PUT INTO target DATA {...}"""
#         try:
#             match = re.search(r'PUT INTO (\w+) DATA\s*({.*?})$', query, re.IGNORECASE | re.DOTALL)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target = match.group(1)
#             data_str = match.group(2).replace("'", '"')
#             data = json.loads(data_str)
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 fields = list(data.keys())
#                 placeholders = ', '.join(['%s' for _ in fields])
#                 values = [data[f] for f in fields]
#                 insert_sql = f"INSERT INTO {target} ({', '.join(fields)}) VALUES ({placeholders})"
#                 self.mysql_cursor.execute(insert_sql, values)
#                 self.mysql_conn.commit()
#                 return {"status": "success", "inserted_id": self.mysql_cursor.lastrowid}
#             else:
#                 data['created_at'] = datetime.utcnow()
#                 result = self.mongo_db[target].insert_one(data)
#                 return {"status": "success", "inserted_id": str(result.inserted_id)}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _fetch_data(self, query: str) -> Dict:
#         """FETCH FROM source WHERE/ALL"""
#         try:
#             match = re.search(r'FETCH FROM (\w+)\s+(?:WHERE\s+(.*)|ALL)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             source = match.group(1)
#             condition = match.group(2)
            
#             if source not in self.schema_registry:
#                 return {"error": f"Source '{source}' does not exist"}
            
#             backend = self.schema_registry[source]['backend']
            
#             if backend == 'mysql':
#                 if condition:
#                     query_sql = f"SELECT * FROM {source} WHERE {condition}"
#                 else:
#                     query_sql = f"SELECT * FROM {source}"
#                 self.mysql_cursor.execute(query_sql)
#                 results = self.mysql_cursor.fetchall()
#                 return {"status": "success", "count": len(results), "data": results}
#             else:
#                 mongo_filter = self._parse_condition(condition) if condition else {}
#                 results = list(self.mongo_db[source].find(mongo_filter))
#                 for r in results:
#                     r['_id'] = str(r['_id'])
#                     if 'created_at' in r:
#                         r['created_at'] = r['created_at'].isoformat()
#                 return {"status": "success", "count": len(results), "data": results}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _change_data(self, query: str) -> Dict:
#         """CHANGE IN target SET field=value WHERE condition"""
#         try:
#             match = re.search(r'CHANGE IN (\w+) SET\s+(.*?)\s+WHERE\s+(.*)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target, set_clause, condition = match.groups()
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 update_sql = f"UPDATE {target} SET {set_clause} WHERE {condition}"
#                 self.mysql_cursor.execute(update_sql)
#                 self.mysql_conn.commit()
#                 return {"status": "success", "updated": self.mysql_cursor.rowcount}
#             else:
#                 parts = set_clause.split('=')
#                 field = parts[0].strip()
#                 value = parts[1].strip().strip('"\'')
#                 try:
#                     value = float(value) if '.' in value else int(value)
#                 except:
#                     pass
#                 mongo_filter = self._parse_condition(condition)
#                 result = self.mongo_db[target].update_many(mongo_filter, {"$set": {field: value}})
#                 return {"status": "success", "updated": result.modified_count}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _remove_data(self, query: str) -> Dict:
#         """REMOVE FROM target WHERE condition"""
#         try:
#             match = re.search(r'REMOVE FROM (\w+) WHERE\s+(.*)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target, condition = match.groups()
            
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 delete_sql = f"DELETE FROM {target} WHERE {condition}"
#                 self.mysql_cursor.execute(delete_sql)
#                 self.mysql_conn.commit()
#                 return {"status": "success", "deleted": self.mysql_cursor.rowcount}
#             else:
#                 mongo_filter = self._parse_condition(condition)
#                 result = self.mongo_db[target].delete_many(mongo_filter)
#                 return {"status": "success", "deleted": result.deleted_count}
                
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _show_tables(self) -> Dict:
#         """Show all tables"""
#         tables = [name for name, info in self.schema_registry.items() 
#                  if info.get('backend') == 'mysql']
#         return {"status": "success", "tables": tables, "count": len(tables)}
    
#     def _show_collections(self) -> Dict:
#         """Show all collections"""
#         collections = [name for name, info in self.schema_registry.items() 
#                       if info.get('backend') == 'mongodb']
#         return {"status": "success", "collections": collections, "count": len(collections)}
    
#     def _drop(self, query: str) -> Dict:
#         """DROP target"""
#         try:
#             match = re.search(r'DROP (\w+)', query, re.IGNORECASE)
#             if not match:
#                 return {"error": "Invalid syntax"}
            
#             target = match.group(1)
#             if target not in self.schema_registry:
#                 return {"error": f"Target '{target}' does not exist"}
            
#             backend = self.schema_registry[target]['backend']
            
#             if backend == 'mysql':
#                 self.mysql_cursor.execute(f"DROP TABLE {target}")
#                 self.mysql_conn.commit()
#             else:
#                 self.mongo_db[target].drop()
            
#             del self.schema_registry[target]
#             return {"status": "success"}
            
#         except Exception as e:
#             return {"error": str(e)}
    
#     def _parse_condition(self, condition: str) -> Dict:
#         """Parse condition to MongoDB filter"""
#         if not condition:
#             return {}
        
#         operators = {
#             '>=': '$gte', '<=': '$lte', '>': '$gt',
#             '<': '$lt', '!=': '$ne', '=': '$eq'
#         }
        
#         for op, mongo_op in operators.items():
#             if op in condition:
#                 parts = condition.split(op)
#                 field = parts[0].strip()
#                 value = parts[1].strip().strip('"\'')
#                 try:
#                     value = float(value) if '.' in value else int(value)
#                 except:
#                     pass
#                 if mongo_op == '$eq':
#                     return {field: value}
#                 else:
#                     return {field: {mongo_op: value}}
#         return {}
    
#     def close(self):
#         """Close all database connections"""
#         if self.mysql_cursor:
#             self.mysql_cursor.close()
#         if self.mysql_conn:
#             self.mysql_conn.close()
#         if self.mongo_client:
#             self.mongo_client.close()
        
#         if self.verbose:
#             print("✓ Database connections closed")


"""
DNACryptDB Triglot Core Engine
Handles MySQL, MongoDB, and Neo4j with custom query language
"""

import mysql.connector
from mysql.connector import Error
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
import json
import re
from typing import Dict, Any, List
from datetime import datetime
import os
import uuid

class DNACryptDB:
    """Triglot DNACryptDB Engine - MySQL + MongoDB + Neo4j"""
    
    def __init__(self, config_file: str = "dnacdb.config.json", verbose: bool = True):
        """Initialize DNACryptDB with all three backends"""
        self.mysql_conn = None
        self.mysql_cursor = None
        self.mongo_client = None
        self.mongo_db = None
        self.neo4j_driver = None
        self.schema_registry = {}
        self.verbose = verbose
        
        if os.path.exists(config_file):
            self._load_config(config_file)
        else:
            raise FileNotFoundError(
                f"Config file not found: {config_file}\n"
                f"Run 'dnacryptdb init' to create one."
            )
    
    def _load_config(self, config_file: str):
        """Load database configuration from JSON file"""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        mysql_config = config.get('mysql', {})
        mongo_config = config.get('mongodb', {})
        neo4j_config = config.get('neo4j', {})
        
        # Connect to MySQL
        try:
            temp_conn = mysql.connector.connect(
                host=mysql_config['host'],
                user=mysql_config['user'],
                password=mysql_config['password']
            )
            temp_cursor = temp_conn.cursor()
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_config['database']}")
            temp_cursor.close()
            temp_conn.close()
            
            self.mysql_conn = mysql.connector.connect(**mysql_config)
            self.mysql_cursor = self.mysql_conn.cursor(dictionary=True)
            
            if self.verbose:
                print(f"✓ MySQL connected: {mysql_config['database']}")
        except Error as e:
            if self.verbose:
                print(f"⚠ MySQL connection failed: {e}")
        
        # Connect to MongoDB
        try:
            self.mongo_client = MongoClient(
                mongo_config['uri'], 
                serverSelectionTimeoutMS=5000
            )
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[mongo_config['database']]
            
            if self.verbose:
                print(f"✓ MongoDB connected: {mongo_config['database']}")
        except Exception as e:
            if self.verbose:
                print(f"⚠ MongoDB connection failed: {e}")
        
        # Connect to Neo4j
        try:
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_config['uri'],
                auth=(neo4j_config.get('user', 'neo4j'), 
                      neo4j_config.get('password', 'password'))
            )
            # Test connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            
            if self.verbose:
                print(f"✓ Neo4j connected: {neo4j_config['uri']}")
        except Exception as e:
            if self.verbose:
                print(f"⚠ Neo4j connection failed: {e}")
    
    def execute(self, query: str) -> Dict[str, Any]:
        """Execute single DNACryptDB query"""
        query = query.strip()
        
        if not query or query.startswith('#') or query.startswith('--'):
            return {"status": "comment"}
        
        try:
            # Graph operations (Neo4j)
            if query.upper().startswith('CREATE USER'):
                return self._create_user_node(query)
            elif query.upper().startswith('CREATE MESSAGE NODE'):
                return self._create_message_node(query)
            elif query.upper().startswith('RELATE'):
                return self._create_relationship(query)
            elif query.upper().startswith('FIND PATH'):
                return self._find_path(query)
            elif query.upper().startswith('FIND PATTERN'):
                return self._find_pattern(query)
            elif query.upper().startswith('DETECT ANOMALY'):
                return self._detect_anomaly(query)
            elif query.upper().startswith('TRACK ACCESS'):
                return self._track_access(query)
            elif query.upper().startswith('SHOW GRAPH'):
                return self._show_graph(query)
            # DNACrypt-specific syntax
            elif query.upper().startswith('CREATE TABLE') and 'FOR ROLE' in query.upper():
                return self._create_table_for_role(query)
            elif query.upper().startswith('CREATE COLLECTION') and 'FOR ROLE' in query.upper():
                return self._create_collection_for_role(query)
            elif query.upper().startswith('SEND MESSAGE'):
                return self._send_message(query)
            elif query.upper().startswith('ADD ALGORITHM'):
                return self._add_algorithm(query)
            elif query.upper().startswith('ADD KEY'):
                return self._add_key(query)
            elif query.upper().startswith('ADD HASH'):
                return self._add_hash(query)
            elif query.upper().startswith('STORE SEQUENCE'):
                return self._store_sequence(query)
            elif query.upper().startswith('GET MESSAGE'):
                return self._get_message(query)
            elif query.upper().startswith('GET SEQUENCE'):
                return self._get_sequence(query)
            elif query.upper().startswith('LINK DATA'):
                return self._link_data(query)
            elif query.upper().startswith('JOIN'):
                return self._polyglot_join(query)
            elif query.upper().startswith('LIST MESSAGES'):
                return self._list_messages(query)
            # Legacy syntax
            elif query.upper().startswith('MAKE TABLE'):
                return self._make_table(query)
            elif query.upper().startswith('MAKE COLLECTION'):
                return self._make_collection(query)
            elif query.upper().startswith('PUT INTO'):
                return self._put_data(query)
            elif query.upper().startswith('FETCH FROM'):
                return self._fetch_data(query)
            elif query.upper().startswith('CHANGE IN'):
                return self._change_data(query)
            elif query.upper().startswith('REMOVE FROM'):
                return self._remove_data(query)
            elif query.upper().startswith('SHOW TABLES'):
                return self._show_tables()
            elif query.upper().startswith('SHOW COLLECTIONS'):
                return self._show_collections()
            elif query.upper().startswith('DROP'):
                return self._drop(query)
            else:
                return {"error": "Unknown command"}
        except Exception as e:
            return {"error": str(e)}
    
    def execute_file(self, filepath: str) -> List[Dict]:
        """Execute all queries in a .dnacdb file with variable support"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        queries = []
        current_query = []
        variables = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('--'):
                continue
            current_query.append(line)
            if line.endswith(';'):
                full_query = ' '.join(current_query).rstrip(';')
                queries.append(full_query)
                current_query = []
        
        if current_query:
            full_query = ' '.join(current_query)
            queries.append(full_query)
        
        results = []
        for i, query in enumerate(queries, 1):
            query = query.strip()
            if not query:
                continue
            
            # Variable assignment
            var_match = re.match(r'\$(\w+)\s*=\s*(.+)', query)
            if var_match:
                var_name = var_match.group(1)
                actual_query = var_match.group(2)
                
                if self.verbose:
                    print(f"\n[Query {i}] ${var_name} = {actual_query[:50]}...")
                
                result = self.execute(actual_query)
                results.append(result)
                
                if result.get('status') == 'success':
                    variables[var_name] = result
                    if self.verbose:
                        print(f"  ✓ Success - stored in ${var_name}")
                elif result.get('error'):
                    if self.verbose:
                        print(f"  ✗ Error: {result['error']}")
                continue
            
            # Replace variables
            original_query = query
            for var_name, var_value in variables.items():
                for field in ['link_id', 'message_id', 'sequence_id', 'inserted_id', 
                             'algo_id', 'key_id', 'hash_id', 'user_id', 'node_id']:
                    placeholder = f"${{{var_name}.{field}}}"
                    if placeholder in query:
                        if field in var_value:
                            query = query.replace(placeholder, str(var_value[field]))
            
            if self.verbose:
                if query != original_query:
                    print(f"\n[Query {i}] {original_query[:60]}...")
                    print(f"         → {query[:60]}...")
                else:
                    print(f"\n[Query {i}] {query[:60]}{'...' if len(query) > 60 else ''}")
            
            result = self.execute(query)
            results.append(result)
            
            if self.verbose:
                if result.get('status') == 'success':
                    print(f"  ✓ Success")
                elif result.get('error'):
                    print(f"  ✗ Error: {result['error']}")
        
        return results
    
    # ========================================================================
    # Neo4j Graph Operations
    # ========================================================================
    
    def _create_user_node(self, query: str) -> Dict:
        """CREATE USER {"email": "alice@dnacrypt.com", "role": "admin", "trust_score": 95}"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            match = re.search(r'CREATE USER\s*({.*?})$', query, re.IGNORECASE | re.DOTALL)
            if not match:
                return {"error": "Invalid syntax"}
            
            data_str = match.group(1).replace("'", '"')
            data = json.loads(data_str)
            
            # Generate user_id if not provided
            user_id = data.get('user_id', str(uuid.uuid4()))
            data['user_id'] = user_id
            data['created_at'] = datetime.utcnow().isoformat()
            
            # Create node in Neo4j
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    CREATE (u:User $props)
                    RETURN u.user_id as user_id, u.email as email
                    """,
                    props=data
                )
                record = result.single()
            
            return {
                "status": "success",
                "backend": "Neo4j (Graph)",
                "user_id": record['user_id'],
                "email": record['email']
            }
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
    
    def _create_message_node(self, query: str) -> Dict:
        """CREATE MESSAGE NODE {"message_id": "xyz", "urgency": "high"}"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            match = re.search(r'CREATE MESSAGE NODE\s*({.*?})$', query, re.IGNORECASE | re.DOTALL)
            if not match:
                return {"error": "Invalid syntax"}
            
            data_str = match.group(1).replace("'", '"')
            data = json.loads(data_str)
            data['created_at'] = datetime.utcnow().isoformat()
            
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    CREATE (m:Message $props)
                    RETURN m.message_id as message_id
                    """,
                    props=data
                )
                record = result.single()
            
            return {
                "status": "success",
                "backend": "Neo4j (Graph)",
                "message_id": record['message_id']
            }
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
    
    def _create_relationship(self, query: str) -> Dict:
        """
        RELATE USER "alice@dnacrypt.com" SENT MESSAGE "xyz-789" AT "2025-11-15T10:00:00"
        RELATE USER "alice@dnacrypt.com" TRUSTS USER "bob@dnacrypt.com" LEVEL 85
        """
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            # Parse SENT relationship
            sent_match = re.search(
                r'RELATE USER ["\'](.+?)["\'] SENT MESSAGE ["\'](.+?)["\'] AT ["\'](.+?)["\']',
                query, re.IGNORECASE
            )
            
            if sent_match:
                user_email = sent_match.group(1)
                message_id = sent_match.group(2)
                timestamp = sent_match.group(3)
                
                with self.neo4j_driver.session() as session:
                    session.run(
                        """
                        MATCH (u:User {email: $email})
                        MATCH (m:Message {message_id: $msg_id})
                        CREATE (u)-[r:SENT {timestamp: $ts}]->(m)
                        RETURN r
                        """,
                        email=user_email, msg_id=message_id, ts=timestamp
                    )
                
                return {
                    "status": "success",
                    "backend": "Neo4j (Graph)",
                    "relationship": "SENT",
                    "from": user_email,
                    "to": message_id
                }
            
            # Parse TRUSTS relationship
            trust_match = re.search(
                r'RELATE USER ["\'](.+?)["\'] TRUSTS USER ["\'](.+?)["\'] LEVEL (\d+)',
                query, re.IGNORECASE
            )
            
            if trust_match:
                user1 = trust_match.group(1)
                user2 = trust_match.group(2)
                level = int(trust_match.group(3))
                
                with self.neo4j_driver.session() as session:
                    session.run(
                        """
                        MATCH (u1:User {email: $email1})
                        MATCH (u2:User {email: $email2})
                        CREATE (u1)-[r:TRUSTS {level: $level, since: $ts}]->(u2)
                        RETURN r
                        """,
                        email1=user1, email2=user2, level=level, 
                        ts=datetime.utcnow().isoformat()
                    )
                
                return {
                    "status": "success",
                    "backend": "Neo4j (Graph)",
                    "relationship": "TRUSTS",
                    "from": user1,
                    "to": user2,
                    "level": level
                }
            
            return {"error": "Invalid RELATE syntax"}
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
    
    def _find_path(self, query: str) -> Dict:
        """FIND PATH FROM "alice@dnacrypt.com" TO "eve@dnacrypt.com" MAX 5"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            match = re.search(
                r'FIND PATH FROM ["\'](.+?)["\'] TO ["\'](.+?)["\'](?:\s+MAX\s+(\d+))?',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            start_email = match.group(1)
            end_email = match.group(2)
            max_depth = int(match.group(3)) if match.group(3) else 5
            
            with self.neo4j_driver.session() as session:
                result = session.run(
                    f"""
                    MATCH path = shortestPath(
                        (start:User {{email: $start}})-[*1..{max_depth}]-(end:User {{email: $end}})
                    )
                    RETURN path, length(path) as hops
                    """,
                    start=start_email, end=end_email
                )
                
                record = result.single()
                if record:
                    path_nodes = [node['email'] for node in record['path'].nodes]
                    return {
                        "status": "success",
                        "backend": "Neo4j (Graph)",
                        "from": start_email,
                        "to": end_email,
                        "hops": record['hops'],
                        "path": path_nodes
                    }
                else:
                    return {
                        "status": "success",
                        "message": "No path found",
                        "from": start_email,
                        "to": end_email
                    }
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
    
    def _find_pattern(self, query: str) -> Dict:
        """FIND PATTERN users WHO accessed MORE THAN 100 messages"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            # Pattern: excessive access
            if 'ACCESSED MORE THAN' in query.upper():
                match = re.search(r'MORE THAN (\d+)', query, re.IGNORECASE)
                threshold = int(match.group(1)) if match else 100
                
                with self.neo4j_driver.session() as session:
                    result = session.run(
                        """
                        MATCH (u:User)-[:ACCESSED]->(m:Message)
                        WITH u, COUNT(m) as access_count
                        WHERE access_count > $threshold
                        RETURN u.email as email, access_count
                        ORDER BY access_count DESC
                        """,
                        threshold=threshold
                    )
                    
                    records = [dict(record) for record in result]
                
                return {
                    "status": "success",
                    "backend": "Neo4j (Graph)",
                    "pattern": "excessive_access",
                    "threshold": threshold,
                    "count": len(records),
                    "results": records
                }
            
            return {"error": "Unknown pattern"}
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
    
    def _detect_anomaly(self, query: str) -> Dict:
        """DETECT ANOMALY IN access patterns"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            with self.neo4j_driver.session() as session:
                # Find users with unusual access patterns
                result = session.run(
                    """
                    MATCH (u:User)-[a:ACCESSED]->(m:Message)
                    WITH u, COUNT(DISTINCT m) as msg_count,
                         COUNT(a) as access_count,
                         AVG(a.duration) as avg_duration
                    WHERE access_count > msg_count * 3
                    RETURN u.email as email, 
                           msg_count, 
                           access_count,
                           (access_count * 1.0 / msg_count) as access_ratio
                    ORDER BY access_ratio DESC
                    LIMIT 10
                    """
                )
                
                anomalies = [dict(record) for record in result]
            
            return {
                "status": "success",
                "backend": "Neo4j (Graph)",
                "anomaly_type": "excessive_repeated_access",
                "count": len(anomalies),
                "anomalies": anomalies
            }
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
    
    def _track_access(self, query: str) -> Dict:
        """TRACK ACCESS BY "alice@dnacrypt.com" TO MESSAGE "xyz-789" ACTION "decrypt" SUCCESS true"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            match = re.search(
                r'TRACK ACCESS BY ["\'](.+?)["\'] TO MESSAGE ["\'](.+?)["\'] ACTION ["\'](.+?)["\'] SUCCESS (\w+)',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            user_email = match.group(1)
            message_id = match.group(2)
            action = match.group(3)
            success = match.group(4).lower() == 'true'
            
            with self.neo4j_driver.session() as session:
                session.run(
                    """
                    MATCH (u:User {email: $email})
                    MATCH (m:Message {message_id: $msg_id})
                    CREATE (u)-[a:ACCESSED {
                        timestamp: $ts,
                        action: $action,
                        success: $success,
                        ip_address: $ip
                    }]->(m)
                    """,
                    email=user_email, msg_id=message_id, action=action,
                    success=success, ts=datetime.utcnow().isoformat(),
                    ip="0.0.0.0"
                )
            
            return {
                "status": "success",
                "backend": "Neo4j (Graph)",
                "access_tracked": True
            }
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
    
    def _show_graph(self, query: str) -> Dict:
        """SHOW GRAPH stats"""
        if not self.neo4j_driver:
            return {"error": "Neo4j not connected"}
        
        try:
            with self.neo4j_driver.session() as session:
                # Count nodes
                user_count = session.run("MATCH (u:User) RETURN COUNT(u) as count").single()['count']
                message_count = session.run("MATCH (m:Message) RETURN COUNT(m) as count").single()['count']
                
                # Count relationships
                sent_count = session.run("MATCH ()-[r:SENT]->() RETURN COUNT(r) as count").single()['count']
                trust_count = session.run("MATCH ()-[r:TRUSTS]->() RETURN COUNT(r) as count").single()['count']
                access_count = session.run("MATCH ()-[r:ACCESSED]->() RETURN COUNT(r) as count").single()['count']
            
            return {
                "status": "success",
                "backend": "Neo4j (Graph)",
                "nodes": {
                    "users": user_count,
                    "messages": message_count,
                    "total": user_count + message_count
                },
                "relationships": {
                    "sent": sent_count,
                    "trusts": trust_count,
                    "accessed": access_count,
                    "total": sent_count + trust_count + access_count
                }
            }
            
        except Neo4jError as e:
            return {"error": f"Neo4j error: {str(e)}"}
    
    # ========================================================================
    # Enhanced SEND MESSAGE (now creates graph relationships too!)
    # ========================================================================
    
    def _send_message(self, query: str) -> Dict:
        """SEND MESSAGE TO messages_admin_adult {...} - Now with graph tracking!"""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(
                r'SEND MESSAGE TO (\w+)\s*({.*?})',
                query, re.IGNORECASE | re.DOTALL
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            table_name = match.group(1)
            data_str = match.group(2).replace("'", '"')
            data = json.loads(data_str)
            
            message_id = str(uuid.uuid4())
            link_id = str(uuid.uuid4())
            
            parts = table_name.split('_')
            role = parts[1] if len(parts) > 1 else None
            age_group = parts[2] if len(parts) > 2 else None
            
            # Insert into MySQL
            insert_query = f"""
                INSERT INTO {table_name}
                (message_id, content_text, sender, receiver, urgency, link_id, role, age_group)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                message_id,
                data['content'],
                data['sender'],
                data['receiver'],
                data.get('urgency', 'medium'),
                link_id,
                role,
                age_group
            )
            
            self.mysql_cursor.execute(insert_query, params)
            self.mysql_conn.commit()
            
            # Also create in Neo4j graph if connected
            if self.neo4j_driver:
                try:
                    with self.neo4j_driver.session() as session:
                        # Create or merge users
                        session.run(
                            "MERGE (u:User {email: $email}) ON CREATE SET u.created_at = $ts",
                            email=data['sender'], ts=datetime.utcnow().isoformat()
                        )
                        session.run(
                            "MERGE (u:User {email: $email}) ON CREATE SET u.created_at = $ts",
                            email=data['receiver'], ts=datetime.utcnow().isoformat()
                        )
                        
                        # Create message node
                        session.run(
                            """
                            CREATE (m:Message {
                                message_id: $msg_id,
                                link_id: $link_id,
                                urgency: $urgency,
                                timestamp: $ts
                            })
                            """,
                            msg_id=message_id, link_id=link_id,
                            urgency=data.get('urgency', 'medium'),
                            ts=datetime.utcnow().isoformat()
                        )
                        
                        # Create SENT relationship
                        session.run(
                            """
                            MATCH (u:User {email: $sender})
                            MATCH (m:Message {message_id: $msg_id})
                            CREATE (u)-[:SENT {timestamp: $ts}]->(m)
                            """,
                            sender=data['sender'], msg_id=message_id,
                            ts=datetime.utcnow().isoformat()
                        )
                        
                        # Create RECEIVED relationship
                        session.run(
                            """
                            MATCH (m:Message {message_id: $msg_id})
                            MATCH (u:User {email: $receiver})
                            CREATE (m)-[:RECEIVED {timestamp: $ts}]->(u)
                            """,
                            msg_id=message_id, receiver=data['receiver'],
                            ts=datetime.utcnow().isoformat()
                        )
                except Neo4jError:
                    # Continue even if graph creation fails
                    pass
            
            return {
                "status": "success",
                "message_id": message_id,
                "link_id": link_id,
                "graph_created": self.neo4j_driver is not None
            }
            
        except Error as e:
            self.mysql_conn.rollback()
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
    
    # ========================================================================
    # MySQL Operations (Keep existing code)
    # ========================================================================
    
    def _create_table_for_role(self, query: str) -> Dict:
        """CREATE TABLE messages FOR ROLE admin AGE adult"""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(
                r'CREATE TABLE (\w+) FOR ROLE (\w+)(?:\s+AGE\s+(\w+))?',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            table_type = match.group(1).lower()
            role = match.group(2).lower()
            age_group = match.group(3).lower() if match.group(3) else None
            
            templates = {
                'messages': """
                    CREATE TABLE IF NOT EXISTS {name} (
                        message_id VARCHAR(36) PRIMARY KEY,
                        content_text TEXT NOT NULL,
                        sender VARCHAR(255) NOT NULL,
                        receiver VARCHAR(255) NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        urgency ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
                        status ENUM('pending', 'sent', 'delivered', 'read') DEFAULT 'pending',
                        link_id VARCHAR(36) UNIQUE NOT NULL,
                        role VARCHAR(50),
                        age_group VARCHAR(50),
                        INDEX idx_sender (sender),
                        INDEX idx_receiver (receiver),
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_link (link_id)
                    )
                """,
                'algorithms': """
                    CREATE TABLE IF NOT EXISTS {name} (
                        algo_id INT AUTO_INCREMENT PRIMARY KEY,
                        message_id VARCHAR(36) NOT NULL,
                        algorithm_name VARCHAR(100) NOT NULL,
                        algorithm_type ENUM('encryption', 'hashing', 'encoding', 'compression') NOT NULL,
                        parameters JSON,
                        execution_order INT,
                        role VARCHAR(50),
                        INDEX idx_message (message_id)
                    )
                """,
                'keys': """
                    CREATE TABLE IF NOT EXISTS {name} (
                        key_id INT AUTO_INCREMENT PRIMARY KEY,
                        message_id VARCHAR(36) NOT NULL,
                        public_key TEXT NOT NULL,
                        key_type ENUM('RSA', 'ECC', 'lattice', 'DNA_based') NOT NULL,
                        key_size INT,
                        role VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_message (message_id)
                    )
                """,
                'hashes': """
                    CREATE TABLE IF NOT EXISTS {name} (
                        hash_id INT AUTO_INCREMENT PRIMARY KEY,
                        message_id VARCHAR(36) NOT NULL,
                        hash_value VARCHAR(512) NOT NULL,
                        hash_algorithm ENUM('SHA256', 'SHA512', 'Blake2', 'DNA_hash') NOT NULL,
                        salt VARCHAR(255),
                        role VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_message (message_id),
                        INDEX idx_hash (hash_value(255))
                    )
                """
            }
            
            if table_type not in templates:
                return {"error": f"Invalid table type: {table_type}"}
            
            if age_group:
                table_name = f"{table_type}_{role}_{age_group}"
            else:
                table_name = f"{table_type}_{role}"
            
            create_sql = templates[table_type].format(name=table_name)
            self.mysql_cursor.execute(create_sql)
            self.mysql_conn.commit()
            
            self.schema_registry[table_name] = {
                'backend': 'mysql',
                'type': table_type,
                'role': role,
                'age_group': age_group
            }
            
            return {
                "status": "success",
                "table": table_name,
                "backend": "MySQL (ACID, 3NF)"
            }
            
        except Error as e:
            self.mysql_conn.rollback()
            return {"error": str(e)}
    
    def _create_collection_for_role(self, query: str) -> Dict:
        """CREATE COLLECTION sequences FOR ROLE admin"""
        if self.mongo_db is None:
            return {"error": "MongoDB not connected"}
        
        try:
            match = re.search(
                r'CREATE COLLECTION (\w+) FOR ROLE (\w+)',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            coll_type = match.group(1).lower()
            role = match.group(2).lower()
            
            coll_name = f"{coll_type}_{role}"
            
            if coll_name not in self.mongo_db.list_collection_names():
                self.mongo_db.create_collection(coll_name)
            
            self.mongo_db[coll_name].create_index("link_id", unique=True)
            self.mongo_db[coll_name].create_index("created_at")
            
            self.schema_registry[coll_name] = {
                'backend': 'mongodb',
                'type': coll_type,
                'role': role
            }
            
            return {
                "status": "success",
                "collection": coll_name,
                "backend": "MongoDB (BASE)"
            }
            
        except PyMongoError as e:
            return {"error": str(e)}
    
    def _add_algorithm(self, query: str) -> Dict:
        """ADD ALGORITHM TO algorithms_admin {...}"""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(
                r'ADD ALGORITHM TO (\w+)\s*({.*?})',
                query, re.IGNORECASE | re.DOTALL
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            table_name = match.group(1)
            data_str = match.group(2).replace("'", '"')
            data = json.loads(data_str)
            
            role = table_name.split('_')[1] if '_' in table_name else None
            
            insert_query = f"""
                INSERT INTO {table_name}
                (message_id, algorithm_name, algorithm_type, parameters, execution_order, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                data['message_id'],
                data['algorithm'],
                data['type'],
                json.dumps(data.get('parameters', {})),
                data.get('order', 1),
                role
            )
            
            self.mysql_cursor.execute(insert_query, params)
            self.mysql_conn.commit()
            
            return {
                "status": "success",
                "algo_id": self.mysql_cursor.lastrowid
            }
            
        except Error as e:
            self.mysql_conn.rollback()
            return {"error": str(e)}
    
    def _add_key(self, query: str) -> Dict:
        """ADD KEY TO keys_admin {...}"""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(
                r'ADD KEY TO (\w+)\s*({.*?})',
                query, re.IGNORECASE | re.DOTALL
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            table_name = match.group(1)
            data_str = match.group(2).replace("'", '"')
            data = json.loads(data_str)
            
            role = table_name.split('_')[1] if '_' in table_name else None
            
            insert_query = f"""
                INSERT INTO {table_name}
                (message_id, public_key, key_type, key_size, role)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                data['message_id'],
                data['public_key'],
                data['type'],
                data.get('size', 2048),
                role
            )
            
            self.mysql_cursor.execute(insert_query, params)
            self.mysql_conn.commit()
            
            return {
                "status": "success",
                "key_id": self.mysql_cursor.lastrowid
            }
            
        except Error as e:
            self.mysql_conn.rollback()
            return {"error": str(e)}
    
    def _add_hash(self, query: str) -> Dict:
        """ADD HASH TO hashes_admin {...}"""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(
                r'ADD HASH TO (\w+)\s*({.*?})',
                query, re.IGNORECASE | re.DOTALL
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            table_name = match.group(1)
            data_str = match.group(2).replace("'", '"')
            data = json.loads(data_str)
            
            role = table_name.split('_')[1] if '_' in table_name else None
            
            insert_query = f"""
                INSERT INTO {table_name}
                (message_id, hash_value, hash_algorithm, salt, role)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                data['message_id'],
                data['hash'],
                data['algorithm'],
                data.get('salt', ''),
                role
            )
            
            self.mysql_cursor.execute(insert_query, params)
            self.mysql_conn.commit()
            
            return {
                "status": "success",
                "hash_id": self.mysql_cursor.lastrowid
            }
            
        except Error as e:
            self.mysql_conn.rollback()
            return {"error": str(e)}
    
    def _store_sequence(self, query: str) -> Dict:
        """STORE SEQUENCE IN sequences_admin {...}"""
        if self.mongo_db is None:
            return {"error": "MongoDB not connected"}
        
        try:
            match = re.search(
                r'STORE SEQUENCE IN (\w+)\s*({.*})',
                query, re.IGNORECASE | re.DOTALL
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            coll_name = match.group(1)
            data_str = match.group(2)
            
            try:
                data_str_clean = data_str.replace("'", '"')
                data = json.loads(data_str_clean)
            except json.JSONDecodeError:
                try:
                    import ast
                    data = ast.literal_eval(data_str)
                except:
                    return {"error": "Invalid JSON format"}
            
            metadata = data.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            sequence_doc = {
                "link_id": data['link_id'],
                "original_sequence": data.get('original', ''),
                "encrypted_sequence": data.get('encrypted', ''),
                "digest_sequence": data.get('digest', ''),
                "final_sequence": data.get('final', ''),
                "metadata": metadata,
                "role": coll_name.split('_')[1] if '_' in coll_name else None,
                "created_at": datetime.utcnow()
            }
            
            result = self.mongo_db[coll_name].insert_one(sequence_doc)
            
            return {
                "status": "success",
                "sequence_id": str(result.inserted_id),
                "link_id": data['link_id']
            }
            
        except PyMongoError as e:
            return {"error": str(e)}
        except KeyError as e:
            return {"error": f"Missing required field: {str(e)}"}
        except Exception as e:
            return {"error": f"Store sequence failed: {str(e)}"}
    
    def _get_message(self, query: str) -> Dict:
        """GET MESSAGE FROM messages_admin_adult WHERE message_id = "..."""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(
                r'GET MESSAGE FROM (\w+) WHERE\s+(\w+)\s*=\s*["\']?(.*?)["\']?$',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            table_name = match.group(1)
            field = match.group(2)
            value = match.group(3).strip('"\'')
            
            select_query = f"SELECT * FROM {table_name} WHERE {field} = %s"
            self.mysql_cursor.execute(select_query, (value,))
            result = self.mysql_cursor.fetchone()
            
            if not result:
                return {"error": "Message not found"}
            
            if 'timestamp' in result and result['timestamp']:
                result['timestamp'] = result['timestamp'].isoformat()
            
            return {"status": "success", "message": result}
            
        except Error as e:
            return {"error": str(e)}
    
    def _get_sequence(self, query: str) -> Dict:
        """GET SEQUENCE FROM sequences_admin WHERE link_id = "..."""
        if self.mongo_db is None:
            return {"error": "MongoDB not connected"}
        
        try:
            match = re.search(
                r'GET SEQUENCE FROM (\w+) WHERE\s+link_id\s*=\s*["\']?(.*?)["\']?$',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            coll_name = match.group(1)
            link_id = match.group(2).strip('"\'')
            
            sequence = self.mongo_db[coll_name].find_one({"link_id": link_id})
            
            if not sequence:
                return {"error": "Sequence not found"}
            
            sequence['_id'] = str(sequence['_id'])
            if 'created_at' in sequence:
                sequence['created_at'] = sequence['created_at'].isoformat()
            
            return {"status": "success", "sequence": sequence}
            
        except PyMongoError as e:
            return {"error": str(e)}
    
    def _link_data(self, query: str) -> Dict:
        """LINK DATA WHERE link_id = "uuid" - Now includes graph data!"""
        try:
            match = re.search(
                r'LINK DATA WHERE\s+link_id\s*=\s*["\']?(.*?)["\']?$',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            link_id = match.group(1).strip('"\'')
            
            result = {
                "status": "success",
                "link_id": link_id,
                "mysql_data": {},
                "mongodb_data": {},
                "neo4j_data": {}
            }
            
            # Search MySQL
            if self.mysql_cursor:
                for table_name, table_info in self.schema_registry.items():
                    if table_info.get('backend') == 'mysql' and table_info.get('type') == 'messages':
                        try:
                            query_sql = f"SELECT * FROM {table_name} WHERE link_id = %s"
                            self.mysql_cursor.execute(query_sql, (link_id,))
                            msg = self.mysql_cursor.fetchone()
                            
                            if msg:
                                if 'timestamp' in msg and msg['timestamp']:
                                    msg['timestamp'] = msg['timestamp'].isoformat()
                                result['mysql_data']['message'] = msg
                                result['mysql_data']['table'] = table_name
                                break
                        except:
                            continue
            
            # Search MongoDB
            if self.mongo_db is not None:
                for coll_name, coll_info in self.schema_registry.items():
                    if coll_info.get('backend') == 'mongodb':
                        try:
                            seq = self.mongo_db[coll_name].find_one({"link_id": link_id})
                            if seq:
                                seq['_id'] = str(seq['_id'])
                                if 'created_at' in seq:
                                    seq['created_at'] = seq['created_at'].isoformat()
                                result['mongodb_data']['sequence'] = seq
                                result['mongodb_data']['collection'] = coll_name
                                break
                        except:
                            continue
            
            # Search Neo4j
            if self.neo4j_driver:
                try:
                    with self.neo4j_driver.session() as session:
                        graph_result = session.run(
                            """
                            MATCH (m:Message {link_id: $link_id})
                            OPTIONAL MATCH (sender:User)-[sent:SENT]->(m)
                            OPTIONAL MATCH (m)-[received:RECEIVED]->(receiver:User)
                            OPTIONAL MATCH (u:User)-[accessed:ACCESSED]->(m)
                            RETURN m, sender, receiver, 
                                   COUNT(accessed) as access_count,
                                   COLLECT(DISTINCT u.email) as accessed_by
                            """,
                            link_id=link_id
                        )
                        
                        record = graph_result.single()
                        if record:
                            result['neo4j_data'] = {
                                'sender': record['sender']['email'] if record['sender'] else None,
                                'receiver': record['receiver']['email'] if record['receiver'] else None,
                                'access_count': record['access_count'],
                                'accessed_by': record['accessed_by']
                            }
                except:
                    pass
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _polyglot_join(self, query: str) -> Dict:
        """JOIN messages_admin_adult WITH sequences_admin ON link_id"""
        try:
            match = re.search(
                r'JOIN (\w+) WITH (\w+) ON (\w+)(?:\s+WHERE\s+(.*))?',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid JOIN syntax"}
            
            mysql_table = match.group(1)
            mongo_collection = match.group(2)
            join_field = match.group(3)
            where_clause = match.group(4)
            
            if where_clause:
                mysql_query = f"SELECT * FROM {mysql_table} WHERE {where_clause}"
            else:
                mysql_query = f"SELECT * FROM {mysql_table}"
            
            self.mysql_cursor.execute(mysql_query)
            mysql_results = self.mysql_cursor.fetchall()
            
            joined_results = []
            
            for mysql_row in mysql_results:
                if join_field not in mysql_row:
                    continue
                
                link_value = mysql_row[join_field]
                mongo_doc = self.mongo_db[mongo_collection].find_one({join_field: link_value})
                
                if mongo_doc:
                    mongo_doc['_id'] = str(mongo_doc['_id'])
                    if 'created_at' in mongo_doc:
                        mongo_doc['created_at'] = mongo_doc['created_at'].isoformat()
                    
                    joined_row = {
                        'mysql_data': dict(mysql_row),
                        'mongodb_data': mongo_doc,
                        'join_field': join_field,
                        'join_value': link_value
                    }
                    
                    if 'timestamp' in joined_row['mysql_data'] and joined_row['mysql_data']['timestamp']:
                        joined_row['mysql_data']['timestamp'] = joined_row['mysql_data']['timestamp'].isoformat()
                    
                    joined_results.append(joined_row)
            
            return {
                "status": "success",
                "join_type": "MySQL ⟕ MongoDB",
                "mysql_table": mysql_table,
                "mongodb_collection": mongo_collection,
                "join_field": join_field,
                "count": len(joined_results),
                "results": joined_results
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _list_messages(self, query: str) -> Dict:
        """LIST MESSAGES FROM messages_admin_adult"""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(
                r'LIST MESSAGES FROM (\w+)(?:\s+WHERE\s+(.*))?',
                query, re.IGNORECASE
            )
            
            if not match:
                return {"error": "Invalid syntax"}
            
            table_name = match.group(1)
            where_clause = match.group(2)
            
            if where_clause:
                select_query = f"SELECT * FROM {table_name} WHERE {where_clause} ORDER BY timestamp DESC"
            else:
                select_query = f"SELECT * FROM {table_name} ORDER BY timestamp DESC"
            
            self.mysql_cursor.execute(select_query)
            results = self.mysql_cursor.fetchall()
            
            for result in results:
                if 'timestamp' in result and result['timestamp']:
                    result['timestamp'] = result['timestamp'].isoformat()
            
            return {
                "status": "success",
                "count": len(results),
                "messages": results
            }
            
        except Error as e:
            return {"error": str(e)}
    
    # ========================================================================
    # Legacy Methods (Keep for backward compatibility)
    # ========================================================================
    
    def _make_table(self, query: str) -> Dict:
        """MAKE TABLE users WITH (name:text, age:int)"""
        if not self.mysql_cursor:
            return {"error": "MySQL not connected"}
        
        try:
            match = re.search(r'MAKE TABLE (\w+) WITH\s*\((.*?)\)', query, re.IGNORECASE)
            if not match:
                return {"error": "Invalid syntax"}
            
            table_name = match.group(1)
            fields_str = match.group(2)
            
            type_mapping = {
                'int': 'INT', 'integer': 'INT', 'text': 'VARCHAR(255)',
                'float': 'FLOAT', 'date': 'DATE', 'datetime': 'DATETIME',
                'bool': 'BOOLEAN'
            }
            
            fields = ['id INT AUTO_INCREMENT PRIMARY KEY']
            field_schema = {}
            
            for field in fields_str.split(','):
                field = field.strip()
                if ':' in field:
                    name, ftype = field.split(':')
                    name, ftype = name.strip(), ftype.strip().lower()
                    if name.lower() != 'id':
                        sql_type = type_mapping.get(ftype, 'VARCHAR(255)')
                        fields.append(f"{name} {sql_type}")
                        field_schema[name] = ftype
            
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(fields)})"
            self.mysql_cursor.execute(create_sql)
            self.mysql_conn.commit()
            
            self.schema_registry[table_name] = {'backend': 'mysql', 'fields': field_schema}
            return {"status": "success", "table": table_name}
            
        except Error as e:
            self.mysql_conn.rollback()
            return {"error": str(e)}
    
    def _make_collection(self, query: str) -> Dict:
        """MAKE COLLECTION logs"""
        if self.mongo_db is None:
            return {"error": "MongoDB not connected"}
        
        try:
            match = re.search(r'MAKE COLLECTION (\w+)', query, re.IGNORECASE)
            if not match:
                return {"error": "Invalid syntax"}
            
            coll_name = match.group(1)
            if coll_name not in self.mongo_db.list_collection_names():
                self.mongo_db.create_collection(coll_name)
            
            self.schema_registry[coll_name] = {'backend': 'mongodb'}
            return {"status": "success", "collection": coll_name}
            
        except PyMongoError as e:
            return {"error": str(e)}
    
    def _put_data(self, query: str) -> Dict:
        """PUT INTO target DATA {...}"""
        try:
            match = re.search(r'PUT INTO (\w+) DATA\s*({.*?})$', query, re.IGNORECASE | re.DOTALL)
            if not match:
                return {"error": "Invalid syntax"}
            
            target = match.group(1)
            data_str = match.group(2).replace("'", '"')
            data = json.loads(data_str)
            
            if target not in self.schema_registry:
                return {"error": f"Target '{target}' does not exist"}
            
            backend = self.schema_registry[target]['backend']
            
            if backend == 'mysql':
                fields = list(data.keys())
                placeholders = ', '.join(['%s' for _ in fields])
                values = [data[f] for f in fields]
                insert_sql = f"INSERT INTO {target} ({', '.join(fields)}) VALUES ({placeholders})"
                self.mysql_cursor.execute(insert_sql, values)
                self.mysql_conn.commit()
                return {"status": "success", "inserted_id": self.mysql_cursor.lastrowid}
            else:
                data['created_at'] = datetime.utcnow()
                result = self.mongo_db[target].insert_one(data)
                return {"status": "success", "inserted_id": str(result.inserted_id)}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _fetch_data(self, query: str) -> Dict:
        """FETCH FROM source WHERE/ALL"""
        try:
            match = re.search(r'FETCH FROM (\w+)\s+(?:WHERE\s+(.*)|ALL)', query, re.IGNORECASE)
            if not match:
                return {"error": "Invalid syntax"}
            
            source = match.group(1)
            condition = match.group(2)
            
            if source not in self.schema_registry:
                return {"error": f"Source '{source}' does not exist"}
            
            backend = self.schema_registry[source]['backend']
            
            if backend == 'mysql':
                if condition:
                    query_sql = f"SELECT * FROM {source} WHERE {condition}"
                else:
                    query_sql = f"SELECT * FROM {source}"
                self.mysql_cursor.execute(query_sql)
                results = self.mysql_cursor.fetchall()
                return {"status": "success", "count": len(results), "data": results}
            else:
                mongo_filter = self._parse_condition(condition) if condition else {}
                results = list(self.mongo_db[source].find(mongo_filter))
                for r in results:
                    r['_id'] = str(r['_id'])
                    if 'created_at' in r:
                        r['created_at'] = r['created_at'].isoformat()
                return {"status": "success", "count": len(results), "data": results}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _change_data(self, query: str) -> Dict:
        """CHANGE IN target SET field=value WHERE condition"""
        try:
            match = re.search(r'CHANGE IN (\w+) SET\s+(.*?)\s+WHERE\s+(.*)', query, re.IGNORECASE)
            if not match:
                return {"error": "Invalid syntax"}
            
            target, set_clause, condition = match.groups()
            
            if target not in self.schema_registry:
                return {"error": f"Target '{target}' does not exist"}
            
            backend = self.schema_registry[target]['backend']
            
            if backend == 'mysql':
                update_sql = f"UPDATE {target} SET {set_clause} WHERE {condition}"
                self.mysql_cursor.execute(update_sql)
                self.mysql_conn.commit()
                return {"status": "success", "updated": self.mysql_cursor.rowcount}
            else:
                parts = set_clause.split('=')
                field = parts[0].strip()
                value = parts[1].strip().strip('"\'')
                try:
                    value = float(value) if '.' in value else int(value)
                except:
                    pass
                mongo_filter = self._parse_condition(condition)
                result = self.mongo_db[target].update_many(mongo_filter, {"$set": {field: value}})
                return {"status": "success", "updated": result.modified_count}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _remove_data(self, query: str) -> Dict:
        """REMOVE FROM target WHERE condition"""
        try:
            match = re.search(r'REMOVE FROM (\w+) WHERE\s+(.*)', query, re.IGNORECASE)
            if not match:
                return {"error": "Invalid syntax"}
            
            target, condition = match.groups()
            
            if target not in self.schema_registry:
                return {"error": f"Target '{target}' does not exist"}
            
            backend = self.schema_registry[target]['backend']
            
            if backend == 'mysql':
                delete_sql = f"DELETE FROM {target} WHERE {condition}"
                self.mysql_cursor.execute(delete_sql)
                self.mysql_conn.commit()
                return {"status": "success", "deleted": self.mysql_cursor.rowcount}
            else:
                mongo_filter = self._parse_condition(condition)
                result = self.mongo_db[target].delete_many(mongo_filter)
                return {"status": "success", "deleted": result.deleted_count}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _show_tables(self) -> Dict:
        """Show all tables"""
        tables = [name for name, info in self.schema_registry.items() 
                 if info.get('backend') == 'mysql']
        return {"status": "success", "tables": tables, "count": len(tables)}
    
    def _show_collections(self) -> Dict:
        """Show all collections"""
        collections = [name for name, info in self.schema_registry.items() 
                      if info.get('backend') == 'mongodb']
        return {"status": "success", "collections": collections, "count": len(collections)}
    
    def _drop(self, query: str) -> Dict:
        """DROP target"""
        try:
            match = re.search(r'DROP (\w+)', query, re.IGNORECASE)
            if not match:
                return {"error": "Invalid syntax"}
            
            target = match.group(1)
            if target not in self.schema_registry:
                return {"error": f"Target '{target}' does not exist"}
            
            backend = self.schema_registry[target]['backend']
            
            if backend == 'mysql':
                self.mysql_cursor.execute(f"DROP TABLE {target}")
                self.mysql_conn.commit()
            else:
                self.mongo_db[target].drop()
            
            del self.schema_registry[target]
            return {"status": "success"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_condition(self, condition: str) -> Dict:
        """Parse condition to MongoDB filter"""
        if not condition:
            return {}
        
        operators = {
            '>=': '$gte', '<=': '$lte', '>': '$gt',
            '<': '$lt', '!=': '$ne', '=': '$eq'
        }
        
        for op, mongo_op in operators.items():
            if op in condition:
                parts = condition.split(op)
                field = parts[0].strip()
                value = parts[1].strip().strip('"\'')
                try:
                    value = float(value) if '.' in value else int(value)
                except:
                    pass
                if mongo_op == '$eq':
                    return {field: value}
                else:
                    return {field: {mongo_op: value}}
        return {}
    
    def close(self):
        """Close all database connections"""
        if self.mysql_cursor:
            self.mysql_cursor.close()
        if self.mysql_conn:
            self.mysql_conn.close()
        if self.mongo_client:
            self.mongo_client.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        if self.verbose:
            print("✓ All database connections closed")
