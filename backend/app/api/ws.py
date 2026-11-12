from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
import json
import redis.asyncio as redis
from app.core.config import settings
from app.api.auth import get_current_user_ws

router = APIRouter()

@router.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket, current_user=Depends(get_current_user_ws)):
    if not current_user:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    
    redis_client = redis.from_url(settings.REDIS_URL)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("incidents_channel")
    
    async def redis_reader():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"].decode("utf-8")
                    await websocket.send_text(data)
        except asyncio.CancelledError:
            pass
            
    reader_task = asyncio.create_task(redis_reader())
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        reader_task.cancel()
        await pubsub.unsubscribe("incidents_channel")
        await redis_client.aclose() if hasattr(redis_client, 'aclose') else await redis_client.close()
