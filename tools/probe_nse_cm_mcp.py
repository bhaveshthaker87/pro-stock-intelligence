#!/usr/bin/env python3
"""Probe NSE's public CM Market MCP endpoint; no credentials or cookies."""
import json
import urllib.request
from datetime import datetime, timezone

URL = "https://mcp.nseindia.in/cmmkt/mcp"

def decode(raw):
    raw = raw.decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except Exception:
        for line in raw.splitlines():
            if line.startswith("data:"):
                try:
                    return json.loads(line[5:].strip())
                except Exception:
                    pass
    raise RuntimeError("No JSON-RPC response in body: " + raw[:500])

def post(payload, session=None, protocol=None):
    headers = {"Content-Type":"application/json", "Accept":"application/json, text/event-stream",
               "User-Agent":"ProStockIntelligence-personal-research/1.0"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=25) as response:
        body = response.read()
        return response.status, response.headers.get("Mcp-Session-Id") or session, response.headers.get("Content-Type",""), decode(body) if body else {}

def main():
    report = {"endpoint":URL, "checkedAt":datetime.now(timezone.utc).isoformat(), "auth":"none", "ok":False}
    status, session, ctype, init = post({
        "jsonrpc":"2.0", "id":1, "method":"initialize",
        "params":{"protocolVersion":"2025-03-26","capabilities":{},
                  "clientInfo":{"name":"psi-personal-probe","version":"1.0.0"}}
    })
    if "error" in init:
        raise RuntimeError("initialize failed: " + json.dumps(init["error"])[:500])
    report.update({"initializeHttp":status,"contentType":ctype,
                   "protocol":init.get("result",{}).get("protocolVersion"),
                   "serverInfo":init.get("result",{}).get("serverInfo"),
                   "sessionIdReceived":bool(session)})
    # tools/list is the decisive compatibility check; no notification required.
    protocol = init.get("result",{}).get("protocolVersion") or "2025-03-26"\n    _, session, _, listed = post({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}},session,protocol)
    tools = listed.get("result",{}).get("tools",[])
    report["toolNames"] = [t.get("name") for t in tools]
    tool = next((t for t in tools if t.get("name")=="cm_get_stock_quote"),None)
    if not tool:
        raise RuntimeError("cm_get_stock_quote absent from tools/list")
    report["quoteInputSchema"] = tool.get("inputSchema")
    _, session, _, called = post({"jsonrpc":"2.0","id":3,"method":"tools/call",
        "params":{"name":"cm_get_stock_quote","arguments":{"symbol":"INFY"}}},session)
    result = called.get("result",{})
    texts = [x.get("text","") for x in result.get("content",[]) if isinstance(x,dict) and x.get("type")=="text"]
    report["isError"] = result.get("isError",False)
    if texts:
        report["quoteText"] = texts[:2]
        try:
            parsed=json.loads(texts[0])
            report["quoteJson"]=parsed
            report["softError"]=parsed.get("error") if isinstance(parsed,dict) else None
        except Exception:
            report["quoteJsonParseError"]=True
    report["ok"] = bool(texts) and not report["isError"] and not report.get("softError")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit("NSE MCP did not return a valid INFY quote")

if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"ok":False,"error":str(exc),"checkedAt":datetime.now(timezone.utc).isoformat()},indent=2))
        raise
