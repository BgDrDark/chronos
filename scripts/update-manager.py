#!/usr/bin/env python3
"""
update-manager.py - HTTP manager for Chronos update requests

Runs on the HOST machine. Receives update requests from the backend container
and executes update.sh safely outside the container.

Usage:
    python3 update-manager.py [--port 14241] [--project-dir /path/to/chronos]
                              [--api-key-file /path/to/update.key]
"""

import argparse
import hmac
import json
import logging
import os
import subprocess
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [update-manager] %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global deploy status
_deploy_status = {
    "is_deploying": False,
    "status": "idle",
    "progress": "",
    "version": None,
    "output": "",
    "timestamp": None,
}
_deploy_lock = threading.Lock()


def _update_status(status, progress, output="", version=None):
    with _deploy_lock:
        _deploy_status["status"] = status
        _deploy_status["progress"] = progress
        _deploy_status["version"] = version
        if output:
            _deploy_status["output"] = output
        _deploy_status["timestamp"] = datetime.now().isoformat()


def _run_deploy(project_dir, version):
    """Execute update.sh in background thread"""
    full_output = []

    try:
        script_path = os.path.join(project_dir, "scripts", "update.sh")
        if not os.path.exists(script_path):
            _update_status("failed", f"update.sh not found at {script_path}")
            return

        cmd = ["bash", script_path]
        if version:
            cmd.extend(["--version", version])

        _update_status("running", "Starting deployment...", "", version)
        logger.info(f"Starting deploy: version={version}")

        env = os.environ.copy()
        env["PROJECT_DIR"] = project_dir

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=project_dir,
            env=env,
        )
        assert process.stdout is not None
        for line in iter(process.stdout.readline, ""):
            if line:
                line = line.rstrip()
                full_output.append(line)
                logger.info(f"deploy: {line}")

                if "[0/7]" in line:
                    _update_status("running", "Acquiring DB lock...", "\n".join(full_output[-50:]), version)
                elif "[1/7]" in line:
                    _update_status("running", "Health check", "\n".join(full_output[-50:]), version)
                elif "[2/7]" in line:
                    _update_status("running", "Creating backup...", "\n".join(full_output[-50:]), version)
                elif "[3/7]" in line:
                    _update_status("running", "Pulling images...", "\n".join(full_output[-50:]), version)
                elif "[4/7]" in line:
                    _update_status("running", "Running migrations...", "\n".join(full_output[-50:]), version)
                elif "[5/7]" in line:
                    _update_status("running", "Deploying backend...", "\n".join(full_output[-50:]), version)
                elif "[6/7]" in line:
                    _update_status("running", "Deploying frontend...", "\n".join(full_output[-50:]), version)
                elif "[7/7]" in line:
                    _update_status("running", "Final health check...", "\n".join(full_output[-50:]), version)
                elif "Deploy Complete" in line:
                    _update_status("success", "Deployment complete", "\n".join(full_output[-50:]), version)
                elif "Rolling back" in line:
                    _update_status("rolled_back", "Rolled back", "\n".join(full_output[-50:]), version)

        process.wait()
        returncode = process.returncode

        if returncode == 0:
            _update_status("success", "Deployment complete", "\n".join(full_output[-100:]), version)
            logger.info(f"Deploy complete: {version}")
        else:
            is_rollback = "Rollback" in "\n".join(full_output)
            final = "rolled_back" if is_rollback else "failed"
            _update_status(final, f"Failed (exit code {returncode})", "\n".join(full_output[-100:]), version)
            logger.error(f"Deploy failed: exit code {returncode}")

    except Exception as e:
        logger.error(f"Deploy error: {e}")
        _update_status("failed", f"Error: {str(e)}", "\n".join(full_output[-50:]), version)
    finally:
        with _deploy_lock:
            _deploy_status["is_deploying"] = False


class UpdateHandler(BaseHTTPRequestHandler):
    """HTTP handler for update requests"""

    api_key_file = None
    project_dir = None

    def log_message(self, format, *args):
        logger.info(format % args)

    def _load_api_key(self):
        """Read API key from file on every request (supports rotation)"""
        if self.api_key_file and os.path.exists(self.api_key_file):
            with open(self.api_key_file, "r") as f:
                return f.read().strip()
        return None

    def _verify_api_key(self):
        """Verify UpdateKey header"""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("UpdateKey "):
            provided_key = auth[len("UpdateKey "):]
            expected_key = self._load_api_key()
            if expected_key and hmac.compare_digest(provided_key, expected_key):
                return True
        return False

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok", "service": "update-manager"})
        elif self.path == "/deploy-status":
            with _deploy_lock:
                self._send_json(dict(_deploy_status))
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/deploy":
            if not self._verify_api_key():
                self._send_json({"error": "Unauthorized"}, 401)
                return

            with _deploy_lock:
                if _deploy_status["is_deploying"]:
                    self._send_json({"error": "Update already in progress"}, 409)
                    return

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""

            version = None
            if body:
                try:
                    data = json.loads(body)
                    version = data.get("version")
                except json.JSONDecodeError:
                    pass

            with _deploy_lock:
                _deploy_status["is_deploying"] = True

            thread = threading.Thread(
                target=_run_deploy,
                args=(self.project_dir, version),
                daemon=True
            )
            thread.start()

            self._send_json({
                "status": "started",
                "message": f"Update started{' to ' + version if version else ''}",
                "version": version,
                "timestamp": datetime.now().isoformat()
            })
        else:
            self._send_json({"error": "Not found"}, 404)


def main():
    parser = argparse.ArgumentParser(description="Chronos Update Manager")
    parser.add_argument("--port", type=int, default=14241, help="Port to listen on (default: 14241)")
    parser.add_argument("--project-dir", type=str, required=True, help="Path to Chronos project directory")
    parser.add_argument("--api-key-file", type=str, default=None, help="Path to file containing update API key")
    args = parser.parse_args()

    UpdateHandler.api_key_file = args.api_key_file
    UpdateHandler.project_dir = args.project_dir

    logger.info(f"Starting update-manager on port {args.port}")
    logger.info(f"Project directory: {args.project_dir}")
    logger.info(f"API key file: {args.api_key_file or 'NOT SET (no auth)'}")

    server = HTTPServer(("0.0.0.0", args.port), UpdateHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down update-manager...")
        server.shutdown()


if __name__ == "__main__":
    main()
