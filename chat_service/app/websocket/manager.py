from datetime import datetime

from fastapi import WebSocket
from typing import Dict, Set, List

from shared.logger import setup_logger

import json

logger = setup_logger(__name__)

class ConnectionManager:
    """
    websoccet connectionni manage qilish
    """

    def __init__(self):
        self.active_connections:Dict[str,Set[WebSocket]] = {}
        self.user_rooms: Dict[str, Set[str]] = {}


    async def connect(self, websocket:WebSocket, room_id: str, user_id:str):
        """
        WebSocket connection qabul qilish
        """
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()

        self.active_connections[room_id].add(websocket)

        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()

        self.user_rooms[user_id].add(room_id)

        logger.info(f"user {user_id} connection to room {room_id}")

        # connection natifaction

        await self.broadcast(
            room_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
                "active_users": len(self.active_connections[room_id])
            },
            exclude_user = None
        )
    async def disconnect(self, websocket: WebSocket, room_id:str, user_id:str):
        """
            WebSocket disconnection
        """
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]


        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)

        logger.info(f"user {user_id} disconnected form room {room_id}")

        # Disconnection notifaction

        if room_id in self.active_connections:
            await self.broadcast(
                room_id,
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "room_id": room_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "active_users": len(self.active_connections[room_id])

                }
            )


    async def broadcast(self, room_id:str, message:dict, exclude_user: str = None):
        """
            Barcha connected clientlarga xabar yuborish
        """

        if room_id not in self.active_connections:
            return

        message_json = json.dumps(message, default=str)

        for connection in self.active_connections[room_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"error sending message: {str(e)}")


    async def send_personal_message(
            self,
            websocket:WebSocket,
            message:dict

        ):
        try:
            await websocket.send_text(json.dumps(message, default=str))

        except Exception as e:
            logger.error(f" error sending personal message : {str(e)}")

    def get_room_users_count(self, room_id:str)->int:

        """
        roomda nechta user bor
        """
        if room_id not in self.active_connections:
            return 0

        return len(self.active_connections[room_id])




