#!/bin/bash

BASE_URL="https://aiserver.digitrends.sa"
PASS=0
FAIL=0

green="\033[32m"
red="\033[31m"
reset="\033[0m"

check() {
    local description="$1"
    local expected="$2"
    local actual="$3"

    if echo "$actual" | grep -q "$expected"; then
        echo -e "${green}PASS${reset} — $description"
        ((PASS++))
    else
        echo -e "${red}FAIL${reset} — $description"
        echo "       Expected to contain: $expected"
        echo "       Got: $actual"
        ((FAIL++))
    fi
}

echo "========================================"
echo "  MCP Auth Security Test Suite"
echo "========================================"
echo ""

# 1. OAuth metadata endpoint exists
echo "--- OAuth Metadata ---"
RESP=$(curl -s "$BASE_URL/.well-known/oauth-authorization-server")
check "Metadata endpoint returns issuer" "issuer" "$RESP"
check "Metadata has authorization_endpoint" "authorization_endpoint" "$RESP"
check "Metadata has token_endpoint" "token_endpoint" "$RESP"
check "Metadata has jwks_uri" "jwks_uri" "$RESP"
check "Metadata points to correct Auth0 domain" "digitrends.us.auth0.com" "$RESP"
echo ""

# 2. No token → 401
echo "--- No Token ---"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
check "No token returns 401" "401" "$RESP"
echo ""

# 3. Empty Bearer token → 401
echo "--- Empty Token ---"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer " \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
check "Empty Bearer token returns 401" "401" "$RESP"
echo ""

# 4. Random fake token → 401
echo "--- Fake Token ---"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer thisisafaketoken123456" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
check "Fake token returns 401" "401" "$RESP"
echo ""

# 5. Tampered JWT (valid structure but wrong signature) → 401
echo "--- Tampered JWT ---"
FAKE_JWT="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkhhY2tlciIsImF1ZCI6Imh0dHBzOi8vYWlzZXJ2ZXIuZGlnaXRyZW5kcy5zYS9tY3AiLCJpYXQiOjE1MTYyMzkwMjJ9.fakesignature"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $FAKE_JWT" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
check "Tampered JWT returns 401" "401" "$RESP"
echo ""

# 6. Wrong auth scheme (Basic instead of Bearer) → 401
echo "--- Wrong Auth Scheme ---"
RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic dXNlcjpwYXNzd29yZA==" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
check "Basic auth scheme returns 401" "401" "$RESP"
echo ""

# 7. WWW-Authenticate header present on 401
echo "--- WWW-Authenticate Header ---"
RESP=$(curl -s -D - -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
check "401 includes WWW-Authenticate header" "WWW-Authenticate" "$RESP"
check "WWW-Authenticate points to oauth metadata" "oauth-authorization-server" "$RESP"
echo ""

# 8. Digitrends app still works (not broken)
echo "--- Digitrends App Health ---"
RESP=$(curl -s -o /dev/null -w "%{http_code}" "https://aiserver.digitrends.sa/")
check "Digitrends homepage still returns 200 or 307" "30\|200" "$RESP"
echo ""

# 9. API endpoint still works
RESP=$(curl -s -o /dev/null -w "%{http_code}" "https://aiserver.digitrends.sa/api/health")
check "Digitrends /api still reachable (not 502/504)" "^[^5]" "$RESP"
echo ""

echo "========================================"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "========================================"
