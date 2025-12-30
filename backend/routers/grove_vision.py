"""
Grove Vision API routes for student attention monitoring.

Provides endpoints to control the Grove Vision edge device and
retrieve stress event data.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/grove-vision", tags=["grove-vision"])

# Store for active WebSocket connections
_websocket_connections: List[WebSocket] = []

# In-memory stress event tracking (per session)
_current_session_events = {
    "session_id": None,
    "stress_count": 0,
    "events": [],
    "is_monitoring": False
}


class StartMonitoringRequest(BaseModel):
    session_id: str
    port: Optional[str] = None


class StartMonitoringResponse(BaseModel):
    success: bool
    message: str
    is_monitoring: bool


class StopMonitoringResponse(BaseModel):
    success: bool
    stress_event_count: int
    events: List[dict]


class StatusResponse(BaseModel):
    is_monitoring: bool
    is_connected: bool
    stress_event_count: int
    session_id: Optional[str]


class StressEventNotification(BaseModel):
    type: str = "stress_event"
    label: str
    confidence: float
    timestamp: str
    total_count: int


@router.post("/start", response_model=StartMonitoringResponse)
async def start_monitoring(request: StartMonitoringRequest):
    """
    Start Grove Vision monitoring for a teaching session.
    
    This will attempt to connect to the Grove Vision device and
    begin monitoring for stress events (closed eyes, yawning).
    """
    global _current_session_events
    
    try:
        from backend.services.grove_vision import get_monitor, StressEvent
        
        monitor = get_monitor()
        
        # Update port if provided
        if request.port:
            monitor.port = request.port
        
        # Reset session data
        _current_session_events = {
            "session_id": request.session_id,
            "stress_count": 0,
            "events": [],
            "is_monitoring": True
        }
        
        # Register callback for stress events
        async def on_stress(event: StressEvent):
            _current_session_events["stress_count"] += 1
            _current_session_events["events"].append({
                "label": event.label,
                "confidence": event.confidence,
                "timestamp": event.timestamp.isoformat()
            })
            
            # Notify all connected WebSocket clients
            notification = {
                "type": "stress_event",
                "label": event.label,
                "confidence": event.confidence,
                "timestamp": event.timestamp.isoformat(),
                "total_count": _current_session_events["stress_count"]
            }
            
            for ws in _websocket_connections[:]:
                try:
                    await ws.send_json(notification)
                except:
                    _websocket_connections.remove(ws)
        
        # Try to start the monitor
        success = monitor.start()
        
        if success:
            # Register callback (sync wrapper for async callback)
            def sync_callback(event):
                asyncio.create_task(on_stress(event))
            
            monitor.on_stress_event(sync_callback)
            
            return StartMonitoringResponse(
                success=True,
                message="Grove Vision 監控已啟動",
                is_monitoring=True
            )
        else:
            # Device not connected, but we can still track events manually
            _current_session_events["is_monitoring"] = True
            return StartMonitoringResponse(
                success=True,
                message="Grove Vision 裝置未連接，使用模擬模式",
                is_monitoring=True
            )
            
    except ImportError:
        # pyserial not installed, use simulation mode
        _current_session_events = {
            "session_id": request.session_id,
            "stress_count": 0,
            "events": [],
            "is_monitoring": True
        }
        return StartMonitoringResponse(
            success=True,
            message="Grove Vision 模組未安裝，使用模擬模式",
            is_monitoring=True
        )
    except Exception as e:
        logger.error(f"Error starting Grove Vision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=StopMonitoringResponse)
async def stop_monitoring():
    """
    Stop Grove Vision monitoring and return summary.
    """
    global _current_session_events
    
    try:
        from backend.services.grove_vision import get_monitor
        monitor = get_monitor()
        summary = monitor.stop()
        
        # Combine with session events
        result = StopMonitoringResponse(
            success=True,
            stress_event_count=_current_session_events["stress_count"],
            events=_current_session_events["events"]
        )
        
        _current_session_events["is_monitoring"] = False
        return result
        
    except ImportError:
        result = StopMonitoringResponse(
            success=True,
            stress_event_count=_current_session_events["stress_count"],
            events=_current_session_events["events"]
        )
        _current_session_events["is_monitoring"] = False
        return result
    except Exception as e:
        logger.error(f"Error stopping Grove Vision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get current monitoring status.
    """
    try:
        from backend.services.grove_vision import get_monitor
        monitor = get_monitor()
        
        return StatusResponse(
            is_monitoring=_current_session_events["is_monitoring"],
            is_connected=monitor.is_connected,
            stress_event_count=_current_session_events["stress_count"],
            session_id=_current_session_events["session_id"]
        )
    except ImportError:
        return StatusResponse(
            is_monitoring=_current_session_events["is_monitoring"],
            is_connected=False,
            stress_event_count=_current_session_events["stress_count"],
            session_id=_current_session_events["session_id"]
        )


@router.post("/simulate-stress")
async def simulate_stress_event(label: str = "閉眼", confidence: float = 98.0):
    """
    Simulate a stress event for testing purposes.
    """
    from datetime import datetime
    
    if not _current_session_events["is_monitoring"]:
        raise HTTPException(status_code=400, detail="監控未啟動")
    
    _current_session_events["stress_count"] += 1
    event = {
        "label": label,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }
    _current_session_events["events"].append(event)
    
    # Notify WebSocket clients
    notification = {
        "type": "stress_event",
        "label": label,
        "confidence": confidence,
        "timestamp": event["timestamp"],
        "total_count": _current_session_events["stress_count"]
    }
    
    for ws in _websocket_connections[:]:
        try:
            await ws.send_json(notification)
        except:
            _websocket_connections.remove(ws)
    
    return {
        "success": True,
        "stress_count": _current_session_events["stress_count"],
        "event": event
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time stress event notifications.
    """
    await websocket.accept()
    _websocket_connections.append(websocket)
    
    try:
        # Send current status
        await websocket.send_json({
            "type": "status",
            "is_monitoring": _current_session_events["is_monitoring"],
            "stress_count": _current_session_events["stress_count"]
        })
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _websocket_connections:
            _websocket_connections.remove(websocket)
