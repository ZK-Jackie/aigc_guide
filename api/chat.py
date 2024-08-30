from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
from core.guide import AiGuide, UserInput
import json

api_chat = APIRouter()
stream_guide = AiGuide(streams=False)

@api_chat.post("/api/test")
async def test():
    return {"code": "200", "msg": "ok", "data": "hello, world!"}

@api_chat.post("/api/chat")
async def post_chat(chat_input: UserInput):
    res = stream_guide.invoke_with_history(chat_input)["output"]
    return {"output": res}


@api_chat.post("/api/stream")
async def chat(chat_input: UserInput):
    async def event_generator():
        msg = ""
        async for event in stream_guide.agent_with_chat_history.astream_events(
                input={"input": chat_input.input},
                config={"configurable": {"session_id": chat_input.session_id}},
                version="v1"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                token = event['data']['chunk'].content
                js_data = {
                    "code": "200",
                    "msg": "ok",
                    "data": token
                }
                yield json.dumps(js_data, ensure_ascii=False)
                msg += token
            elif kind == "on_chat_model_end":
                yield json.dumps({
                    'code': '200',
                    'msg': 'ok',
                    'data': '<|done|>'
                }, ensure_ascii=False)
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@api_chat.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            chat_input = UserInput(**data)
            await websocket.send_json({
                "code": "200",
                "msg": "ok",
                "data": "<|start|>"
            })
            async for event in stream_guide.agent_with_chat_history.astream_events(
                    input={"input": chat_input.input},
                    config={"configurable": {"session_id": chat_input.session_id}},
                    version="v1"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    token = event['data']['chunk'].content
                    js_data = {
                        "code": "200",
                        "msg": "ok",
                        "data": token
                    }
                    await websocket.send_json(js_data)
                elif kind == "on_chat_model_end":
                    await websocket.send_json({
                        'code': '200',
                        'msg': 'ok',
                        'data': '<|done|>'
                    })
                    break
    except WebSocketDisconnect:
        print("Client disconnected")
