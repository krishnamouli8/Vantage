"""WebSocket handler for real-time metrics."""

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
from api.database import get_timeseries_data

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics."""
    await websocket.accept()
    active_connections.add(websocket)
    
    try:
        while True:
            # Send latest metrics every 5 seconds
            await asyncio.sleep(5)
            
            metrics = get_timeseries_data(time_range=60)  # Last minute
            await websocket.send_json({"type": "metrics", "data": metrics})
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)
