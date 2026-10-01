#!/usr/bin/env bash
# =============================================================================
# Cloud-Native Automated Compliance & Audit System (CACA)
# Universal Setup & Launch Script - Zero Dependencies Required
# =============================================================================
# This script creates a fully isolated environment and launches the platform.
# Works on Linux, macOS, and Windows (via WSL/Git Bash).
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
PROJECT_NAME="CACA - Compliance Audit System"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
BACKEND_PORT=8000
FRONTEND_PORT=3000
PYTHON_MIN_VERSION="3.10"
NODE_MIN_VERSION="18"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------
log() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*" >&2; }
step() { echo -e "\n${CYAN}${BOLD}▶ $*${NC}"; }
banner() {
    echo -e "${CYAN}"
    cat <<'EOF'
╔═══════════════════════════════════════════════════════════════════════╗
║  ☁️  Cloud-Native Automated Compliance & Audit System (CACA)          ║
║  🎓  Final Year Capstone Project  |  RegTech  |  AI + Serverless      ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

cleanup() {
    log "Shutting down services..."
    [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
    [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
    # Kill any child processes
    pkill -P $$ 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM EXIT

# -----------------------------------------------------------------------------
# Version Checking
# -----------------------------------------------------------------------------
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

check_python() {
    if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
        error "Python 3 not found. Please install Python ${PYTHON_MIN_VERSION}+"
        exit 1
    fi
    local py_cmd=$(command -v python3 || command -v python)
    local version=$($py_cmd --version 2>&1 | cut -d' ' -f2)
    if ! version_ge "$version" "$PYTHON_MIN_VERSION"; then
        error "Python ${version} found, but ${PYTHON_MIN_VERSION}+ required"
        exit 1
    fi
    echo "$py_cmd"
}

check_node() {
    if ! command -v node &>/dev/null; then
        error "Node.js not found. Please install Node ${NODE_MIN_VERSION}+"
        exit 1
    fi
    local version=$(node --version 2>&1 | sed 's/^v//')
    if ! version_ge "$version" "$NODE_MIN_VERSION"; then
        error "Node ${version} found, but ${NODE_MIN_VERSION}+ required"
        exit 1
    fi
    echo "node"
}

check_npm() {
    if ! command -v npm &>/dev/null; then
        error "npm not found. Please install npm"
        exit 1
    fi
    echo "npm"
}

# -----------------------------------------------------------------------------
# Virtual Environment
# -----------------------------------------------------------------------------
setup_venv() {
    local py_cmd="$1"
    step "Creating isolated Python environment..."
    if [[ -d "$VENV_DIR" ]]; then
        warn "Existing .venv found, recreating..."
        rm -rf "$VENV_DIR"
    fi
    "$py_cmd" -m venv "$VENV_DIR"
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    pip install --quiet --upgrade pip setuptools wheel >/dev/null 2>&1
    success "Virtual environment ready at .venv/"
}

install_python_deps() {
    step "Installing Python dependencies..."
    local req_file="$PROJECT_ROOT/backend/requirements.txt"
    if [[ ! -f "$req_file" ]]; then
        error "Requirements file not found: $req_file"
        exit 1
    fi
    # Use the venv pip directly to avoid activation issues
    "$VENV_DIR/bin/pip" install --quiet -r "$req_file" 2>&1 | tail -5
    success "Python packages installed"
}

# -----------------------------------------------------------------------------
# Frontend Setup
# -----------------------------------------------------------------------------
install_node_deps() {
    step "Installing Node.js dependencies..."
    cd "$PROJECT_ROOT/frontend"
    if [[ -f "package-lock.json" ]]; then
        "$NPM_CMD" ci --silent 2>&1 | tail -3
    else
        "$NPM_CMD" install --silent 2>&1 | tail -3
    fi
    success "Node packages installed"
}

# -----------------------------------------------------------------------------
# Database & Seeding
# -----------------------------------------------------------------------------
init_database() {
    step "Initializing database & seeding samples..."
    cd "$PROJECT_ROOT"
    "$VENV_DIR/bin/python" -c "
import sys
sys.path.insert(0, 'backend')
from backend.database import engine, Base
from backend.models import AuditDocument, ComplianceFinding, AuditReport
Base.metadata.create_all(bind=engine)
print('  Database schema created')
" 2>&1
    "$VENV_DIR/bin/python" -c "
import sys
sys.path.insert(0, 'backend')
from backend.main import seed_sample_documents
from backend.database import SessionLocal
db = SessionLocal()
try:
    result = seed_sample_documents(db)
    if result['seeded_files']:
        print(f'  Seeded: {len(result[\"seeded_files\"])} sample documents')
    else:
        print('  Samples already exist')
finally:
    db.close()
" 2>&1
    success "Database initialized with sample compliance documents"
}

# -----------------------------------------------------------------------------
# Service Launchers
# -----------------------------------------------------------------------------
start_backend() {
    step "Starting FastAPI Backend (port $BACKEND_PORT)..."
    cd "$PROJECT_ROOT"
    "$VENV_DIR/bin/python" -m uvicorn backend.main:app \
        --host 0.0.0.0 --port "$BACKEND_PORT" --log-level warning &
    BACKEND_PID=$!

    # Wait for backend health check
    local max_wait=30
    for ((i=1; i<=max_wait; i++)); do
        if curl -s "http://localhost:$BACKEND_PORT/" >/dev/null 2>&1; then
            success "Backend ready at http://localhost:$BACKEND_PORT"
            success "API Documentation: http://localhost:$BACKEND_PORT/docs"
            return 0
        fi
        sleep 0.5
    done
    error "Backend failed to start within ${max_wait}s"
    exit 1
}

start_frontend() {
    step "Starting Next.js Frontend (port $FRONTEND_PORT)..."
    cd "$PROJECT_ROOT/frontend"
    "$NPM_CMD" run dev &
    FRONTEND_PID=$!

    # Wait for frontend
    local max_wait=20
    for ((i=1; i<=max_wait; i++)); do
        if curl -s "http://localhost:$FRONTEND_PORT/" >/dev/null 2>&1; then
            success "Frontend ready at http://localhost:$FRONTEND_PORT"
            return 0
        fi
        sleep 1
    done
    warn "Frontend may still be compiling... check http://localhost:$FRONTEND_PORT"
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
main() {
    banner
    log "Project: $PROJECT_NAME"
    log "Root: $PROJECT_ROOT"

    # Check prerequisites
    step "Checking prerequisites..."
    PY_CMD=$(check_python)
    NODE_CMD=$(check_node)
    NPM_CMD=$(check_npm)
    success "Python: $($PY_CMD --version)"
    success "Node: $(node --version)"
    success "npm: $(npm --version)"

    # Setup environment
    setup_venv "$PY_CMD"
    install_python_deps
    install_node_deps
    init_database

    # Launch services
    start_backend
    start_frontend

    # Display access info
    echo -e "\n${GREEN}${BOLD}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  🚀  PLATFORM RUNNING  🚀${NC}"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "  ${CYAN}📊 Dashboard:${NC}      http://localhost:$FRONTEND_PORT"
    echo -e "  ${CYAN}📚 API Docs:${NC}       http://localhost:$BACKEND_PORT/docs"
    echo -e "  ${CYAN}🔌 API Base:${NC}       http://localhost:$BACKEND_PORT/api"
    echo -e "  ${CYAN}📁 Sample Docs:${NC}    POST http://localhost:$BACKEND_PORT/api/seed-samples"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "\n  ${YELLOW}Press Ctrl+C to stop all services${NC}\n"

    # Keep script running
    wait $BACKEND_PID $FRONTEND_PID
}

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
main "$@"
