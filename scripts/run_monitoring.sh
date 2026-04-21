#!/bin/bash
# Unified Monitoring Script for WorkingTime
# Runs health checks, performance tests, and system validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default values
MODE="all"
JSON_OUTPUT=false
WATCH_MODE=false
INTERVAL=60

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --health          Run health check only"
    echo "  --performance     Run performance tests only"
    echo "  --system          Run system validation only"
    echo "  --all             Run all checks (default)"
    echo "  --json            Output as JSON"
    echo "  --watch           Run in watch mode (continuous)"
    echo "  --interval SECS    Watch mode interval (default: 60)"
    echo "  -h, --help        Show this help"
    echo ""
    exit 0
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        (--health) MODE="health"; shift ;;
        (--performance) MODE="performance"; shift ;;
        (--system) MODE="system"; shift ;;
        (--all) MODE="all"; shift ;;
        (--json) JSON_OUTPUT=true; shift ;;
        (--watch) WATCH_MODE=true; shift ;;
        (--interval) INTERVAL="$2"; shift 2 ;;
        (-h|--help) usage ;;
        (*) echo "Unknown option: $1"; usage ;;
    esac
done

cd "$PROJECT_ROOT"

echo ""
echo "======================================"
echo -e "${CYAN}🔍 WorkingTime Unified Monitoring${NC}"
echo "======================================"
echo ""

# Run system validation
run_system_check() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📋 System Validation${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if bash "$SCRIPT_DIR/test_system.sh"; then
        log_success "System validation passed"
        return 0
    else
        log_error "System validation failed"
        return 1
    fi
}

# Run health check
run_health_check() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🏥 Health Check${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local cmd="python3 $SCRIPT_DIR/health_monitor.py"
    [ "$JSON_OUTPUT" = true ] && cmd="$cmd --json"
    [ "$WATCH_MODE" = true ] && cmd="$cmd --watch --interval $INTERVAL"
    
    if $cmd; then
        log_success "Health check passed"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 2 ]; then
            log_error "Health check: CRITICAL issues found"
        elif [ $exit_code -eq 1 ]; then
            log_warn "Health check: Warnings found"
        fi
        return $exit_code
    fi
}

# Run performance tests
run_performance_check() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}⚡ Performance Tests${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if python3 "$SCRIPT_DIR/performance_testing.py"; then
        log_success "Performance tests passed"
        return 0
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Main execution
main() {
    local exit_code=0
    
    case $MODE in
        (system)
            run_system_check
            exit_code=$?
            ;;
        (health)
            run_health_check
            exit_code=$?
            ;;
        (performance)
            run_performance_check
            exit_code=$?
            ;;
        (all)
            run_system_check || exit_code=1
            echo ""
            run_health_check || exit_code=1
            echo ""
            run_performance_check || exit_code=1
            ;;
    esac
    
    echo ""
    echo "======================================"
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ All checks passed!${NC}"
    else
        echo -e "${RED}❌ Some checks failed (exit code: $exit_code)${NC}"
    fi
    echo "======================================"
    
    exit $exit_code
}

main
