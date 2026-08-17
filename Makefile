.PHONY: up down build logs restart clean

# Start all services
up:
	docker compose up -d

# Start all services and force rebuild
build:
	docker compose up -d --build

# Stop all services
down:
	docker compose down

# View logs for all services
logs:
	docker compose logs -f

# Restart all services
restart:
	docker compose restart

# Remove containers, networks, volumes, and images created by up
clean:
	docker compose down -v --rmi all
