from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import sys

# Ensure backend and ml_engine are in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base, get_db
from backend.models import UserPortfolio, PortfolioAsset, RebalanceLog
from backend.portfolio_manager import PortfolioManager, TICKER_ESG_SCORES, DEFAULT_TICKERS

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise FinTech Intelligence & Autonomous Portfolio Manager API",
    description="Full-stack AI-driven portfolio management API with ESG constraints and news sentiment indexing.",
    version="1.0.0"
)

# Enable CORS for frontend dashboard connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for validation
class PortfolioConfigUpdate(BaseModel):
    risk_tolerance: Optional[str] = None  # conservative, moderate, aggressive
    target_esg_score: Optional[float] = None  # 0 to 100

class AssetResponse(BaseModel):
    ticker: str
    shares: float
    avg_buy_price: float
    current_price: float
    esg_score: float
    current_value: float

    class Config:
        from_attributes = True

class PortfolioResponse(BaseModel):
    username: str
    total_value: float
    cash: float
    risk_tolerance: str
    target_esg_score: float
    current_esg_score: float
    assets: List[AssetResponse]

    class Config:
        from_attributes = True

class RebalanceLogResponse(BaseModel):
    id: int
    timestamp: str
    action_summary: str
    old_esg_score: float
    new_esg_score: float
    old_sentiment: float
    new_sentiment: float

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Enterprise FinTech Intelligence API",
        "version": "1.0.0"
    }

@app.get("/api/portfolio/{username}", response_model=PortfolioResponse)
def get_portfolio(username: str, db: Session = Depends(get_db)):
    pm = PortfolioManager(db)
    portfolio = pm.get_or_create_portfolio(username)

    # Update prices on fetch to ensure live valuation
    pm.update_asset_prices(portfolio)

    # Formulate asset list
    assets_out = []
    for asset in portfolio.assets:
        if asset.shares > 0:
            assets_out.append(AssetResponse(
                ticker=asset.ticker,
                shares=round(asset.shares, 4),
                avg_buy_price=round(asset.avg_buy_price, 2),
                current_price=round(asset.current_price, 2),
                esg_score=asset.esg_score,
                current_value=round(asset.shares * asset.current_price, 2)
            ))

    return PortfolioResponse(
        username=portfolio.username,
        total_value=round(portfolio.total_value, 2),
        cash=round(portfolio.cash, 2),
        risk_tolerance=portfolio.risk_tolerance,
        target_esg_score=portfolio.target_esg_score,
        current_esg_score=portfolio.current_esg_score,
        assets=assets_out
    )

@app.post("/api/portfolio/{username}/config")
def update_portfolio_config(username: str, config: PortfolioConfigUpdate, db: Session = Depends(get_db)):
    pm = PortfolioManager(db)
    portfolio = pm.get_or_create_portfolio(username)

    if config.risk_tolerance is not None:
        val = config.risk_tolerance.lower()
        if val not in ["conservative", "moderate", "aggressive"]:
            raise HTTPException(status_code=400, detail="Risk tolerance must be: 'conservative', 'moderate', or 'aggressive'")
        portfolio.risk_tolerance = val

    if config.target_esg_score is not None:
        if not (0 <= config.target_esg_score <= 100):
            raise HTTPException(status_code=400, detail="Target ESG score must be between 0 and 100")
        portfolio.target_esg_score = config.target_esg_score

    db.commit()
    db.refresh(portfolio)

    return {
        "success": True,
        "message": f"Updated configuration for {username}",
        "risk_tolerance": portfolio.risk_tolerance,
        "target_esg_score": portfolio.target_esg_score
    }

@app.post("/api/portfolio/{username}/rebalance")
def trigger_rebalance(username: str, tickers: Optional[List[str]] = None, db: Session = Depends(get_db)):
    pm = PortfolioManager(db)
    try:
        result = pm.rebalance(username, tickers)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebalancing failed: {str(e)}")

@app.get("/api/portfolio/{username}/history", response_model=List[RebalanceLogResponse])
def get_rebalance_history(username: str, db: Session = Depends(get_db)):
    pm = PortfolioManager(db)
    portfolio = pm.get_or_create_portfolio(username)

    logs = db.query(RebalanceLog).filter(RebalanceLog.portfolio_id == portfolio.id).order_by(RebalanceLog.timestamp.desc()).all()

    return [
        RebalanceLogResponse(
            id=log.id,
            timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            action_summary=log.action_summary,
            old_esg_score=log.old_esg_score,
            new_esg_score=log.new_esg_score,
            old_sentiment=log.old_sentiment,
            new_sentiment=log.new_sentiment
        )
        for log in logs
    ]

@app.get("/api/market-data")
def get_market_data(db: Session = Depends(get_db)):
    """Returns predictions, ESG scores, and news sentiments for all monitored assets."""
    import yfinance as yf
    from ml_engine.sentiment_analyzer import FinancialSentimentAnalyzer
    from ml_engine.predictor import run_pipeline

    sentiment_analyzer = FinancialSentimentAnalyzer()
    out = []

    for ticker in DEFAULT_TICKERS:
        # Get live price
        current_price = 0.0
        try:
            t = yf.Ticker(ticker)
            history = t.history(period="1d")
            if not history.empty:
                current_price = history['Close'].iloc[-1]
        except:
            pass

        # Get ML prediction
        ml_res = run_pipeline(ticker, forecast_days=5)
        predicted_price = 0.0
        predicted_return = 0.0
        if ml_res["success"]:
            predicted_price = ml_res["prediction"]["predicted_price"]
            predicted_return = ml_res["prediction"]["predicted_return"]

        # Get Sentiment
        sentiment = 0.0
        try:
            news = t.news or []
            if news:
                sentiment = sentiment_analyzer.analyze_batch(news)
        except:
            pass

        out.append({
            "ticker": ticker,
            "company_name": yf.Ticker(ticker).info.get("longName", ticker),
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "predicted_return": round(predicted_return * 100, 2),  # percentage
            "esg_score": TICKER_ESG_SCORES[ticker],
            "sentiment_score": sentiment
        })

    return out

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
