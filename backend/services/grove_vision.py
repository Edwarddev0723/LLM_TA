"""
Grove Vision Module - Edge device integration for student attention monitoring.

Monitors student attention through eye/yawn detection using Grove Vision AI.
"""
import serial
import json
import threading
import time
import logging
import os
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Setup file logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
os.makedirs(LOG_DIR, exist_ok=True)

# Create main logger for Grove Vision (all logs)
logger = logging.getLogger('grove_vision')
logger.setLevel(logging.DEBUG)

# File handler for ALL logs - rotating log files
all_log_file = os.path.join(LOG_DIR, 'grove_vision.log')
all_file_handler = RotatingFileHandler(
    all_log_file,
    maxBytes=5*1024*1024,  # 5MB per file
    backupCount=5,
    encoding='utf-8'
)
all_file_handler.setLevel(logging.DEBUG)
all_file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
all_file_handler.setFormatter(all_file_formatter)
logger.addHandler(all_file_handler)

# Create separate logger for EVENTS only
event_logger = logging.getLogger('grove_vision.events')
event_logger.setLevel(logging.INFO)
event_logger.propagate = False  # Don't propagate to parent logger

# File handler for EVENTS only
events_log_file = os.path.join(LOG_DIR, 'grove_vision_events.log')
events_file_handler = RotatingFileHandler(
    events_log_file,
    maxBytes=5*1024*1024,  # 5MB per file
    backupCount=5,
    encoding='utf-8'
)
events_file_handler.setLevel(logging.INFO)
events_file_formatter = logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
events_file_handler.setFormatter(events_file_formatter)
event_logger.addHandler(events_file_handler)

# Console handler for main logger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Detection labels
CLASS_NAMES = ["閉眼", "睜眼", "打哈欠", "不打哈欠"]

# Stress event labels (labels that indicate lack of attention)
STRESS_LABELS = ["閉眼", "打哈欠"]

# Confidence threshold for triggering stress event
CONFIDENCE_THRESHOLD = 95.0


@dataclass
class DetectionResult:
    """Result of a single detection."""
    label: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    is_stress_event: bool = False


@dataclass
class StressEvent:
    """A recorded stress event."""
    label: str
    confidence: float
    timestamp: datetime


