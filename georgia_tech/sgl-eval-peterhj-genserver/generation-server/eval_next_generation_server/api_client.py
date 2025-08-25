from typing import Any, Optional
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import concurrent.futures
import json
import threading
import time
import traceback
import urllib.request

from .api_registry import APIEndpoint, APIModel, APIRegistry
from .utils import merge_dicts

@dataclass
class ExceptItem:
    exc_type: str
    exc_str: str
    stack_trace: str

@dataclass
class ResponseItem:
    t0: str = None
    t1: str = None
    status: int = None
    payload: Any = None
    debug_messages: Any = None
    debug_sampling_params: Any = None
    debug_tools: Any = None
    debug_request: Any = None
    debug_response: Any = None

@dataclass
class ChatCompletionWorkItem:
    model: APIModel
    messages: Any
    sampling_params: Any
    tools: Any
    debug: Optional[bool]
    res: Any = None
    exc: Any = None

    def _finalize(self):
        if self.exc is not None:
            print(f"DEBUG: ChatCompletionWorkItem._finalize: exc = {self.exc}")
            return 500, self.res, self.exc
        if self.res is None:
            return 500, self.res, self.exc
        return self.res.status, self.res, self.exc

@dataclass
class AnthropicMessageWorkItem:
    model: APIModel
    api_version: Optional[str]
    payload: Any
    # debug: Optional[bool]
    res: Any = None
    exc: Any = None

    def _finalize(self):
        if self.exc is not None:
            print(f"DEBUG: AnthropicMessageWorkItem._finalize: exc = {self.exc}")
            return 500, self.res, self.exc
        if self.res is None:
            return 500, self.res, self.exc
        return self.res.status, self.res, self.exc

