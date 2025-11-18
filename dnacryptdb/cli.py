# """
# DNACryptDB Command Line Interface
# Provides commands for running scripts and interactive mode
# """

# import argparse
# import json
# import sys
# import os
# from .core import DNACryptDB


# def cli_run(args):
#     """Run a .dnacdb script file"""
#     print(f"DNACryptDB - Running: {args.file}")
#     print("="*70)
    
#     try:
#         db = DNACryptDB(config_file=args.config, verbose=True)
#         results = db.execute_file(args.file)
        
#         # Summary
#         print("\n" + "="*70)
#         print(f"Execution Summary")
#         print("="*70)
        
#         total = len(results)
#         success = sum(1 for r in results if r.get('status') == 'success')
#         errors = sum(1 for r in results if r.get('error'))
#         comments = sum(1 for r in results if r.get('status') == 'comment')
        
#         print(f"Total queries: {total}")
#         print(f"✓ Success: {success}")
#         print(f"✗ Errors: {errors}")
#         print(f"# Comments: {comments}")
#         print("="*70)
        
#         db.close()
        
#         return 0 if errors == 0 else 1
        
#     except FileNotFoundError as e:
#         print(f"✗ Error: {e}")
#         return 1
#     except Exception as e:
#         print(f"✗ Unexpected error: {e}")
#         return 1


# def cli_interactive(args):
#     """Start interactive mode"""
#     print("""

#                   DNACryptDB - Interactive Mode                     
#                Type 'help' for commands, 'exit' to quit              
#     """)
    
#     try:
#         db = DNACryptDB(config_file=args.config, verbose=True)
#         print()
        
#         # Interactive loop
#         while True:
#             try:
#                 query = input("dnacdb> ").strip()
                
#                 if query.lower() == 'exit' or query.lower() == 'quit':
#                     print("\nGoodbye!")
#                     break
                
#                 if query.lower() == 'help':
#                     print_help()
#                     continue
                
#                 if query.lower() == 'clear':
#                     os.system('clear' if os.name == 'posix' else 'cls')
#                     continue
                
#                 if not query:
#                     continue
                
#                 # Execute query
#                 result = db.execute(query)
                
#                 # Pretty print result
#                 if result.get('status') == 'success':
#                     if 'data' in result:
#                         print(json.dumps(result['data'], indent=2, default=str))
#                     else:
#                         print(json.dumps(result, indent=2, default=str))
#                 elif result.get('error'):
#                     print(f"✗ Error: {result['error']}")
#                     if result.get('hint'):
#                         print(f"  Hint: {result['hint']}")
#                 else:
#                     print(json.dumps(result, indent=2, default=str))
                
#                 print()
                
#             except KeyboardInterrupt:
#                 print("\n\nUse 'exit' to quit")
#                 continue
#             except EOFError:
#                 print("\n\nGoodbye!")
#                 break
#             except Exception as e:
#                 print(f"✗ Error: {e}\n")
        
#         db.close()
#         return 0
        
#     except FileNotFoundError as e:
#         print(f"\n✗ Error: {e}")
#         print("  Run 'dnacryptdb init' to create a configuration file.")
#         return 1
#     except Exception as e:
#         print(f"\n✗ Unexpected error: {e}")
#         return 1


# def cli_init(args):
#     """Initialize a new DNACryptDB configuration"""
#     print("""

#               DNACryptDB - Configuration Setup                        
#     """)
    
#     print("\n[MySQL Configuration]")
#     mysql_host = input("  Host (default: localhost): ").strip() or "localhost"
#     mysql_user = input("  Username (default: root): ").strip() or "root"
#     mysql_pass = input("  Password: ").strip()
#     mysql_db = input("  Database name (default: dnacryptdb): ").strip() or "dnacryptdb"
    
#     print("\n[MongoDB Configuration]")
#     mongo_host = input("  Host (default: localhost): ").strip() or "localhost"
#     mongo_port = input("  Port (default: 27017): ").strip() or "27017"
#     mongo_db = input("  Database name (default: dnacryptdb): ").strip() or "dnacryptdb"
#     mongo_user = input("  Username (leave empty for no auth): ").strip()
    
#     # Build MongoDB URI
#     if mongo_user:
#         mongo_pass = input("  Password: ").strip()
#         mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"
#     else:
#         mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/"
    
#     # Create configuration
#     config = {
#         "mysql": {
#             "host": mysql_host,
#             "user": mysql_user,
#             "password": mysql_pass,
#             "database": mysql_db
#         },
#         "mongodb": {
#             "uri": mongo_uri,
#             "database": mongo_db
#         }
#     }
    
#     # Save configuration
#     config_file = args.output or "dnacdb.config.json"
    
#     with open(config_file, 'w') as f:
#         json.dump(config, f, indent=2)
    
#     print(f"\n✓ Configuration saved to: {config_file}")
#     print(f"\nYou can now run:")
#     print(f"  dnacryptdb run script.dnacdb")
#     print(f"  dnacryptdb interactive")
    
#     return 0


