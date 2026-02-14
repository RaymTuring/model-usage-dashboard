#!/bin/bash

# OpenClaw Model Usage Dashboard Server Startup Script

SERVER_SCRIPT="/Users/raymondturing/.openclaw/workspace/web/server.py"
PID_FILE="/Users/raymondturing/.openclaw/logs/dashboard_server.pid"
LOG_FILE="/Users/raymondturing/.openclaw/logs/dashboard_server.log"
PORT=8080

# Ensure log directory exists
mkdir -p "/Users/raymondturing/.openclaw/logs"

start_server() {
    echo "🚀 Starting OpenClaw Model Usage Dashboard Server..."
    
    # Check if server is already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "❌ Server is already running (PID: $PID)"
            echo "📊 Dashboard available at: http://localhost:$PORT"
            return 1
        else
            # Remove stale PID file
            rm -f "$PID_FILE"
        fi
    fi
    
    # Start the server in the background
    python3 "$SERVER_SCRIPT" > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    # Save PID to file
    echo "$SERVER_PID" > "$PID_FILE"
    
    # Wait a moment and check if server started successfully
    sleep 2
    if ps -p "$SERVER_PID" > /dev/null 2>&1; then
        echo "✅ Dashboard server started successfully!"
        echo "📊 Dashboard URL: http://localhost:$PORT"
        echo "📡 API Endpoint: http://localhost:$PORT/api/model-usage"
        echo "📋 Server PID: $SERVER_PID"
        echo "📝 Logs: $LOG_FILE"
    else
        echo "❌ Failed to start dashboard server"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_server() {
    echo "🛑 Stopping OpenClaw Model Usage Dashboard Server..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            rm -f "$PID_FILE"
            echo "✅ Dashboard server stopped"
        else
            echo "⚠️  Server was not running"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️  No PID file found, server may not be running"
    fi
}

status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ Dashboard server is running (PID: $PID)"
            echo "📊 Dashboard URL: http://localhost:$PORT"
            echo "📡 API Endpoint: http://localhost:$PORT/api/model-usage"
        else
            echo "❌ Dashboard server is not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ Dashboard server is not running"
    fi
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the dashboard server"
        echo "  stop     - Stop the dashboard server"
        echo "  restart  - Restart the dashboard server"
        echo "  status   - Check server status"
        echo ""
        echo "Dashboard will be available at: http://localhost:$PORT"
        exit 1
        ;;
esac