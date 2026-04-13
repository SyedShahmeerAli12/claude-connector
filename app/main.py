import os
import httpx
import yfinance as yf
from jose import jwt, JWTError
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# --- Auth0 config (set these in .env) ---
AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]       # e.g. your-tenant.us.auth0.com
AUTH0_AUDIENCE = os.environ["AUTH0_AUDIENCE"]   # e.g. https://aiserver.digitrends.sa/mcp

_jwks_cache = None


async def get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


async def verify_token(token: str) -> dict:
    jwks = await get_jwks()
    try:
        return jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# --- MCP server ---
mcp = FastMCP(
    "saudi-exchange-mcp",
    transport_security=TransportSecuritySettings(
        allowed_hosts=["aiserver.digitrends.sa", "aiserver.digitrends.sa:443"],
        allowed_origins=["https://aiserver.digitrends.sa"],
    ),
)

TOP_SAUDI_STOCKS = {
    "2222.SR": "Saudi Aramco",
    "7010.SR": "STC",
    "2010.SR": "SABIC",
    "1180.SR": "Al Rajhi Bank",
    "2350.SR": "Saudi Kayan",
    "1120.SR": "Al Jazira Bank",
    "2380.SR": "Petro Rabigh",
    "4200.SR": "Saudi Telecom",
    "1211.SR": "Maaden",
    "3010.SR": "Saudi Cement",
}


@mcp.tool()
def get_stock_price(symbol: str) -> dict:
    """
    Get real-time stock price for a Saudi Exchange listed company.
    Example symbols: 2222.SR (Aramco), 7010.SR (STC), 2010.SR (SABIC)
    """
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    return {
        "symbol": symbol,
        "price": round(info.last_price, 2),
        "currency": "SAR",
        "previous_close": round(info.previous_close, 2),
        "change": round(info.last_price - info.previous_close, 2),
        "change_percent": round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2),
        "volume": info.last_volume,
    }


@mcp.tool()
def get_top_saudi_stocks() -> list:
    """
    Get current prices for top 10 Saudi Exchange (Tadawul) listed companies.
    """
    results = []
    for symbol, name in TOP_SAUDI_STOCKS.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            change_pct = round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2)
            results.append({
                "symbol": symbol,
                "name": name,
                "price": round(info.last_price, 2),
                "currency": "SAR",
                "change_percent": change_pct,
                "trend": "▲" if change_pct >= 0 else "▼",
            })
        except Exception:
            results.append({"symbol": symbol, "name": name, "error": "data unavailable"})
    return results


@mcp.tool()
def get_stock_history(symbol: str, period: str = "1mo") -> dict:
    """
    Get historical price data for a Saudi stock.
    symbol: e.g. 2222.SR
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    if hist.empty:
        return {"error": f"No data found for {symbol}"}
    records = []
    for date, row in hist.iterrows():
        records.append({
            "date": str(date.date()),
            "open": round(row["Open"], 2),
            "close": round(row["Close"], 2),
            "high": round(row["High"], 2),
            "low": round(row["Low"], 2),
            "volume": int(row["Volume"]),
        })
    return {"symbol": symbol, "period": period, "records": records}


@mcp.tool()
def get_stock_info(symbol: str) -> dict:
    """
    Get detailed company information for a Saudi Exchange listed stock.
    Example: 2222.SR for Saudi Aramco
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "symbol": symbol,
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap", "N/A"),
        "employees": info.get("fullTimeEmployees", "N/A"),
        "description": info.get("longBusinessSummary", "N/A")[:300] if info.get("longBusinessSummary") else "N/A",
        "website": info.get("website", "N/A"),
    }


# --- FastAPI outer app with auth middleware ---
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"error": "unauthorized", "message": "Bearer token required"},
                    headers={
                        "WWW-Authenticate": (
                            'Bearer realm="Saudi Exchange MCP",'
                            ' resource_metadata="https://aiserver.digitrends.sa'
                            '/.well-known/oauth-authorization-server"'
                        )
                    },
                )
            try:
                await verify_token(auth[7:])
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"error": e.detail})
        return await call_next(request)


app = FastAPI()
app.add_middleware(AuthMiddleware)


@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414) — points to Auth0."""
    return {
        "issuer": f"https://{AUTH0_DOMAIN}/",
        "authorization_endpoint": f"https://{AUTH0_DOMAIN}/authorize",
        "token_endpoint": f"https://{AUTH0_DOMAIN}/oauth/token",
        "jwks_uri": f"https://{AUTH0_DOMAIN}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["openid", "profile", "email"],
    }


# Mount MCP under the outer app
app.mount("/", mcp.streamable_http_app())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, forwarded_allow_ips="*")
