# Automaton Auditor

A toolkit for running a detective-style graph against a repository. It can install dependencies, spin up a backend and front end, and execute a diagnostic graph on a target repo URL.

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/leuel-a/automaton-auditor
   cd automaton-auditor
   ```

2. **Python environment**
   - Ensure you have Python 3.10+ installed.
   - Create a virtual environment and activate it:
     ```bash
     python -m venv venv
     source venv/bin/activate    # on Linux/macOS
     # or `venv\Scripts\activate` on Windows
     ```

3. **Install backend dependencies**
   This project uses **uv** as the Python dependency manager. With your virtual environment active, run:
   ```bash
   uv sync --frozen --no-dev
   ```
   This will install all packages pinned in `uv.lock` (generated from `pyproject.toml`).

4. **Install frontend dependencies**
   ```bash
   cd frontend
   pnpm install     # or `npm install` / `yarn` depending on your package manager
   cd ..
   ```

## Running the Application

### Backend

From the project root (with virtualenv activated):
```bash
# run the fastapi server
python backend/run_server.py
```
The backend listens on `http://localhost:8000` by default and exposes endpoints the frontend uses as well as CLI commands.

### Frontend (UI)

The frontend is built with Next.js. To get the best UI experience:

```bash
cd frontend
pnpm install             # or npm install / yarn install
pnpm run dev              # starts development server on port 3000
```

Once running, open your browser to `http://localhost:3000`. Use the forms to provide a repository URL and submit. The UI will communicate with the backend at `http://localhost:8000` and display the detective graph results in a user-friendly format.

### CLI Graph Execution (Testing)

To test the detective graph logic without the UI, use the CLI module. It accepts a `--target` parameter for the repository URL and prints results in the terminal.

```bash
# make sure virtualenv is active
python -m cli.main run-graph --target https://github.com/owner/repo.git
```

You can specify any public Git repository. The command will clone the repo locally, execute the graph, and output a summary report. For help or extra options run `python -m cli.main --help`.

## Notes

- Docker support is provided via the existing `Dockerfile` and `docker-compose.yml` if you prefer containerized workflows.
- Ensure your Python environment has all required packages; you can regenerate the lock file with Poetry or update `requirements.txt` if necessary.
