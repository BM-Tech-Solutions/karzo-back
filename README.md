# Karzo Backend

This is a FastAPI backend with PostgreSQL and Alembic migrations, containerized using Docker.

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/)

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/karzo-back.git
   cd karzo-back
   ```

2. **Build and run the Docker containers:**

   ```bash
   docker-compose up --build
   ```

3. **Apply Alembic migrations:**

   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Access the API:**

   - The FastAPI app will be available at http://localhost:8000 .

