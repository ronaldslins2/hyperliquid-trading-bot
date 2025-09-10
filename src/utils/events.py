from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Event types for the trading framework"""

    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_PLACED = "order_placed"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"
    PRICE_UPDATE = "price_update"
    STRATEGY_START = "strategy_start"
    STRATEGY_STOP = "strategy_stop"
    STRATEGY_UPDATE = "strategy_update"
    ERROR = "error"
    SYSTEM = "system"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class Event:
    """Base event class"""

    type: EventType
    timestamp: float
    data: Dict[str, Any]
    source: Optional[str] = None


class EventBus:
    """Simple event bus for framework communication"""

    def __init__(self):
        self._listeners: Dict[EventType, List[Callable[[Event], None]]] = {}

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """Subscribe to an event type"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unsubscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """Unsubscribe from an event type"""
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass

    def emit(self, event: Event) -> None:
        """Emit an event to all subscribers"""
        if event.type in self._listeners:
            for callback in self._listeners[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    # Log error but don't stop other listeners
                    print(f"Error in event listener: {e}")