@dataclass
class APIClientModelEndpoint:
    model: APIModel
    endpoint: APIEndpoint = None
    max_new_tokens: int = None
    throttle_rps: Optional[int] = None

    def __post_init__(self) -> None:
        if self.endpoint is None:
            self.endpoint = self.model.endpoint
        if self.endpoint.protocol in (
            "deepseek",
            "openai",
        ):
            # TODO: proper urllib formatting.
            if self.endpoint.protocol == "deepseek":
                self._chat_endpoint_url = "{}/chat/completions".format(self.endpoint.api_url)
            elif self.endpoint.protocol == "openai":
                self._chat_endpoint_url = "{}/v1/chat/completions".format(self.endpoint.api_url)
            else:
                raise NotImplementedError
            self._chat_endpoint_headers = {
                "User-Agent": "fastapi",
                "Authorization": "Bearer {}".format(self.endpoint.api_key),
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        elif self.endpoint.protocol == "anthropic":
            # TODO: proper urllib formatting.
            self._chat_endpoint_url = "{}/v1/messages".format(self.endpoint.api_url)
            self._chat_endpoint_headers = {
                "User-Agent": "fastapi",
                "X-API-Key": "{}".format(self.endpoint.api_key),
                "Anthropic-Version": "2023-06-01",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        elif self.endpoint.protocol == "gemini":
            self._chat_endpoint_url = "{}/v1beta/{}:generateContent".format(
                self.endpoint.api_url,
                self.model.endpoint_model_path,
            )
            self._chat_endpoint_headers = {
                "User-Agent": "fastapi",
                "x-goog-api-key": "{}".format(self.endpoint.api_key),
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        else:
            raise NotImplementedError

    def chat_completion(
        self,
        messages: list[dict[str, Any]] = None,
        sampling_params: dict[str, Any] = None,
        tools: Optional[list] = None,
        debug: Optional[bool] = None,
        res: Any = None,
    ):
        og_messages = deepcopy(messages)
        og_sampling_params = deepcopy(sampling_params)
        if sampling_params is None:
            sampling_params = dict()
        system_prompt = None
        if self.endpoint.protocol in ("anthropic", "gemini"):
            if messages and messages[0]["role"] == "system":
                system_prompt = messages[0]["content"]
                messages = messages[1:]
        if self.endpoint.protocol in (
            "anthropic",
            "deepseek",
            "openai",
        ):
            req_body = dict()
            req_body["model"] = self.model.endpoint_model_path
            if system_prompt is not None:
                req_body["system"] = system_prompt
            if (
                self.endpoint.protocol == "anthropic" and
                messages is not None
            ):
                newmessages = []
                for message in messages:
                    role = message["role"]
                    if role == "assistant":
                        newcontent = []
                        if "content" in message:
                            newcontent.append({
                                "type": "text",
                                "text": message["content"],
                            })
                        # NB(peter): reasoning block must be the last block
                        # before tool call blocks.
                        if "reasoning_content" in message:
                            reasoning = message["reasoning_content"]
                            newblock = {
                                "type": "thinking",
                                "thinking": reasoning,
                            }
                            if "reasoning_id" in message:
                                newblock["signature"] = message["reasoning_id"]
                            newcontent.append(newblock)
                        if "tool_calls" in message:
                            for tool_call in (message["tool_calls"] or []):
                                tool_call_id = tool_call["id"]
                                fun_call = tool_call["function"]
                                tool_call_name = fun_call["name"]
                                tool_call_args = fun_call["arguments"]
                                newcontent.append({
                                    "type": "tool_use",
                                    "id": tool_call_id,
                                    "name": tool_call_name,
                                    "input": json.loads(tool_call_args),
                                })
                        newmessage = {
                            "role": role,
                            "content": newcontent,
                        }
                    elif role == "tool":
                        newmessage = {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": message["tool_call_id"],
                                    "content": message["content"],
                                },
                            ],
                        }
                    elif role == "user":
                        newmessage = {
                            "role": role,
                            "content": message["content"],
                        }
                    else:
                        raise ValueError(f"not implemented: anthropic support for role: {repr(role)}")
                    newmessages.append(newmessage)
                req_body["messages"] = newmessages
            elif messages is not None:
                req_body["messages"] = messages
            if (
                self.endpoint.protocol == "anthropic" and
                tools is not None
            ):
                newtools = []
                for tool in tools:
                    if tool["type"] != "function":
                        raise ValueError(f"not implemented: anthropic version of tool: {tool}")
                    fun = tool["function"]
                    newtool = {
                        "name": fun["name"],
                        "description": fun["description"],
                        "input_schema": fun["parameters"],
                    }
                    newtools.append(newtool)
                req_body["tools"] = newtools
            elif tools is not None:
                req_body["tools"] = tools
            req_body["stream"] = False
            if self.endpoint.protocol == "deepseek":
                max_completion_tokens = sampling_params.pop("max_completion_tokens", None)
                if max_completion_tokens is not None:
                    assert "max_new_tokens" not in sampling_params
                    sampling_params["max_new_tokens"] = max_completion_tokens
                max_tokens = sampling_params.pop("max_tokens", None)
                if max_tokens is not None:
                    assert "max_new_tokens" not in sampling_params
                    sampling_params["max_new_tokens"] = max_tokens
            if self.endpoint.protocol in ("anthropic", "openai"):
                max_new_tokens = sampling_params.pop("max_new_tokens", None)
                if max_new_tokens is not None:
                    assert "max_tokens" not in sampling_params
                    sampling_params["max_tokens"] = max_new_tokens
                max_completion_tokens = sampling_params.pop("max_completion_tokens", None)
                if max_completion_tokens is not None:
                    assert "max_tokens" not in sampling_params
                    sampling_params["max_tokens"] = max_completion_tokens
                if (
                    self.model.model_path.startswith("openai/o3") or
                    self.model.model_path.startswith("openai/o4")
                ):
                    max_tokens = sampling_params.pop("max_tokens", None)
                    if max_tokens is not None:
                        assert "max_completion_tokens" not in sampling_params
                        sampling_params["max_completion_tokens"] = max_tokens
                    sampling_params.pop("stop", None)
            if self.endpoint.protocol == "anthropic":
                stop = sampling_params.pop("stop", None)
                if stop is None:
                    pass
                elif isinstance(stop, str):
                    sampling_params["stop_sequences"] = [stop]
                elif isinstance(stop, list):
                    sampling_params["stop_sequences"] = stop
                else:
                    raise ValueError(f"invalid conversion to stop_sequences: {stop}")
                sampling_params.pop("frequency_penalty", None)
                sampling_params.pop("presence_penalty", None)
                sampling_params.pop("logprobs", None)
                sampling_params.pop("top_logprobs", None)
        elif self.endpoint.protocol == "gemini":
            contents = None
            for message_idx, message in enumerate(messages or []):
                role = message["role"]
                if role == "assistant":
                    role = "model"
                    parts = []
                    if "reasoning_id" in message:
                        part = {
                            "thought": True,
                            "thoughtSignature": message["reasoning_id"],
                        }
                        if "reasoning_content" in message:
                            part["text"] = message["reasoning_content"]
                        parts.append(part)
                    if "content" in message:
                        msg_content = message["content"]
                        if isinstance(msg_content, str):
                            part = {
                                "text": msg_content,
                            }
                        else:
                            raise ValueError(f"not implemented: gemini support for assistant message: {message}")
                        parts.append(part)
                    if "tool_calls" in message:
                        for tool_call in message["tool_calls"]:
                            if tool_call["type"] != "function":
                                raise ValueError(f"not implemented: gemini support for non-function tool call: {tool_call}")
                            tool_call_id = tool_call["id"]
                            fun_call = tool_call["function"]
                            tool_call_name = fun_call["name"]
                            tool_call_args = json.loads(fun_call["arguments"])
                            parts.append({
                                "functionCall": {
                                    "id": tool_call_id,
                                    "name": tool_call_name,
                                    "args": tool_call_args,
                                },
                            })
                elif role == "tool":
                    role = "user"
                    parts = []
                    tool_call_id = message["tool_call_id"]
                    tool_call_name = None
                    for prev_message_idx in reversed(range(message_idx)):
                        prev_message = messages[prev_message_idx]
                        if "tool_calls" in prev_message:
                            for tool_call in prev_message["tool_calls"]:
                                if tool_call["type"] != "function":
                                    raise ValueError(f"not implemented: gemini support for non-function tool call: {tool_call}")
                                fun_call = tool_call["function"]
                                if tool_call_id == tool_call["id"]:
                                    tool_call_name = fun_call["name"]
                                    break
                            if tool_call_name is not None:
                                break
                    tool_call_result = json.loads(message["content"])
                    parts.append({
                        "functionResponse": {
                            "id": tool_call_id,
                            "name": tool_call_name,
                            "response": tool_call_result,
                        },
                    })
                elif role == "user":
                    parts = []
                    msg_content = message["content"]
                    if isinstance(msg_content, str):
                        parts.append({
                            "text": msg_content,
                        })
                    else:
                        raise ValueError(f"not implemented: gemini support for user message: {message}")
                else:
                    raise ValueError(f"not implemented: gemini support for role: {repr(role)}")
                content = {
                    "role": role,
                    "parts": parts,
                }
                if contents is None:
                    contents = []
                contents.append(content)
            newtools = None
            for tool in (tools or []):
                newtool = tool
                if newtools is None:
                    newtools = []
                newtools.append(newtool)
            req_body = dict()
            if system_prompt is not None:
                req_body["system_instruction"] = {
                    "parts": [
                        {
                            "text": system_prompt,
                        },
                    ],
                }
            if contents is not None:
                req_body["contents"] = contents
            if newtools is not None:
                req_body["tools"] = [
                    {
                        "functionDeclarations": newtools,
                    }
                ]
            # TODO: tool config.
            # req_body["toolConfig"] = _
            max_new_tokens = sampling_params.pop("max_new_tokens", None)
            if max_new_tokens is not None:
                assert "max_tokens" not in sampling_params
                sampling_params["max_tokens"] = max_new_tokens
            max_completion_tokens = sampling_params.pop("max_completion_tokens", None)
            if max_completion_tokens is not None:
                assert "max_tokens" not in sampling_params
                sampling_params["max_tokens"] = max_completion_tokens
            def _convert_stop(v):
                if v is None:
                    return []
                if isinstance(v, str):
                    return [v]
                if isinstance(v, list):
                    return v
                raise ValueError
            sampling_key_map = [
                ("stop", "stopSequences", _convert_stop),
                ("temperature",),
                ("top_p", "topP"),
                ("top_k", "topK"),
                ("n", "candidateCount"),
                ("max_tokens", "maxOutputTokens"),
                ("logprobs", "responseLogprobs"),
                ("top_logprobs", "logprobs"),
                ("seed",),
                # ("presence_penalty", "presencePenalty"),
                # ("frequency_penalty", "frequencyPenalty"),
                ("presence_penalty", None),
                ("frequency_penalty", None),
                ("stream", None),
            ]
            generation_cfg = dict()
            for k in sampling_key_map:
                if len(k) == 1:
                    ok, = k
                    nk = ok
                    convert = None
                elif len(k) == 2:
                    ok, nk = k
                    convert = None
                elif len(k) == 3:
                    ok, nk, convert = k
                else:
                    raise NotImplementedError
                if ok in sampling_params:
                    v = sampling_params.pop(ok)
                    if convert is not None:
                        v = convert(v)
                    if nk is not None:
                        generation_cfg[nk] = v
            if sampling_params:
                raise ValueError(f"unsupported sampling params: {sampling_params.keys()}")
            sampling_params = {
                "generationConfig": generation_cfg,
            }
        else:
            raise NotImplementedError
        if (
            self.model.model_path.startswith("openai/o3") or
            self.model.model_path.startswith("openai/o4")
        ):
            sampling_params.pop("temperature", None)
            sampling_params.pop("top_p", None)
        res.sampling_params = sampling_params
        req_body |= sampling_params
        # req_body = merge_dicts(req_body, sampling_params)
        if self.model.endpoint_extra_params is not None:
            req_body = merge_dicts(req_body, deepcopy(self.model.endpoint_extra_params))
        if self.endpoint.protocol == "anthropic":
            if (
                "max_tokens" in req_body and
                "thinking" in req_body and
                "budget_tokens" in req_body["thinking"]
            ):
                max_tokens = req_body["max_tokens"]
                thinking_tokens = req_body["thinking"]["budget_tokens"]
                # print(f"DEBUG: APIClientModelEndpoint.chat_completion: anthropic: max tokens = {max_tokens} thinking tokens = {thinking_tokens}")
                req_body["thinking"]["budget_tokens"] = max(0, min(max_tokens - 1, thinking_tokens))
        print(f"DEBUG: APIClientModelEndpoint.chat_completion: req body = {req_body}")
        if debug:
            res.debug_messages = og_messages
            res.debug_sampling_params = og_sampling_params
            res.debug_tools = tools
            res.debug_request = req_body
        req_data = json.dumps(req_body).encode("utf-8")
        hreq = urllib.request.Request(
            self._chat_endpoint_url,
            headers = self._chat_endpoint_headers.copy(),
            data = req_data,
        )
        res.t0 = datetime.utcnow().isoformat()
        try:
            with urllib.request.urlopen(hreq) as hres:
                res_status = hres.status
                res_data = hres.read()
        except urllib.error.HTTPError as e:
            err_status = e.code
            res.t1 = datetime.utcnow().isoformat()
            res.status = err_status
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                print(f"DEBUG: APIClientModelEndpoint.chat_completion: err body = {err_body}")
                res.payload = err_body
            except Exception:
                pass
            return res
        except urllib.error.URLError as e:
            err_status = e.code
            res.t1 = datetime.utcnow().isoformat()
            res.status = err_status
            return res
        res.t1 = datetime.utcnow().isoformat()
        res.status = res_status
        res_body = json.loads(res_data.decode("utf-8"))
        print(f"DEBUG: APIClientModelEndpoint.chat_completion: res body = {res_body}")
        if debug:
            res.debug_response = deepcopy(res_body)
        res.payload = res_body
        if self.endpoint.protocol == "anthropic":
            res_type = res.payload.pop("type")
            if res_type != "message":
                raise ValueError(f"not implemented: anthropic response type = {repr(res_type)}")
            role = res.payload.pop("role")
            res_content = res.payload.pop("content")
            res_stop_sequence = res.payload.pop("stop_sequence", None)
            res_stop_reason = res.payload.pop("stop_reason", None)
            if res_stop_reason is None:
                finish_reason = None
            elif res_stop_reason == "refusal":
                finish_reason = "content_filter"
            elif res_stop_reason in ("max_tokens", "pause_turn"):
                finish_reason = "length"
            elif res_stop_reason in ("end_turn", "stop_sequence"):
                finish_reason = "stop"
            elif res_stop_reason == "tool_use":
                finish_reason = "tool_calls"
            else:
                raise ValueError(f"not implemented: anthropic stop reason = {repr(res_stop_reason)}")
            res_usage = res.payload.pop("usage", None)
            res.payload["object"] = "chat.completion"
            res.payload["created"] = int(datetime.fromisoformat(res.t1).timestamp())
            reasoning_id = None
            reasoning = None
            text = None
            tool_calls = None
            for content in res_content:
                content_type = content["type"]
                if content_type == "thinking":
                    assert reasoning is None
                    reasoning = content["thinking"]
                    if "signature" in content:
                        assert reasoning_id is None
                        reasoning_id = content["signature"]
                elif content_type == "text":
                    assert text is None
                    text = content["text"]
                elif content_type == "tool_use":
                    tool_call_id = content["id"]
                    tool_call_name = content["name"]
                    tool_call = {
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call_name,
                        },
                    }
                    if "input" in content:
                        tool_call["function"]["arguments"] = json.dumps(content["input"])
                    if tool_calls is None:
                        tool_calls = []
                    tool_calls.append(tool_call)
                else:
                    raise ValueError(f"not implemented: anthropic response content: {res_content}")
            message = {
                "role": role,
            }
            if reasoning_id is not None:
                message["reasoning_id"] = reasoning_id
            if reasoning is not None:
                message["reasoning_content"] = reasoning
            if text is not None:
                message["content"] = text
            if tool_calls is not None:
                message["tool_calls"] = tool_calls
            res.payload["choices"] = [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": finish_reason,
                }
            ]
            if res_usage is not None:
                usage = dict()
                total_tokens = 0
                if "input_tokens" in res_usage:
                    usage["prompt_tokens"] = res_usage["input_tokens"]
                    total_tokens += usage["prompt_tokens"]
                if "output_tokens" in res_usage:
                    usage["completion_tokens"] = res_usage["output_tokens"]
                    total_tokens += usage["completion_tokens"]
                usage["total_tokens"] = total_tokens
                res.payload["usage"] = usage
                service_tier = res_usage.get("service_tier", None)
                if service_tier is not None:
                    res.payload["service_tier"] = service_tier
        elif self.endpoint.protocol == "gemini":
            def _convert_choice(v):
                content_dict = v["content"]
                role = content_dict["role"]
                if role == "model":
                    role = "assistant"
                reasoning_id = None
                reasoning = None
                text = None
                tool_calls = None
                for part in content_dict["parts"]:
                    if "thought" in part and part["thought"]:
                        if "thoughtSignature" in part:
                            assert reasoning_id is None
                            reasoning_id = part["thoughtSignature"]
                        if "text" in part:
                            assert reasoning is None
                            reasoning = part["text"]
                    elif "functionCall" in part:
                        fun_call = part["functionCall"]
                        tool_call_id = fun_call["id"]
                        tool_call_name = fun_call["name"]
                        tool_call = {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_call_name,
                            },
                        }
                        if "args" in fun_call:
                            tool_call["function"]["arguments"] = json.dumps(fun_call["args"])
                        if tool_calls is None:
                            tool_calls = []
                        tool_calls.append(tool_call)
                    elif "text" in part:
                        assert text is None
                        text = part["text"]
                    else:
                        raise NotImplementedError("not implemented: gemini response choice: {v}")
                message = {
                    "role": role,
                }
                if reasoning_id is not None:
                    message["reasoning_id"] = reasoning_id
                if reasoning is not None:
                    message["reasoning_content"] = reasoning
                if text is not None:
                    message["content"] = text
                if tool_calls is not None:
                    message["tool_calls"] = tool_calls
                finish_reason = v["finishReason"]
                if finish_reason is not None:
                    finish_reason = finish_reason.lower()
                index = v["index"]
                return {
                    "index": index,
                    "message": message,
                    "finish_reason": finish_reason,
                }
            def _convert_choices(vs):
                return [_convert_choice(v) for v in vs]
            def _convert_usage(v):
                nv = dict()
                if "promptTokenCount" in v:
                    nv["prompt_tokens"] = v["promptTokenCount"]
                if "candidatesTokenCount" in v:
                    nv["completion_tokens"] = v["candidatesTokenCount"]
                if "totalTokenCount" in v:
                    nv["total_tokens"] = v["totalTokenCount"]
                if "thoughtsTokenCount" in v:
                    nv["completion_tokens_details"] = {
                        "reasoning_tokens": v["thoughtsTokenCount"],
                    }
                return nv
            response_key_map = [
                ("responseId", "id"),
                ("modelVersion", "model"),
                ("candidates", "choices", _convert_choices),
                ("usageMetadata", "usage", _convert_usage),
            ]
            payload = dict()
            payload["id"] = None
            payload["object"] = "chat.completion"
            payload["created"] = int(datetime.fromisoformat(res.t1).timestamp())
            for k in response_key_map:
                if len(k) == 1:
                    ok, = k
                    nk = ok
                    convert = None
                elif len(k) == 2:
                    ok, nk = k
                    convert = None
                elif len(k) == 3:
                    ok, nk, convert = k
                else:
                    raise ValueError
                if ok in res.payload:
                    v = res.payload.pop(ok)
                    if convert is not None:
                        v = convert(v)
                    payload[nk] = v
            res.payload = payload
        res.payload["model"] = self.model.model_path
        return res

    def message(
        self,
        api_version: Optional[str] = None,
        payload: Any = None,
        # debug: Optional[bool] = None,
        res: Any = None,
    ):
        req_body = payload
        req_body["model"] = self.model.endpoint_model_path
        req_data = json.dumps(req_body).encode("utf-8")
        req_headers = self._chat_endpoint_headers.copy()
        if api_version is not None:
            req_headers["Anthropic-Version"] = api_version
        hreq = urllib.request.Request(
            self._chat_endpoint_url,
            headers=req_headers,
            data=req_data,
        )
        res.t0 = datetime.utcnow().isoformat()
        try:
            with urllib.request.urlopen(hreq) as hres:
                res_status = hres.status
                res_data = hres.read()
        except urllib.error.HTTPError as e:
            err_status = e.code
            res.t1 = datetime.utcnow().isoformat()
            res.status = err_status
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                print(f"DEBUG: APIClientModelEndpoint.message: err body = {err_body}")
                res.payload = err_body
            except Exception:
                pass
            return res
        except urllib.error.URLError as e:
            err_status = e.code
            res.t1 = datetime.utcnow().isoformat()
            res.status = err_status
            return res
        res.t1 = datetime.utcnow().isoformat()
        res.status = res_status
        res_body = json.loads(res_data.decode("utf-8"))
        res.payload = res_body
        res.payload["model"] = self.model.model_path
        return res

