#!/usr/bin/env python3

import os
import json
import re
import uuid
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse


class RemoteControlManager:
    """Manages remote control sessions and command queues."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions = {}
        self._command_queue = []

    def create_session(self, client_name=None):
        session_id = str(uuid.uuid4())[:8]
        with self._lock:
            self._sessions[session_id] = {
                'id': session_id,
                'client_name': client_name or f'remote-{session_id}',
                'connected_at': datetime.now().isoformat(),
                'last_heartbeat': datetime.now().isoformat(),
                'status': 'connected'
            }
        return self._sessions[session_id]

    def disconnect_session(self, session_id):
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['status'] = 'disconnected'
                return True
        return False

    def get_sessions(self):
        with self._lock:
            return list(self._sessions.values())

    def get_session(self, session_id):
        with self._lock:
            return self._sessions.get(session_id)

    def heartbeat(self, session_id):
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['last_heartbeat'] = datetime.now().isoformat()
                return True
        return False

    def enqueue_command(self, session_id, command, params=None):
        with self._lock:
            if session_id not in self._sessions:
                return None
            if self._sessions[session_id]['status'] != 'connected':
                return None
            cmd = {
                'id': str(uuid.uuid4())[:8],
                'session_id': session_id,
                'command': command,
                'params': params or {},
                'timestamp': datetime.now().isoformat(),
                'status': 'queued'
            }
            self._command_queue.append(cmd)
            return cmd

    def get_pending_commands(self):
        with self._lock:
            pending = [c for c in self._command_queue if c['status'] == 'queued']
            for c in pending:
                c['status'] = 'delivered'
            return pending

    def get_command_history(self, limit=20):
        with self._lock:
            return self._command_queue[-limit:]


# Global remote control manager
remote_control = RemoteControlManager()

class DashboardRequestHandler(BaseHTTPRequestHandler):
    
    VALID_COMMANDS = {'refresh', 'set-refresh-interval', 'highlight-agent', 'clear-highlight', 'scroll-to-top'}

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/' or parsed_path.path == '/dashboard':
            self.serve_dashboard()
        elif parsed_path.path == '/api/model-usage':
            self.serve_model_usage_api()
        elif parsed_path.path == '/api/remote-control':
            self.handle_remote_control_get()
        elif parsed_path.path == '/api/remote-control/commands':
            self.handle_get_pending_commands()
        elif parsed_path.path.startswith('/static/'):
            self.serve_static_file(parsed_path.path)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/remote-control/connect':
            self.handle_remote_connect()
        elif parsed_path.path == '/api/remote-control/disconnect':
            self.handle_remote_disconnect()
        elif parsed_path.path == '/api/remote-control/command':
            self.handle_remote_command()
        elif parsed_path.path == '/api/remote-control/heartbeat':
            self.handle_remote_heartbeat()
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        dashboard_path = '/Users/raymondturing/.openclaw/workspace/web/dashboard.html'
        
        try:
            with open(dashboard_path, 'r') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404, "Dashboard not found")
    
    def serve_model_usage_api(self):
        """Serve model usage data as JSON API"""
        dashboard_md_path = '/Users/raymondturing/.openclaw/workspace/MODEL_USAGE_DASHBOARD.md'
        
        try:
            # Parse the markdown dashboard file
            agents_data = self.parse_dashboard_markdown(dashboard_md_path)
            
            response_data = {
                'agents': agents_data,
                'timestamp': datetime.now().isoformat(),
                'total_agents': len(agents_data)
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_error(500, f"Error parsing dashboard data: {str(e)}")
    
    def parse_dashboard_markdown(self, file_path):
        """Parse the markdown dashboard file to extract agent data"""
        agents = []
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the table section
        lines = content.split('\n')
        in_table = False
        
        for line in lines:
            # Skip header and separator rows
            if '|----' in line or line.startswith('| Agent |'):
                in_table = True
                continue
            
            # Parse data rows
            if in_table and line.startswith('|') and '@' in line:
                parts = [part.strip() for part in line.split('|') if part.strip()]
                
                if len(parts) >= 6:
                    agent_data = {
                        'name': parts[0],
                        'model': parts[1],
                        'timestamp': parts[2],
                        'inputTokens': int(parts[3]) if parts[3].isdigit() else 0,
                        'outputTokens': int(parts[4]) if parts[4].isdigit() else 0,
                        'cost': float(parts[5].replace('$', '')) if parts[5].replace('$', '').replace('.', '').isdigit() else 0.0,
                        'status': parts[6] if len(parts) > 6 else 'Available'
                    }
                    agents.append(agent_data)
            
            # Stop parsing after the table
            elif in_table and not line.startswith('|'):
                break
        
        return agents
    
    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode())

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def handle_remote_control_get(self):
        """GET /api/remote-control - Return remote control status and sessions."""
        sessions = remote_control.get_sessions()
        active = [s for s in sessions if s['status'] == 'connected']
        self._send_json({
            'status': 'ok',
            'active_sessions': len(active),
            'sessions': sessions,
            'available_commands': list(self.VALID_COMMANDS),
            'timestamp': datetime.now().isoformat()
        })

    def handle_remote_connect(self):
        """POST /api/remote-control/connect - Create a new remote session."""
        try:
            body = self._read_json_body()
        except (json.JSONDecodeError, ValueError):
            body = {}
        session = remote_control.create_session(body.get('client_name'))
        self._send_json({
            'status': 'connected',
            'session': session
        }, 201)

    def handle_remote_disconnect(self):
        """POST /api/remote-control/disconnect - Disconnect a session."""
        try:
            body = self._read_json_body()
        except (json.JSONDecodeError, ValueError):
            self._send_json({'error': 'Invalid request body'}, 400)
            return
        session_id = body.get('session_id')
        if not session_id:
            self._send_json({'error': 'session_id is required'}, 400)
            return
        if remote_control.disconnect_session(session_id):
            self._send_json({'status': 'disconnected', 'session_id': session_id})
        else:
            self._send_json({'error': 'Session not found'}, 404)

    def handle_remote_command(self):
        """POST /api/remote-control/command - Send a command to the dashboard."""
        try:
            body = self._read_json_body()
        except (json.JSONDecodeError, ValueError):
            self._send_json({'error': 'Invalid request body'}, 400)
            return
        session_id = body.get('session_id')
        command = body.get('command')
        if not session_id or not command:
            self._send_json({'error': 'session_id and command are required'}, 400)
            return
        if command not in self.VALID_COMMANDS:
            self._send_json({
                'error': f'Unknown command: {command}',
                'available_commands': list(self.VALID_COMMANDS)
            }, 400)
            return
        cmd = remote_control.enqueue_command(session_id, command, body.get('params'))
        if cmd:
            self._send_json({'status': 'queued', 'command': cmd})
        else:
            self._send_json({'error': 'Session not found or not connected'}, 404)

    def handle_remote_heartbeat(self):
        """POST /api/remote-control/heartbeat - Keep a session alive."""
        try:
            body = self._read_json_body()
        except (json.JSONDecodeError, ValueError):
            self._send_json({'error': 'Invalid request body'}, 400)
            return
        session_id = body.get('session_id')
        if not session_id:
            self._send_json({'error': 'session_id is required'}, 400)
            return
        if remote_control.heartbeat(session_id):
            self._send_json({'status': 'ok', 'session_id': session_id})
        else:
            self._send_json({'error': 'Session not found'}, 404)

    def handle_get_pending_commands(self):
        """GET /api/remote-control/commands - Poll for pending commands."""
        commands = remote_control.get_pending_commands()
        self._send_json({'commands': commands})

    def serve_static_file(self, path):
        """Serve static files"""
        # For now, we don't have static files
        self.send_error(404, "Static file not found")
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[{datetime.now()}] {format % args}")

def run_server(port=8080):
    """Run the dashboard HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    
    print(f"🚀 OpenClaw Model Usage Dashboard")
    print(f"📊 Server running at: http://localhost:{port}")
    print(f"🔗 Dashboard URL: http://localhost:{port}/dashboard")
    print(f"📡 API Endpoint: http://localhost:{port}/api/model-usage")
    print(f"🎮 Remote Control: http://localhost:{port}/api/remote-control")
    print(f"⏹️  Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server(8080)