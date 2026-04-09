$headers = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json, text/event-stream"
}

$body = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

Invoke-RestMethod -Uri "http://localhost:8000/mcp" -Method POST -Headers $headers -Body $body
