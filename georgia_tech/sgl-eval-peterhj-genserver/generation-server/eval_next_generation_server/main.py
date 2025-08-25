from typing import Annotated
from argparse import ArgumentParser
from contextlib import asynccontextmanager
import json
import logging

from fastapi import FastAPI, Header, Request, HTTPException
import uvicorn

from .api_client import APIClient
from .api_registry import APIRegistry
from .server_config import ServerConfig

@asynccontextmanager
async def lifespan(app):
    app.state.server_config = ServerConfig(
        default_key=app.server_args.key,
        journal_path=app.server_args.journal_path,
    )
    app.state.registry = APIRegistry()
    app.state.client = APIClient(
        app.state.registry,
        max_workers=app.server_args.max_workers,
    )
    app.state.inflight_ctr = 0
    yield

app = FastAPI(lifespan=lifespan)
logger = logging.getLogger("uvicorn.error")

@app.get("/v1/models")
async def v1_models(authorization: Annotated[str | None, Header()], request: Request):
    request.app.state.server_config.authorize_request(authorization, request)
    # FIXME: pydantic.
    return {
        "data": [model.to_openai() for _, model in request.app.state.registry.models.items()],
        "object": "list",
    }

@app.post("/v1/chat/completions")
async def v1_chat_completions(authorization: Annotated[str | None, Header()], request: Request):
    request.app.state.server_config.authorize_request(authorization, request)
    payload = await request.json()
    print(f"DEBUG: v1_chat_completions: payload = {payload}")
    model = payload.pop("model", None)
    model_path = payload.pop("model_path", None)
    if (model is not None and model_path is None):
        model_path = model
    elif (model is None and model_path is not None):
        pass
    elif (model is None and model_path is None):
        raise HTTPException(status_code=400, detail="missing \"model\" or \"model_path\"")
    else:
        raise HTTPException(status_code=400, detail="specified both \"model\" and \"model_path\"")
    messages = payload.pop("messages", None)
    if messages is None:
        raise HTTPException(status_code=400, detail="missing \"messages\"")
    tools = payload.pop("tools", None)
    model = request.app.state.registry.find_model(model_path)
    if model is None:
        raise HTTPException(status_code=400, detail=f"model path not found: {repr(model_path)}")
    if payload.get("stream", None):
        raise HTTPException(status_code=400, detail="streaming chat completion not supported")
    debug = payload.pop("x_sgl_debug", None)
    app.state.inflight_ctr += 1
    logger.info(f"POST /v1/chat/completions: request  inflight = {app.state.inflight_ctr}")
    status, res, exc = await request.app.state.client.chat_completion(
        model=model,
        messages=messages,
        sampling_params=payload,
        tools=tools,
        debug=debug,
    )
    logger.info(f"POST /v1/chat/completions: response inflight = {app.state.inflight_ctr}")
    app.state.inflight_ctr -= 1
    payload = res.payload
    if debug:
        payload["x_sgl_debug_messages"] = res.debug_messages
        payload["x_sgl_debug_sampling_params"] = res.debug_sampling_params
        payload["x_sgl_debug_tools"] = res.debug_tools
        payload["x_sgl_debug_request"] = res.debug_request
        payload["x_sgl_debug_response"] = res.debug_response
    # TODO: returning non-200 but OK status codes.
    if not (status >= 200 and status < 300):
        raise HTTPException(status_code=status, detail=json.dumps(payload))
    return payload

@app.post("/v1/completions")
async def v1_completions(request: Request):
    raise HTTPException(status_code=405, detail="not implemented")
    return dict()

@app.post("/v1/messages")
async def v1_messages(
    x_api_key: Annotated[str | None, Header()],
    anthropic_version: Annotated[str | None, Header()],
    request: Request
):
    request.app.state.server_config.authorize_anthropic_request(x_api_key, request)
    payload = await request.json()
    print(f"DEBUG: v1_messages: version = {repr(anthropic_version) if anthropic_version is not None else None} payload = {payload}")
    model = payload.pop("model", None)
    model_path = payload.pop("model_path", None)
    if (model is not None and model_path is None):
        model_path = model
    elif (model is None and model_path is not None):
        pass
    elif (model is None and model_path is None):
        raise HTTPException(status_code=400, detail="missing \"model\" or \"model_path\"")
    else:
        raise HTTPException(status_code=400, detail="specified both \"model\" and \"model_path\"")
    model = request.app.state.registry.find_model(model_path)
    if model is None:
        raise HTTPException(status_code=400, detail=f"model path not found: {repr(model_path)}")
    if not model.model_path.startswith("anthropic/"):
        raise HTTPException(status_code=400, detail="/v1/messages only supports anthropic models")
    debug = payload.pop("x_sgl_debug", None)
    app.state.inflight_ctr += 1
    logger.info(f"POST /v1/messages: request  inflight = {app.state.inflight_ctr}")
    status, res, exc = await request.app.state.client.message(
        model=model,
        api_version=anthropic_version,
        payload=payload,
        # debug=debug,
    )
    logger.info(f"POST /v1/messages: response inflight = {app.state.inflight_ctr}")
    app.state.inflight_ctr -= 1
    payload = res.payload
    # TODO: returning non-200 but OK status codes.
    if not (status >= 200 and status < 300):
        raise HTTPException(status_code=status, detail=json.dumps(payload))
    return payload

def _start_server(args):
    app.server_args = args
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("--host", type=str, default="127.0.0.1")
    args.add_argument("--port", type=int, default=10000)
    args.add_argument("--max-workers", type=int, default=192)
    args.add_argument("--journal-path", type=str, default=None)
    args.add_argument("--key", type=str, default="dev")
    args = args.parse_args()
    _start_server(args)
