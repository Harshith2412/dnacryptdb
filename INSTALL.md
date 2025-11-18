# DNACryptDB - Installation Guide

## Quick Install (Copy-Paste Commands)

### Step 1: Create Project Structure

```bash
# Create all directories
mkdir -p dnacryptdb/dnacryptdb
mkdir -p dnacryptdb/examples
cd dnacryptdb
```

### Step 2: Create All Files

**Create `dnacryptdb/__init__.py`:**
```bash
cat > dnacryptdb/__init__.py << 'EOF'
"""
DNACryptDB - Polyglot Database System
A unified query language for MySQL and MongoDB
"""

from .core import DNACryptDB

__version__ = "1.0.0"
__author__ = "Harshith"
__all__ = ["DNACryptDB"]
EOF
```

**Copy `dnacryptdb/core.py` from artifact**

**Copy `dnacryptdb/cli.py` from artifact**

**Create `setup.py`:**
```bash
cat > setup.py << 'EOF'
# Copy setup.py content from artifact
EOF
```

**Create `requirements.txt`:**
```bash
cat > requirements.txt << 'EOF'
mysql-connector-python>=8.0.0
pymongo>=4.0.0
EOF
```

**Copy `README.md` from artifact**

**Copy example files from artifacts**

### Step 3: Install Package

```bash
# Install in development mode
pip install -e .
```

### Step 4: Initialize Database Config

```bash
dnacryptdb init
```

Enter your database credentials when prompted.

### Step 5: Test Installation

```bash
# Run example script
dnacryptdb run examples/example.dnacdb

# Or try interactive mode
dnacryptdb interactive
```

---

## Manual Installation

### Prerequisites

1. **Python 3.8+**
```bash
python --version  # Should be 3.8 or higher
```

2. **MySQL 5.7+**
```bash
# Check if MySQL is running
mysql --version

# Start MySQL
# macOS:
brew services start mysql
# Linux:
sudo systemctl start mysql
```

3. **MongoDB 4.0+**
```bash
# Check if MongoDB is running
mongod --version

# Start MongoDB
# macOS:
brew services start mongodb-community
# Linux:
sudo systemctl start mongod
```

### Installation Steps

1. **Download/Clone the project**
```bash
git clone <repository-url>
cd dnacryptdb
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install the package**
```bash
# Development mode (can edit code)
pip install -e .

# Or production install
pip install .
```

4. **Verify installation**
```bash
dnacryptdb --help
```

---

## Database Setup

### MySQL Setup

1. **Create database user**
```bash
mysql -u root -p
```

```sql
CREATE DATABASE dnacryptdb;
CREATE USER 'dnacrypt_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dnacryptdb.* TO 'dnacrypt_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### MongoDB Setup

1. **Start MongoDB**
```bash
# No authentication (development)
mongod --dbpath /path/to/data

# With authentication (production)
mongod --auth --dbpath /path/to/data
```

2. **Create database user (if using auth)**
```bash
mongosh
```

```javascript
use admin
db.createUser({
  user: "dnacrypt_user",
  pwd: "your_password",
  roles: [{ role: "readWrite", db: "dnacryptdb" }]
})
```

---

## Configuration

### Option 1: Interactive Config

```bash
dnacryptdb init
```

### Option 2: Manual Config

Create `dnacdb.config.json`:

```json
{
  "mysql": {
    "host": "localhost",
    "user": "dnacrypt_user",
    "password": "your_password",
    "database": "dnacryptdb"
  },
  "mongodb": {
    "uri": "mongodb://localhost:27017/",
    "database": "dnacryptdb"
  }
}
```

With authentication for MongoDB:
```json
{
  "mysql": {
    "host": "localhost",
    "user": "dnacrypt_user",
    "password": "your_mysql_password",
    "database": "dnacryptdb"
  },
  "mongodb": {
    "uri": "mongodb://dnacrypt_user:your_mongo_password@localhost:27017/",
    "database": "dnacryptdb"
  }
}
```

---

## Testing Installation

### Test 1: Run Example Script

```bash
dnacryptdb run examples/example.dnacdb
```

Expected output:
```
DNACryptDB - Running: examples/example.dnacdb
======================================================================
✓ MySQL connected: dnacryptdb
✓ MongoDB connected: dnacryptdb

[Query 1] MAKE TABLE users WITH (name:text, email:text, age:int)
  ✓ Success

[Query 2] PUT INTO users DATA {"name": "Alice", ...}
  ✓ Success

...

======================================================================
Execution Summary
======================================================================
Total queries: 15
✓ Success: 15
✗ Errors: 0
# Comments: 3
======================================================================
```

### Test 2: Interactive Mode

```bash
dnacryptdb interactive
```

```
dnacdb> MAKE TABLE test WITH (name:text);
{
  "status": "success",
  "message": "Table 'test' created",
  "backend": "MySQL"
}

dnacdb> PUT INTO test DATA {"name": "Hello"};
{
  "status": "success",
  "backend": "MySQL",
  "inserted_id": 1
}

dnacdb> FETCH FROM test ALL;
[
  {
    "id": 1,
    "name": "Hello"
  }
]

dnacdb> exit
```

---

## Troubleshooting

### Issue: "dnacryptdb: command not found"

**Solution:**
```bash
# Reinstall package
pip uninstall dnacryptdb
pip install -e .

# Or add to PATH
export PATH="$PATH:$HOME/.local/bin"
```

### Issue: "MySQL connection failed"

**Solutions:**
1. Check MySQL is running:
```bash
mysql -u root -p  # Should connect
```

2. Verify credentials in `dnacdb.config.json`

3. Create database manually:
```bash
mysql -u root -p -e "CREATE DATABASE dnacryptdb;"
```

### Issue: "MongoDB connection failed"

**Solutions:**
1. Check MongoDB is running:
```bash
mongosh  # Should connect
```

2. Start MongoDB:
```bash
# macOS:
brew services start mongodb-community
# Linux:
sudo systemctl start mongod
```

3. Check MongoDB port:
```bash
sudo lsof -i :27017  # Should show mongod
```

### Issue: "Config file not found"

**Solution:**
```bash
# Initialize config in current directory
dnacryptdb init

# Or specify config path
dnacryptdb run script.dnacdb -c /path/to/config.json
```

---

## Uninstallation

```bash
# Uninstall package
pip uninstall dnacryptdb

# Remove config file
rm dnacdb.config.json

# Optional: Drop databases
mysql -u root -p -e "DROP DATABASE dnacryptdb;"
mongosh --eval "db.getSiblingDB('dnacryptdb').dropDatabase()"
```

---

## Next Steps

1. **Read the README.md** for query syntax
2. **Run example scripts** in `examples/` directory
3. **Create your own `.dnacdb` files**
4. **Explore interactive mode**

For more help:
- GitHub Issues: https://github.com/yourusername/dnacryptdb/issues
- Email: harshith@northeastern.edu