class GroveVisionMonitor:
    """
    Grove Vision AI monitor for student attention detection.
    
    Connects to Grove Vision edge device via serial port and monitors
    for signs of inattention (closed eyes, yawning).
    """
    
    def __init__(
        self,
        port: str = '/dev/cu.usbmodem578D0264891',
        baudrate: int = 921600,
        confidence_threshold: float = CONFIDENCE_THRESHOLD
    ):
        self.port = port
        self.baudrate = baudrate
        self.confidence_threshold = confidence_threshold
        
        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Stress event tracking
        self._stress_events: List[StressEvent] = []
        self._stress_callbacks: List[Callable[[StressEvent], None]] = []
        
        # Last detection for debouncing
        self._last_stress_time: Optional[datetime] = None
        self._debounce_seconds = 3.0  # Minimum seconds between stress events
        
        # Connection status
        self._connected = False
        self._last_error: Optional[str] = None
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    @property
    def stress_event_count(self) -> int:
        return len(self._stress_events)
    
    @property
    def stress_events(self) -> List[StressEvent]:
        return self._stress_events.copy()
    
    def on_stress_event(self, callback: Callable[[StressEvent], None]) -> None:
        """Register a callback for stress events."""
        self._stress_callbacks.append(callback)
    
    def start(self) -> bool:
        """Start monitoring. Returns True if successful."""
        if self._running:
            logger.warning("Monitor already running")
            return True
        
        logger.info("Starting Grove Vision monitor...")
        
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=1)
            logger.debug(f"Serial port opened: {self.port}")
            
            # Send space key to initialize device
            self._serial.write(b' ')
            time.sleep(2)
            self._serial.reset_input_buffer()
            logger.debug("Device initialized with space key")
            
            # Send start command (corrected format)
            command = "AT+INVOKE=1,1,0\r\n"
            self._serial.write(command.encode('utf-8'))
            logger.debug(f"Command sent: {command.strip()}")
            
            # Wait for confirmation
            time.sleep(1)
            response_received = False
            for _ in range(5):
                if self._serial.in_waiting > 0:
                    line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                    logger.debug(f"Device response: {line}")
                    if '"name":"INVOKE"' in line:
                        response_received = True
                        break
                time.sleep(0.5)
            
            self._connected = True
            self._running = True
            self._stress_events = []  # Reset events for new session
            
            # Start monitoring thread
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            
            if response_received:
                logger.info(f"Grove Vision monitor started successfully on {self.port}")
            else:
                logger.warning(f"Grove Vision monitor started on {self.port} but no INVOKE response received")
            
            return True
            
        except serial.SerialException as e:
            self._last_error = str(e)
            logger.error(f"Failed to connect to Grove Vision device: {e}")
            logger.info("Continuing in simulation mode (device not connected)")
            
            # Still mark as running for simulation mode
            self._connected = False
            self._running = True
            self._stress_events = []
            
            return True  # Return True to allow simulation mode
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Unexpected error starting Grove Vision: {e}")
            return False
    
    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return summary."""
        logger.info("Stopping Grove Vision monitor...")
        
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        if self._serial:
            try:
                self._serial.close()
                logger.debug("Serial connection closed")
            except:
                pass
            self._serial = None
        
        self._connected = False
        
        summary = {
            "stress_event_count": len(self._stress_events),
            "events": [
                {
                    "label": e.label,
                    "confidence": e.confidence,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self._stress_events
            ]
        }
        
        logger.info(f"Grove Vision monitor stopped. Total stress events: {len(self._stress_events)}")
        return summary
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        while self._running and self._serial:
            try:
                if self._serial.in_waiting > 0:
                    line = self._serial.readline().decode('utf-8', errors='ignore').strip()
                    self._process_line(line)
                else:
                    time.sleep(0.01)  # Small sleep to prevent CPU spinning
                    
            except serial.SerialException as e:
                logger.error(f"Serial error: {e}")
                self._connected = False
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
    
    def _process_line(self, line: str) -> None:
        """Process a line of data from the device."""
        if '"name":"INVOKE"' in line and '"boxes"' in line:
            try:
                obj = json.loads(line)
                boxes = obj.get('data', {}).get('boxes', [])
                
                for box in boxes:
                    if len(box) >= 2:
                        label_index = box[-1]
                        confidence = box[-2]
                        
                        if label_index < len(CLASS_NAMES):
                            label = CLASS_NAMES[label_index]
                            logger.debug(f"Detection: {label} ({confidence}%)")
                            self._handle_detection(label, confidence)
                            
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode error: {e}")
            except Exception as e:
                logger.debug(f"Error processing detection: {e}")
        
        elif "INIT@STAT" in line:
            # Device needs reinitialization
            logger.debug("Device needs reinitialization")
            if self._serial:
                self._serial.write(b"AT+INVOKE=1,1,0\r\n")
        
        elif '"name":"INVOKE"' in line:
            # INVOKE response without boxes (initialization confirmation)
            logger.debug("INVOKE initialization confirmed")
        
        else:
            # Log other messages at debug level
            if len(line) > 20:  # Only log substantial messages
                logger.debug(f"Device message: {line[:100]}...")
    
    def _handle_detection(self, label: str, confidence: float) -> None:
        """Handle a detection result."""
        # Check if this is a stress event
        if label in STRESS_LABELS and confidence >= self.confidence_threshold:
            now = datetime.now()
            
            # Debounce: don't trigger too frequently
            if self._last_stress_time:
                elapsed = (now - self._last_stress_time).total_seconds()
                if elapsed < self._debounce_seconds:
                    return
            
            # Record stress event
            event = StressEvent(
                label=label,
                confidence=confidence,
                timestamp=now
            )
            self._stress_events.append(event)
            self._last_stress_time = now
            
            # Log to main logger (all logs)
            logger.info(f"Stress event detected: {label} ({confidence}%)")
            
            # Log to events-only logger
            event_logger.info(f"STRESS_EVENT | {label} | confidence={confidence}% | total_count={len(self._stress_events)}")
            
            # Notify callbacks
            for callback in self._stress_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Callback error: {e}")


# Global monitor instance
_monitor: Optional[GroveVisionMonitor] = None


def get_monitor() -> GroveVisionMonitor:
    """Get or create the global monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = GroveVisionMonitor()
    return _monitor


def start_monitoring(port: Optional[str] = None) -> bool:
    """Start the global monitor."""
    monitor = get_monitor()
    if port:
        monitor.port = port
    return monitor.start()


def stop_monitoring() -> Dict[str, Any]:
    """Stop the global monitor and return summary."""
    monitor = get_monitor()
    return monitor.stop()


def get_stress_count() -> int:
    """Get current stress event count."""
    monitor = get_monitor()
    return monitor.stress_event_count