def _chat_completion(work_item, endpoint_state):
    endpoint = APIClientModelEndpoint(work_item.model)
    t = datetime.utcnow()
    t0 = None
    # FIXME
    if False and endpoint.throttle_rps is not None:
        throttle_delay = 1.0 / endpoint.endpoint_throttle_rps
        delta_t = timedelta(seconds=throttle_delay)
        with self._get_lock:
            t0 = self._next_get_t0
            if t0 is not None:
                self._next_get_t0 = max(t0, t) + delta_t
            else:
                self._next_get_t0 = t + delta_t
        while t0 is not None and t0 > t:
            time.sleep((t0 - t).total_seconds())
            t = datetime.utcnow()
    print(f"DEBUG: APIClient.chat_completion: t = {t.isoformat()} t0 = {t0.isoformat() if t0 is not None else None}")
    work_item.res = ResponseItem()
    endpoint.chat_completion(
        messages=work_item.messages,
        sampling_params=work_item.sampling_params,
        tools=work_item.tools,
        debug=work_item.debug,
        res=work_item.res,
    )
    return work_item

def _try_chat_completion(work_item, endpoint_state):
    try:
        _chat_completion(work_item, endpoint_state)
    # TODO: exc reporting.
    except Exception as e:
        # print(f"DEBUG: _try_chat_completion: except = {e}")
        work_item.exc = ExceptItem(
            exc_type=f"{type(e).__name__}",
            exc_str=str(e),
            stack_trace=traceback.format_exc(),
        )
        print(f"DEBUG: _try_chat_completion: except = {work_item.exc}")
    return work_item

