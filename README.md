# DNACryptDB
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MySQL](https://img.shields.io/badge/MySQL-5.7+-blue.svg)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.0+-green.svg)](https://www.mongodb.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-4.0+-blue.svg)](https://neo4j.com/)

A secure triglot database system combining MySQL, MongoDB, and Neo4j with military-grade encryption.

A polyglot database system with a custom query language that unifies MySQL (relational) and MongoDB (document store) operations.

## Features

- Unified Query Language**: One syntax for both MySQL and MongoDB
- Automatic Backend Routing**: Structured data → MySQL, Flexible data → MongoDB
- SQL Injection Proof**: Parameterized queries throughout
- Script Files**: Write `.dnacdb` files and execute them
- Interactive Mode**: Test queries in real-time
- Easy Configuration**: Simple JSON config file

## Installation



### From PyPI (once published)

```bash
pip install dnacryptdb
```

## Quick Start

### 1. Initialize Configuration

```bash
dnacryptdb init
```

This creates `dnacdb.config.json` with your database credentials:

```json
{
  "mysql": {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "dnacryptdb"
  },
  "mongodb": {
    "uri": "mongodb://localhost:27017/",
    "database": "dnacryptdb"
  }
}
```

### 2. Create a Script File

Create `hello.dnacdb`:

```sql
-- Create a table in MySQL
MAKE TABLE users WITH (name:text, email:text, age:int);

-- Insert data
PUT INTO users DATA {"name": "Alice", "email": "alice@example.com", "age": 30};
PUT INTO users DATA {"name": "Bob", "email": "bob@example.com", "age": 25};

-- Query data
FETCH FROM users WHERE age > 26;

-- Create a collection in MongoDB
MAKE COLLECTION logs;

-- Insert flexible documents
PUT INTO logs DATA {"level": "INFO", "message": "Application started"};

-- Show all structures
SHOW TABLES;
SHOW COLLECTIONS;
```

### 3. Run the Script

```bash
dnacryptdb run hello.dnacdb
```

### 4. Interactive Mode

```bash
dnacryptdb interactive

dnacdb> MAKE TABLE products WITH (name:text, price:float);
dnacdb> PUT INTO products DATA {"name": "Laptop", "price": 999.99};
dnacdb> FETCH FROM products ALL;
dnacdb> exit
```

## Query Language Reference

### Create Structures

```sql
-- Create relational table (MySQL)
MAKE TABLE tablename WITH (field1:type1, field2:type2);

-- Create document collection (MongoDB)
MAKE COLLECTION collectionname;
```

### Data Types

- `int` / `integer` - Integer numbers
- `float` / `double` - Floating point numbers
- `text` / `string` - Text strings
- `date` - Date values
- `datetime` / `timestamp` - Date and time
- `bool` / `boolean` - Boolean values

### Insert Data

```sql
PUT INTO target DATA {"field": "value", "field2": 123};
```

### Query Data

```sql
-- Query all records
FETCH FROM source ALL;

-- Query with condition
FETCH FROM source WHERE field > value;
FETCH FROM source WHERE field = "value";
```

### Update Data

```sql
CHANGE IN target SET field = value WHERE condition;
CHANGE IN target SET field = "value" WHERE name = "Alice";
```

### Delete Data

```sql
REMOVE FROM target WHERE condition;
REMOVE FROM target WHERE age < 18;
```

### Show Structures

```sql
SHOW TABLES;       -- List MySQL tables
SHOW COLLECTIONS;  -- List MongoDB collections
```

### Drop Structures

```sql
DROP tablename;
```

### Comments

```sql
-- This is a comment
# This is also a comment
```

## Examples

### Example 1: User Management

```sql
-- Create users table
MAKE TABLE users WITH (username:text, email:text, age:int);

-- Insert users
PUT INTO users DATA {"username": "alice", "email": "alice@example.com", "age": 30};
PUT INTO users DATA {"username": "bob", "email": "bob@example.com", "age": 25};
PUT INTO users DATA {"username": "charlie", "email": "charlie@example.com", "age": 35};

-- Query users over 26
FETCH FROM users WHERE age > 26;

-- Update user age
CHANGE IN users SET age = 31 WHERE username = "alice";

-- Remove young users
REMOVE FROM users WHERE age < 30;
```

### Example 2: Flexible Analytics

```sql
-- Create analytics collection
MAKE COLLECTION analytics;

-- Insert various event types
PUT INTO analytics DATA {"event": "page_view", "page": "/home", "timestamp": "2025-11-14T10:00:00"};
PUT INTO analytics DATA {"event": "click", "button": "signup", "metadata": {"campaign": "winter"}};
PUT INTO analytics DATA {"event": "purchase", "amount": 99.99, "items": ["laptop", "mouse"]};

-- Query all analytics
FETCH FROM analytics ALL;
```

### Example 3: Mixed Data Types

```sql
-- Structured product data in MySQL
MAKE TABLE products WITH (name:text, price:float, stock:int);
PUT INTO products DATA {"name": "Laptop", "price": 999.99, "stock": 50};

-- Flexible review data in MongoDB
MAKE COLLECTION reviews;
PUT INTO reviews DATA {"product": "Laptop", "rating": 5, "comment": "Great!", "tags": ["fast", "reliable"]};

-- Query both
FETCH FROM products ALL;
FETCH FROM reviews ALL;
```

## Architecture

### Backend Selection

DNACryptDB automatically routes operations to the appropriate backend:

- **Structured Data (MySQL)**: Tables with defined schemas
- **Flexible Data (MongoDB)**: Collections with dynamic documents

### Security

- **Parameterized Queries**: All user input is treated as data, not code
- **No SQL Injection**: Uses prepared statements for MySQL
- **Safe JSON Parsing**: No `eval()` or unsafe code execution

### Database Structure

```
MySQL (ACID Properties)
├── Tables with fixed schemas
├── Auto-increment primary keys
├── Type enforcement
└── Relational integrity

MongoDB (BASE Properties)
├── Flexible document schemas
├── Automatic timestamps
├── Nested data support
└── Eventual consistency
```

## Command Line Reference

```bash
# Initialize configuration
dnacryptdb init
dnacryptdb init -o custom_config.json

# Run script files
dnacryptdb run script.dnacdb
dnacryptdb run script.dnacdb -c custom_config.json

# Interactive mode
dnacryptdb interactive
dnacryptdb interactive -c custom_config.json

# Help
dnacryptdb --help
dnacryptdb run --help
```

## Use as Python Library

```python
from dnacryptdb import DNACryptDB

# Initialize
db = DNACryptDB(config_file="dnacdb.config.json")

# Execute single query
result = db.execute("MAKE TABLE users WITH (name:text, age:int)")
print(result)

# Execute script file
results = db.execute_file("script.dnacdb")

# Close connections
db.close()
```

## Requirements

- Python 3.8+
- MySQL 5.7+ or MariaDB 10.2+
- MongoDB 4.0+

## Development

```bash
# Clone repository
git clone https://github.com/Harshith2412/dnacryptdb.git
cd dnacryptdb

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Format code
black dnacryptdb/

# Type checking
mypy dnacryptdb/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for the DNACrypt project at Northeastern University
- Integrates MySQL and MongoDB for polyglot database operations
- Part of MS in Cybersecurity research

## Support

For issues, questions, or contributions, please visit:
- GitHub Issues: https://github.com/Harshith2412/dnacryptdb/issues
- Email: madhavaram.harshith2412@gmail.com

## Changelog

### Version 1.0.0 (2025-11-14)

- Initial release
- Basic CRUD operations
- MySQL and MongoDB integration
- Script file execution
- Interactive mode
- Configuration management