# def print_help():
#     """Print interactive mode help"""
#     print("""
# Available Commands:
  
#   Create Structures:
#     MAKE TABLE name WITH (field:type, ...)
#     MAKE COLLECTION name
  
#   Insert Data:
#     PUT INTO target DATA {json}
  
#   Query Data:
#     FETCH FROM source WHERE condition
#     FETCH FROM source ALL
  
#   Update Data:
#     CHANGE IN target SET field=value WHERE condition
  
#   Delete Data:
#     REMOVE FROM target WHERE condition
  
#   Show Structures:
#     SHOW TABLES
#     SHOW COLLECTIONS
  
#   Drop Structures:
#     DROP name
  
#   System Commands:
#     help   - Show this help
#     clear  - Clear screen
#     exit   - Exit interactive mode

# Data Types:
#   int, float, text, date, datetime, bool

# Examples:
#   MAKE TABLE users WITH (name:text, age:int);
#   PUT INTO users DATA {"name": "Alice", "age": 30};
#   FETCH FROM users WHERE age > 25;
#   CHANGE IN users SET age = 31 WHERE name = "Alice";
#     """)


# def main():
#     """Main CLI entry point"""
#     parser = argparse.ArgumentParser(
#         prog='dnacryptdb',
#         description='DNACryptDB - Polyglot Database Command Line Tool',
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# Examples:
#   # Initialize configuration
#   dnacryptdb init
  
#   # Run a script file
#   dnacryptdb run script.dnacdb
  
#   # Start interactive mode
#   dnacryptdb interactive
  
#   # Use custom config file
#   dnacryptdb run script.dnacdb -c myconfig.json

# For more information, visit: https://github.com/yourusername/dnacryptdb
#         """
#     )
    
#     subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
#     # Init command
#     init_parser = subparsers.add_parser(
#         'init', 
#         help='Initialize database configuration'
#     )
#     init_parser.add_argument(
#         '-o', '--output',
#         help='Output config file (default: dnacdb.config.json)'
#     )
    
#     # Run command
#     run_parser = subparsers.add_parser(
#         'run',
#         help='Run a .dnacdb script file'
#     )
#     run_parser.add_argument(
#         'file',
#         help='.dnacdb script file to execute'
#     )
#     run_parser.add_argument(
#         '-c', '--config',
#         default='dnacdb.config.json',
#         help='Config file (default: dnacdb.config.json)'
#     )
    
#     # Interactive command
#     interactive_parser = subparsers.add_parser(
#         'interactive',
#         help='Start interactive mode'
#     )
#     interactive_parser.add_argument(
#         '-c', '--config',
#         default='dnacdb.config.json',
#         help='Config file (default: dnacdb.config.json)'
#     )
    
#     # Parse arguments
#     args = parser.parse_args()
    
#     if not args.command:
#         parser.print_help()
#         return 1
    
#     # Route to appropriate handler
#     if args.command == 'init':
#         return cli_init(args)
#     elif args.command == 'run':
#         return cli_run(args)
#     elif args.command == 'interactive':
#         return cli_interactive(args)
#     else:
#         parser.print_help()
#         return 1


# if __name__ == '__main__':
#     sys.exit(main())

"""
DNACryptDB Command Line Interface
Provides commands for running scripts and interactive mode
"""

import argparse
import json
import sys
import os
from .core import DNACryptDB


def cli_run(args):
    """Run a .dnacdb script file"""
    print(f"DNACryptDB - Running: {args.file}")
    print("="*70)
    
    try:
        db = DNACryptDB(config_file=args.config, verbose=True)
        results = db.execute_file(args.file)
        
        # Summary
        print("\n" + "="*70)
        print(f"Execution Summary")
        print("="*70)
        
        total = len(results)
        success = sum(1 for r in results if r.get('status') == 'success')
        errors = sum(1 for r in results if r.get('error'))
        comments = sum(1 for r in results if r.get('status') == 'comment')
        
        print(f"Total queries: {total}")
        print(f"✓ Success: {success}")
        print(f"✗ Errors: {errors}")
        print(f"# Comments: {comments}")
        print("="*70)
        
        db.close()
        
        return 0 if errors == 0 else 1
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


