#!/usr/bin/env bash
set -euo pipefail

# Cloud-Native Automated Compliance and Audit System
# Zero-dependency setup script - creates isolated environment and runs everything

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_CMD="${PYTHON_CMD:-python3}"
NODE_CMD="${NODE_CMD:-node}"
NPM_CMD="${NPM_CMD:-npm}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step() { echo -e "\n${CYAN}▶${NC} $*"; }

cleanup() {
    log_info "Shutting down..."
    if [[ -n "${BACKEND_PID:-}" ]]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
    if [[ -n "${FRONTEND_PID:-}" ]]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
    exit 0
}
trap cleanup INT TERM EXIT

check_command() {
    if ! command -v "$1" &>/dev/null; then
        log_error "$1 not found. Please install $1 and try again."
        exit 1
    fi
}

main() {
    echo -e "${CYAN}"
    cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║  Cloud-Native Automated Compliance & Audit System            ║
║  Zero-Setup Launch Script                                     ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    log_step "Checking prerequisites..."
    check_command "$PYTHON_CMD"
    check_command "$NODE_CMD"
    check_command "$NPM_CMD"

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    NODE_VERSION=$($NODE_CMD --version 2>&1)
    log_success "Python $PYTHON_VERSION | Node $NODE_VERSION"

    log_step "Creating isolated Python environment..."
    if [[ -d "$VENV_DIR" ]]; then
        log_warn "Existing .venv found, removing..."
        rm -rf "$VENV_DIR"
    fi
    $PYTHON_CMD -m venv "$VENV_DIR"
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    pip install --quiet --upgrade pip setuptools wheel

    log_step "Installing Python dependencies..."
    pip install --quiet -r "$PROJECT_ROOT/backend/requirements.txt"
    pip install --quiet -r "$PROJECT_ROOT/requirements-dev.txt" 2>/dev/null || true
    log_success "Python packages installed"

    log_step "Installing Node.js dependencies..."
    cd "$PROJECT_ROOT/frontend"
    $NPM_CMD ci --silent 2>/dev/null || $NPM_CMD install --silent
    log_success "Node packages installed"

    log_step "Initializing database & seeding samples..."
    cd "$PROJECT_ROOT"
    $VENV_DIR/bin/python -c "
import sys
sys.path.insert(0, 'backend')
from backend.database import engine, Base
from backend.models import AuditDocument, ComplianceFinding, AuditReport
Base.metadata.create_all(bind=engine)
print('Database schema created')
"

    $VENV_DIR/bin/python -c "
import sys
sys.path.insert(0, 'backend')
from backend.main import seed_sample_documents
from backend.database import SessionLocal
db = SessionLocal()
try:
    result = seed_sample_documents(db)
    print(f'Seeded: {result[\"seeded_files\"]}')
finally:
    db.close()
"

    log_step "Starting FastAPI Backend (port 8000)..."
    cd "$PROJECT_ROOT"
    $VENV_DIR/bin/python -m uvicorn backend.main:app \
        --host 0.0.0.0 --port 8000 --log-level warning &
    BACKEND_PID=$!

    # Wait for backend to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8000/ >/dev/null 2>&1; then
            log_success "Backend ready at http://localhost:8000"
            break
        fi
        sleep 0.5
    done

    log_step "Starting Next.js Frontend (port 3000)..."
    cd "$PROJECT_ROOT/frontend"
    $NPM_CMD run dev &
    FRONTEND_PID=$!

    sleep 3
    log_success "Frontend ready at http://localhost:3000"

    echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Platform Running!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "  ${CYAN}Dashboard:${NC}     http://localhost:3000"
    echo -e "  ${CYAN}API Docs:${NC}      http://localhost:8000/docs"
    echo -e "  ${CYAN}API Base:${NC}      http://localhost:8000/api"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop all services\n"

    wait $BACKEND_PID $FRONTEND_PID
}

main "$@"
