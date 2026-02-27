# ODR Troubleshooting - `AccessStatus=DeniedBySystem`

## Symptom

When trying to use the custom registered MCP server via ODR CLI:

```text
Client '<id>' access to server 'calcslive-excel-mcp-0.1.0' denied.
PackageFamilyName='(null)', ContainsValidStaticResponses=True, TestMode=False, AccessStatus=DeniedBySystem.
```

## What This Means

- The server registration itself can succeed.
- The current ODR client context (plain CLI with no package family identity) is not authorized to invoke that server.
- `TestMode=False` in logs suggests developer/test mode policy is not enabled for this access path.

## Checks Performed

1. ODR runtime verified
   - `odr --version` -> `0.1.1`
2. MCP command surface verified
   - `odr mcp --help`
3. Custom server registration verified
   - `odr mcp add "...\excel-mcp\manifest.json"` -> success
4. Invocation attempt
   - `odr mcp run --proxy calcslive-excel-mcp-0.1.0` -> denied by system
5. Static responses added to manifest
   - still denied by system
6. Remote server path attempted (streamable-http and sse)
   - `odr mcp add <name> --uri http://127.0.0.1:8000/mcp` -> failed to connect
   - `odr mcp add <name> --uri http://127.0.0.1:8000/sse` -> failed to connect

## Likely Root Causes

- ODR policy requires a trusted package/client identity for invoking custom on-device servers.
- CLI context has `PackageFamilyName='(null)'`, so access is denied.
- Remote URI validation path from ODR may not be able to connect to loopback in current service/client context.

## Practical Workarounds (Hackathon)

1. Keep the stable MVP path as primary:
   - Azure-backed agent + local Excel bridge REST flow.
2. Keep ODR evidence as partial proof:
   - runtime installed
   - MCP registration works
   - troubleshooting log documents policy gate clearly.
3. Frame ODR integration as in-progress with explicit next step:
   - enable supported test mode/allowlist or run via approved host app client context.

## Next Steps to Unblock Fully

1. Validate official ODR test mode guidance for custom servers in dev environment.
2. Validate allowlist/permission model for custom server invocation by non-packaged clients.
3. Test invocation from an ODR-supported host app/client context (instead of raw CLI identity).
4. Re-run end-to-end ODR flow after policy adjustment.
