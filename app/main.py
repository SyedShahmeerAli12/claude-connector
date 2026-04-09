import yfinance as yf
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("saudi-exchange-mcp")

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
    return {
        "symbol": symbol,
        "period": period,
        "records": records,
    }


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


if __name__ == "__main__":
    import uvicorn
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
