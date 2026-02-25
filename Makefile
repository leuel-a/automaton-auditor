PYTHON = python3
DOCKER = docker
NPM = npm --prefix frontend

cli:
	$(PYTHON) ./cli/main.py

dev: dev-frontend dev-backend

dev-frontend:
	$(NPM) run dev

dev-backend:
	$(PYTHON) ./backend/run_server.py
