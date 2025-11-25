# Claims Agent ADK Agent


## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.x
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Configuration Setup

#### Using Local Environment Variables

1. Copy `.env.example` to create a new `.env` file in the backend directory
2. Update the `.env` file with your credentials and configuration:
3. Verify that all required environment variables are properly added

### Running the Agent

To run the Claims Agent:

```bash
python app.py
```

## Developer Guide - Local PostgreSQL Setup

This guide explains how to set up and manage PostgreSQL locally using Docker Compose for development purposes.

### Prerequisites

Before you begin, ensure you have the following installed on your development machine:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Project Structure

The relevant files for database setup are:

```
backend/
├── docker-compose.yml    # Docker Compose configuration
└── README.md            # This documentation
```

### PostgreSQL Docker Configuration

### Running PostgreSQL

1. Start the PostgreSQL container:
   ```bash
   docker-compose up -d
   ```

2. Verify the container is running:
   ```bash
   docker-compose ps
   ```

3. Stop and remove containers (including volumes):
   ```bash
   docker-compose down -v
   ```

4. Restart containers:
   ```bash
   docker-compose up -d
   ```

### Connecting to PostgreSQL

To connect to the PostgreSQL container and access the psql command line:

```bash
docker exec -it claims-postgres psql -U postgres -d claims_db
```

To exit the psql prompt:
```bash
\q
```

### Database Initialization and Schema Setup

1. Locate the database schema file:
   ```
   backend/init-sql/table.sql
   ```

2. Initialize the database schema using one of these methods:
   - Using pgAdmin:
     1. Connect to your database
     2. Open the Query Tool
     3. Load and execute the `table.sql` file

   - Using psql command line:
     ```bash
     psql -U postgres -d real_estate -f init-sql/table.sql
     ```

3. After manual data entries or modifications, run the following sequence fix commands:
   ```sql
   -- Fix sequence for users table
   SELECT setval(pg_get_serial_sequence('users', 'user_id'), 
          COALESCE((SELECT MAX(user_id) FROM users), 1), TRUE);

   -- Fix sequence for property_search_requests table
   SELECT setval(pg_get_serial_sequence('property_search_requests', 'property_search_request_id'), 
          COALESCE((SELECT MAX(property_search_request_id) FROM property_search_requests), 1), TRUE);

   -- Fix sequence for properties table
   SELECT setval(pg_get_serial_sequence('properties', 'property_id'), 
          COALESCE((SELECT MAX(property_id) FROM properties), 1), TRUE);

   -- Fix sequence for PropertyMaps table
   SELECT setval(pg_get_serial_sequence('PropertyMaps', 'map_id'), 
          COALESCE((SELECT MAX(map_id) FROM "PropertyMaps"), 1), TRUE);
   ```

   **Important**: Always run these sequence fix commands after making manual data entries in the database to maintain data integrity and avoid synchronization issues.

### Database Management Commands

#### Checking Tables and Objects

1. List all tables:
   ```sql
   \dt
   ```

2. List all database objects (tables, views, sequences):
   ```sql
   \d
   ```

#### Querying Data

1. Basic SELECT query:
   ```sql
   SELECT * FROM users;
   ```

2. Enable expanded display mode for better formatting:
   ```sql
   \x
   ```
   Toggle this mode on/off before running queries for different output formats.


## Project Structure

```
backend/
├── agents/              # Agent implementation files
├── database/           # Database repositories and connection management
├── init-sql/          # SQL initialization scripts
├── models/            # Data models and schemas
├── routes/            # API routes and endpoints
├── tests/             # Test files and configurations
├── tools/             # Utility tools (Bayut API, Maps, etc.)
├── utils/             # Utility functions and middleware
├── app.py            # Main application entry point
└── docker-compose.yml # Docker configuration
```

### Troubleshooting

If you encounter issues:

1. Check container logs:
   ```bash
   docker-compose logs postgres
   ```

2. Verify environment variables are properly set
3. Ensure all required ports are available
4. Check Google Cloud credentials if using Vertex AI
   ```bash
   netstat -an | findstr "5432"
   ```

3. Reset the database (warning: this will delete all data):
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```