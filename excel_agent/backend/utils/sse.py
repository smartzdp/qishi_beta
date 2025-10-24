"""
Server-Sent Events utilities
"""
import json
from typing import Dict, Any, AsyncGenerator


async def sse_message(event: str, data: Dict[str, Any]) -> str:
    """
    Format a Server-Sent Event message
    
    Args:
        event: Event name
        data: Event data
        
    Returns:
        Formatted SSE message
    """
    message = f"event: {event}\n"
    message += f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    return message


async def sse_generator(events: AsyncGenerator) -> AsyncGenerator[str, None]:
    """
    Generate SSE messages from an async generator
    
    Args:
        events: Async generator of (event_name, data) tuples
        
    Yields:
        Formatted SSE messages
    """
    async for event_name, data in events:
        yield await sse_message(event_name, data)

