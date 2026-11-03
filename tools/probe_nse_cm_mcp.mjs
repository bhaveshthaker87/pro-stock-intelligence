import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const endpoint = "https://mcp.nseindia.in/cmmkt/mcp";
const report = { endpoint, checkedAt: new Date().toISOString(), auth: "none", ok: false };
const client = new Client({ name: "pro-stock-intelligence-personal", version: "1.0.0" });
const transport = new StreamableHTTPClientTransport(new URL(endpoint), {
  requestInit: { headers: { "User-Agent": "ProStockIntelligence-personal-research/1.0" } },
});
try {
  await client.connect(transport, { timeout: 30000 });
  const listed = await client.listTools(undefined, { timeout: 30000 });
  report.toolNames = listed.tools.map((tool) => tool.name);
  const quoteTool = listed.tools.find((tool) => tool.name === "cm_get_stock_quote");
  if (!quoteTool) throw new Error("cm_get_stock_quote is not published by the NSE endpoint");
  report.quoteInputSchema = quoteTool.inputSchema;
  const result = await client.callTool(
    { name: "cm_get_stock_quote", arguments: { symbol: "INFY" } },
    undefined,
    { timeout: 30000 },
  );
  report.isError = Boolean(result.isError);
  const textBlock = result.content?.find((item) => item.type === "text");
  if (textBlock?.text) {
    try {
      report.quote = JSON.parse(textBlock.text);
    } catch {
      report.quoteText = textBlock.text.slice(0, 2000);
    }
  }
  if (report.quote?.error) throw new Error("NSE tool returned an application error: " + String(report.quote.error));
  if (report.isError) throw new Error("NSE MCP tools/call returned isError=true");
  if (!report.quote) throw new Error("NSE quote response did not contain a JSON text block");
  report.ok = true;
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  report.error = String(error?.message || error);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  await client.close().catch(() => {});
}