def _message(work_item, endpoint_state):
    endpoint = APIClientModelEndpoint(work_item.model)
    t = datetime.utcnow()
    t0 = None
    print(f"DEBUG: APIClient.message: t = {t.isoformat()} t0 = {t0.isoformat() if t0 is not None else None}")
    work_item.res = ResponseItem()
    endpoint.message(
        api_version=work_item.api_version,
        payload=work_item.payload,
        # debug=work_item.debug,
        res=work_item.res,
    )
    return work_item

def _try_message(work_item, endpoint_state):
    try:
        _message(work_item, endpoint_state)
    # TODO: exc reporting.
    except Exception as e:
        # print(f"DEBUG: _try_message: except = {e}")
        work_item.exc = ExceptItem(
            exc_type=f"{type(e).__name__}",
            exc_str=str(e),
            stack_trace=traceback.format_exc(),
        )
        print(f"DEBUG: _try_message: except = {work_item.exc}")
    return work_item

@dataclass
class APIClientEndpointState:
    _lock: Any = None
    _next_t0: Any = None

    def __post_init__(self):
        if self._lock is None:
            self._lock = threading.Lock()

@dataclass
class APIClientWorker:
    max_workers: int
    _poolexec: Any = None

    def __post_init__(self) -> None:
        if self._poolexec is None:
            self._poolexec = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers,
            )