def cli_interactive(args):
    """Start interactive mode"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    DNACryptDB - Interactive Mode                     ║
║                Type 'help' for commands, 'exit' to quit              ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        db = DNACryptDB(config_file=args.config, verbose=True)
        print()
        
        # Interactive loop
        while True:
            try:
                query = input("dnacdb> ").strip()
                
                if query.lower() == 'exit' or query.lower() == 'quit':
                    print("\nGoodbye!")
                    break
                
                if query.lower() == 'help':
                    print_help()
                    continue
                
                if query.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                
                if not query:
                    continue
                
                # Execute query
                result = db.execute(query)
                
                # Pretty print result
                if result.get('status') == 'success':
                    if 'data' in result:
                        print(json.dumps(result['data'], indent=2, default=str))
                    else:
                        print(json.dumps(result, indent=2, default=str))
                elif result.get('error'):
                    print(f"✗ Error: {result['error']}")
                    if result.get('hint'):
                        print(f"  Hint: {result['hint']}")
                else:
                    print(json.dumps(result, indent=2, default=str))
                
                print()
                
            except KeyboardInterrupt:
                print("\n\nUse 'exit' to quit")
                continue
            except EOFError:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"✗ Error: {e}\n")
        
        db.close()
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("  Run 'dnacryptdb init' to create a configuration file.")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


def cli_init(args):
    """Initialize a new DNACryptDB configuration"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              DNACryptDB - Configuration Setup                        ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n[MySQL Configuration]")
    mysql_host = input("  Host (default: localhost): ").strip() or "localhost"
    mysql_user = input("  Username (default: root): ").strip() or "root"
    mysql_pass = input("  Password: ").strip()
    mysql_db = input("  Database name (default: dnacryptdb): ").strip() or "dnacryptdb"
    
    print("\n[MongoDB Configuration]")
    mongo_host = input("  Host (default: localhost): ").strip() or "localhost"
    mongo_port = input("  Port (default: 27017): ").strip() or "27017"
    mongo_db = input("  Database name (default: dnacryptdb): ").strip() or "dnacryptdb"
    mongo_user = input("  Username (leave empty for no auth): ").strip()
    
    # Build MongoDB URI
    if mongo_user:
        mongo_pass = input("  Password: ").strip()
        mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"
    else:
        mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/"
    
    print("\n[Neo4j Configuration]")
    neo4j_host = input("  Host (default: localhost): ").strip() or "localhost"
    neo4j_port = input("  Port (default: 7687): ").strip() or "7687"
    neo4j_user = input("  Username (default: neo4j): ").strip() or "neo4j"
    neo4j_pass = input("  Password (default: password): ").strip() or "password"
    neo4j_uri = f"bolt://{neo4j_host}:{neo4j_port}"
    
    # Create configuration
    config = {
        "mysql": {
            "host": mysql_host,
            "user": mysql_user,
            "password": mysql_pass,
            "database": mysql_db
        },
        "mongodb": {
            "uri": mongo_uri,
            "database": mongo_db
        },
        "neo4j": {
            "uri": neo4j_uri,
            "user": neo4j_user,
            "password": neo4j_pass
        }
    }
    
    # Save configuration
    config_file = args.output or "dnacdb.config.json"
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Configuration saved to: {config_file}")
    print(f"\nYou can now run:")
    print(f"  dnacryptdb run script.dnacdb")
    print(f"  dnacryptdb interactive")
    
    return 0


def print_help():
    """Print interactive mode help"""
    print("""
Available Commands:
  
  Create Structures:
    MAKE TABLE name WITH (field:type, ...)
    MAKE COLLECTION name
  
  Insert Data:
    PUT INTO target DATA {json}
  
  Query Data:
    FETCH FROM source WHERE condition
    FETCH FROM source ALL
  
  Update Data:
    CHANGE IN target SET field=value WHERE condition
  
  Delete Data:
    REMOVE FROM target WHERE condition
  
  Show Structures:
    SHOW TABLES
    SHOW COLLECTIONS
  
  Drop Structures:
    DROP name
  
  System Commands:
    help   - Show this help
    clear  - Clear screen
    exit   - Exit interactive mode

Data Types:
  int, float, text, date, datetime, bool

Examples:
  MAKE TABLE users WITH (name:text, age:int);
  PUT INTO users DATA {"name": "Alice", "age": 30};
  FETCH FROM users WHERE age > 25;
  CHANGE IN users SET age = 31 WHERE name = "Alice";
    """)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='dnacryptdb',
        description='DNACryptDB - Polyglot Database Command Line Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize configuration
  dnacryptdb init
  
  # Run a script file
  dnacryptdb run script.dnacdb
  
  # Start interactive mode
  dnacryptdb interactive
  
  # Use custom config file
  dnacryptdb run script.dnacdb -c myconfig.json

For more information, visit: https://github.com/yourusername/dnacryptdb
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser(
        'init', 
        help='Initialize database configuration'
    )
    init_parser.add_argument(
        '-o', '--output',
        help='Output config file (default: dnacdb.config.json)'
    )
    
    # Run command
    run_parser = subparsers.add_parser(
        'run',
        help='Run a .dnacdb script file'
    )
    run_parser.add_argument(
        'file',
        help='.dnacdb script file to execute'
    )
    run_parser.add_argument(
        '-c', '--config',
        default='dnacdb.config.json',
        help='Config file (default: dnacdb.config.json)'
    )
    
    # Interactive command
    interactive_parser = subparsers.add_parser(
        'interactive',
        help='Start interactive mode'
    )
    interactive_parser.add_argument(
        '-c', '--config',
        default='dnacdb.config.json',
        help='Config file (default: dnacdb.config.json)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate handler
    if args.command == 'init':
        return cli_init(args)
    elif args.command == 'run':
        return cli_run(args)
    elif args.command == 'interactive':
        return cli_interactive(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())