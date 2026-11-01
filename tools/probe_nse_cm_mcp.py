#!/usr/bin/env python3
"""Probe NSE's public CM Market MCP endpoint without credentials; never persists secrets."""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

URL = "https://mcp.nseindia.in/cmmkt/mcp"

def parse_response(raw):
    raw = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
    candidates = []
    try:
        candidates.append(json.loads(raw))
    except Exception:
        pass
    for line in raw.splitlines():
        if line.startswith("data:"):
            try:
                candidates.append(json.loads(line[5:].strip()))
            except Exception:
                continue
    for item in reversed(candidates):
        if isinstance(item, dict) and ("result" in item or "error" in item):
            return item
    raise RuntimeError("MCP response contained no JSON-RPC result: " + raw[:500])

def post(payload, session=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "ProStockIntelligence-personal-research/1.0",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read()
        return response.status, response.headers.get("Mcp-Session-Id") or session, response.headers.get("Content-Type", ""), parse_response(body) if body else {}

def main():
    report = {"endpoint": URL, "checkedAt": datetime.now(timezone.utc).isoformat(), "auth": "none", "ok": False}
    status, session, content_type, init = post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "psi-personal-probe", "version": "1.0.0"}}
    })
    if "error" in init:
        raise RuntimeError("initialize failed: " + json.dumps(init["error"])[:500])
    report.update({"initializeHttp": status, "contentType": content_type, "protocol": init.get("result", {}).get("protocolVersion"), "serverInfo": init.get("result", {}).get("serverInfo")})
    report["sessionIdReceived"] = bool(session)
    # Some public MCP gateways reject the optional initialized notification with 404;
    # tools/list is the authoritative connectivity check and is attempted regardless.
    try:\n        post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, session)\n    except Exception as exc:\n        report["initializedNotificationWarning"] = str(exc)\n    _, session, _, listed = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, session)
    tools = listed.get("result", {}).get("tools", [])
    names = [t.get("name") for t in tools]
    report["toolNames"] = names
    quote_tool = next((t for t in tools if t.get("name") == "cm_get_stock_quote"), None)
    if not quote_tool:
        raise RuntimeError("Expected cm_get_stock_quote absent; tool list=" + ",".join(map(str, names)))
    report["quoteInputSchema"] = quote_tool.get("inputSchema")
    _, session, _, quote = post({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "cm_get_stock_quote", "arguments": {"symbol": "INFY"}}
    }, session)
    result = quote.get("result", {})
    content = result.get("content", [])
    texts = [x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text"]
    report["isError"] = result.get("isError", False)
    report["quoteText"] = texts[:2]
    if texts:
        try:
            parsed = json.loads(texts[0])
            report["quoteJson"] = parsed
            report["softError"] = parsed.get("error") if isinstance(parsed, dict) else None
        except Exception:
            report["quoteJsonParseError"] = True
    report["ok"] = bool(texts) and not report["isError"] and not report.get("softError")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit("NSE MCP returned no validated stock quote; inspect report artifact")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "checkedAt": datetime.now(timezone.utc).isoformat()}, indent=2))
        raise