@dataclass
class APIClient:
    registry: APIRegistry
    max_workers: int = 192
    timeout: int = 1800

    _worker: APIClientWorker = None
    _journal: Any = None
    # TODO: per-endpoint throttle state.
    # _get_lock: Any = None
    # _next_get_t0: Any = None
    _endpoint_state: dict[str, Any] = None

    def __post_init__(self) -> None:
        print(f"DEBUG: APIClient: max workers = {self.max_workers}")
        if self._worker is None:
            self._worker = APIClientWorker(self.max_workers)
        # if self._journal is None:
        #     self._journal = JournalAsyncInterface("approx-oracle")
        if self._endpoint_state is None:
            self._endpoint_state = dict()

    async def chat_completion(
        self,
        model: APIModel,
        messages: list[dict],
        sampling_params: Optional[dict] = None,
        tools: Optional[list] = None,
        debug: Optional[bool] = None,
    ):
        if model.endpoint.name not in self._endpoint_state:
            self._endpoint_state[model.endpoint.name] = APIClientEndpointState()
        endpoint_state = self._endpoint_state[model.endpoint.name]
        work_item = ChatCompletionWorkItem(
            model=model,
            messages=messages,
            sampling_params=sampling_params,
            tools=tools,
            debug=debug,
        )
        def _chat_completion_work_item():
            _try_chat_completion(work_item, endpoint_state)
            return work_item
        loop = asyncio.get_running_loop()
        w = loop.run_in_executor(self._worker._poolexec, _chat_completion_work_item)
        work_item = await w
        status, res, exc = work_item._finalize()
        if self._journal is not None:
            print(f"DEBUG: APIClient.chat_completion: journal put...")
            raise NotImplementedError
            put_ret = await self._journal.put(item)
            print(f"DEBUG: APIClient.chat_completion: journal put: ret = {repr(put_ret)}")
        return status, res, exc

    async def message(
        self,
        model: APIModel,
        api_version: Optional[str],
        payload: Any,
    ):
        if model.endpoint.name not in self._endpoint_state:
            self._endpoint_state[model.endpoint.name] = APIClientEndpointState()
        endpoint_state = self._endpoint_state[model.endpoint.name]
        work_item = AnthropicMessageWorkItem(
            model=model,
            api_version=api_version,
            payload=payload,
            # debug=debug,
        )
        def _message_work_item():
            _try_message(work_item, endpoint_state)
            return work_item
        loop = asyncio.get_running_loop()
        w = loop.run_in_executor(self._worker._poolexec, _message_work_item)
        work_item = await w
        status, res, exc = work_item._finalize()
        if self._journal is not None:
            raise NotImplementedError
        return status, res, exc
