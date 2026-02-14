#!/usr/bin/env python3

import os
import json
import re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

class DashboardRequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/dashboard':
            self.serve_dashboard()
        elif parsed_path.path == '/api/model-usage':
            self.serve_model_usage_api()
        elif parsed_path.path.startswith('/static/'):
            self.serve_static_file(parsed_path.path)
        else:
            self.send_error(404, "Not Found")
    
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
    print(f"⏹️  Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server(8080)