# Neo4j Installation Guide for DNACryptDB

## Installing Neo4j (Third Database Engine)

---

## macOS Installation

### Option 1: Homebrew (Recommended)

```bash
# Install Neo4j
brew install neo4j

# Start Neo4j
brew services start neo4j

# Or run manually
neo4j start
```

### Option 2: Docker (Easiest!)

```bash
# Run Neo4j in Docker
docker run -d \
    --name neo4j \
    -p 7474:7474 \
    -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest

# Verify it's running
docker ps | grep neo4j
```

---

## Ubuntu/Linux Installation

```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Install
sudo apt update
sudo apt install neo4j

# Start
sudo systemctl start neo4j
sudo systemctl enable neo4j
```

---

## Windows Installation

1. Download from: https://neo4j.com/download/
2. Run installer
3. Start Neo4j Desktop
4. Create new database
5. Start the database

---

## Verify Installation

### Check Neo4j is Running

```bash
# Check service status
neo4j status

# Or check port
curl http://localhost:7474
# Should return HTML page
```

### Access Neo4j Browser

Open browser and go to:
```
http://localhost:7474
```

**Default credentials:**
- Username: `neo4j`
- Password: `neo4j`
- (You'll be prompted to change password on first login)

---

## Configure for DNACryptDB

### Update dnacdb.config.json

```json
{
  "mysql": {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "dnacryptdb"
  },
  "mongodb": {
    "uri": "mongodb://localhost:27017/",
    "database": "dnacryptdb"
  },
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_neo4j_password"
  }
}
```

### Or Use Interactive Init

```bash
dnacryptdb init
```

It will now prompt for Neo4j credentials:

```
[Neo4j Configuration]
  Host (default: localhost): [Enter]
  Port (default: 7687): [Enter]
  Username (default: neo4j): [Enter]
  Password (default: password): your_password
```

---

## Install Python Neo4j Driver

```bash
# Install the driver
pip install neo4j

# Or reinstall all dependencies
pip install -r requirements.txt
```

---

## Test Neo4j Connection

### Method 1: Using DNACryptDB

```bash
dnacryptdb interactive

dnacdb> CREATE USER {"email": "test@test.com", "role": "test"};
# Should return success
```

### Method 2: Using Python

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

with driver.session() as session:
    result = session.run("RETURN 'Connection successful!' as message")
    print(result.single()['message'])

driver.close()
```

### Method 3: Using Neo4j Browser

1. Go to http://localhost:7474
2. Login with credentials
3. Run query:
   ```cypher
   RETURN "Neo4j is working!" as message
   ```

---

## Quick Start After Installation

```bash
# 1. Update config
dnacryptdb init

# 2. Run triglot example
dnacryptdb run examples/triglot_complete_example.dnacdb

# 3. View graph in browser
# Open http://localhost:7474 and run:
# MATCH (n) RETURN n LIMIT 25
```

---

## Neo4j Ports

| Port | Purpose |
|------|---------|
| 7474 | HTTP (Neo4j Browser) |
| 7473 | HTTPS |
| 7687 | Bolt Protocol (for drivers) |

Make sure these ports are not blocked by firewall!

---

## Troubleshooting

### Issue: "Neo4j not starting"

```bash
# Check logs
neo4j console

# Or with Docker
docker logs neo4j
```

### Issue: "Connection refused on port 7687"

```bash
# Check if Neo4j is running
neo4j status

# Start it
neo4j start

# Or with Docker
docker start neo4j
```

### Issue: "Authentication failed"

Default password is `neo4j`. On first login you must change it.

```bash
# Reset password
neo4j-admin set-initial-password your_new_password
```

---

## Uninstall Neo4j

### Homebrew

```bash
brew services stop neo4j
brew uninstall neo4j
```

### Docker

```bash
docker stop neo4j
docker rm neo4j
```

### Linux

```bash
sudo systemctl stop neo4j
sudo apt remove neo4j
```

---

## Next Steps

After installing Neo4j:

1. ✅ Run `dnacryptdb init` to update config
2. ✅ Test with `examples/triglot_complete_example.dnacdb`
3. ✅ View graph in Neo4j Browser (http://localhost:7474)
4. ✅ Explore security queries and relationship tracking

---

## Resources

- Neo4j Documentation: https://neo4j.com/docs/
- Neo4j Desktop: https://neo4j.com/download/
- Cypher Query Language: https://neo4j.com/developer/cypher/
- Python Driver: https://neo4j.com/docs/api/python-driver/current/