import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime

# Adjust path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models import UserPortfolio, PortfolioAsset, RebalanceLog
from ml_engine.predictor import run_pipeline
from ml_engine.sentiment_analyzer import FinancialSentimentAnalyzer

# Enterprise-grade ESG ratings lookup directory
TICKER_ESG_SCORES = {
    "AAPL": 82.0,
    "MSFT": 85.0,
    "TSLA": 72.0,
    "GOOGL": 78.0,
    "AMZN": 64.0,
    "NVDA": 75.0,
    "JPM": 61.0,
    "XOM": 35.0,
    "NEE": 92.0,   # NextEra Energy (Leader in Clean Energy)
    "ENPH": 88.0,  # Enphase Energy (Solar leader)
}

DEFAULT_TICKERS = list(TICKER_ESG_SCORES.keys())

class PortfolioManager:
    """
    Manages user portfolios, executes transactions, and performs autonomous
    portfolio optimization based on ML forecasts, ESG ratings, and Sentiment.
    """

    def __init__(self, db: Session):
        self.db = db
        self.sentiment_analyzer = FinancialSentimentAnalyzer()

    def get_or_create_portfolio(self, username: str) -> UserPortfolio:
        """Retrieves user portfolio or initializes one with $100k cash."""
        portfolio = self.db.query(UserPortfolio).filter(UserPortfolio.username == username).first()
        if not portfolio:
            portfolio = UserPortfolio(
                username=username,
                total_value=100000.0,
                cash=100000.0,
                risk_tolerance="moderate",
                target_esg_score=70.0,
                current_esg_score=0.0
            )
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)
        return portfolio

    def update_asset_prices(self, portfolio: UserPortfolio) -> float:
        """
        Fetches current market prices and updates database assets.
        Returns the new total valuation of all assets (excluding cash).
        """
        import yfinance as yf
        assets_value = 0.0

        for asset in portfolio.assets:
            if asset.shares > 0:
                try:
                    ticker = yf.Ticker(asset.ticker)
                    # Fetch fast historical info
                    history = ticker.history(period="1d")
                    if not history.empty:
                        current_price = history['Close'].iloc[-1]
                        asset.current_price = round(current_price, 2)
                        assets_value += asset.shares * current_price
                except Exception as e:
                    print(f"Error updating price for {asset.ticker}: {e}")
                    # Keep previous current_price
                    assets_value += asset.shares * asset.current_price

        portfolio.total_value = round(portfolio.cash + assets_value, 2)
        self.db.commit()
        return assets_value

    def calculate_utility_scores(self, portfolio: UserPortfolio, tickers: list) -> dict:
        """
        Calculates an investment utility score for each ticker combining:
        1. ML predicted returns
        2. Financial news sentiment
        3. Asset ESG scores
        Weighted by user risk tolerance.
        """
        import yfinance as yf
        scores = {}

        # Risk tolerance weights
        # Aggressive prioritizes returns; Conservative prioritizes ESG/low volatility; Moderate balances both.
        risk_map = {
            "conservative": {"return": 0.2, "esg": 0.6, "sentiment": 0.2},
            "moderate":     {"return": 0.4, "esg": 0.3, "sentiment": 0.3},
            "aggressive":   {"return": 0.6, "esg": 0.1, "sentiment": 0.3}
        }

        weights = risk_map.get(portfolio.risk_tolerance.lower(), risk_map["moderate"])

        for ticker in tickers:
            # 1. Get ML Return Prediction
            ml_result = run_pipeline(ticker, forecast_days=5)
            predicted_return = 0.0
            current_price = 100.0

            if ml_result["success"]:
                predicted_return = ml_result["prediction"]["predicted_return"]
                current_price = ml_result["prediction"]["current_price"]

            # 2. Get Real-time Sentiment Score
            sentiment = 0.0
            try:
                t_obj = yf.Ticker(ticker)
                news = t_obj.news or []
                if news:
                    sentiment = self.sentiment_analyzer.analyze_batch(news)
            except Exception as e:
                print(f"Error fetching sentiment for {ticker}: {e}")

            # 3. Get ESG Score
            esg = TICKER_ESG_SCORES.get(ticker, 50.0)

            # Normalize inputs into standardized scales for Utility computation
            # Predicted Return: scaled around expected returns (e.g. 5% = 1.0, -5% = -1.0)
            scaled_return = max(-2.0, min(2.0, predicted_return / 0.05))

            # Sentiment: Already in range [-1.0, 1.0]
            scaled_sentiment = sentiment

            # ESG Score: scale [0, 100] to [-1.0, 1.0] where 70 is neutral (0.0)
            scaled_esg = (esg - 70.0) / 30.0

            # Calculate utility
            utility = (
                weights["return"] * scaled_return +
                weights["esg"] * scaled_esg +
                weights["sentiment"] * scaled_sentiment
            )

            scores[ticker] = {
                "utility": round(utility, 4),
                "predicted_return": predicted_return,
                "current_price": current_price,
                "sentiment": sentiment,
                "esg_score": esg
            }

        return scores

    def rebalance(self, username: str, tickers: list = None) -> dict:
        """
        Executes the autonomous rebalancing pipeline:
        - Evaluates utility scores for target tickers.
        - Checks and solves for the ESG compliance constraint.
        - Executes sells of declining assets and buys of optimal assets.
        - Commits to the DB and logs the results.
        """
        if tickers is None:
            tickers = DEFAULT_TICKERS

        portfolio = self.get_or_create_portfolio(username)

        # 1. Update prices of existing assets first to get accurate portfolio valuation
        self.update_asset_prices(portfolio)
        total_funds = portfolio.total_value

        # Record pre-rebalance scores
        old_esg = portfolio.current_esg_score

        # 2. Generate Utility Metrics
        metrics = self.calculate_utility_scores(portfolio, tickers)

        # 3. Allocation Optimization: Filter for positive utility
        valid_candidates = {t: m for t, m in metrics.items() if m["utility"] > -0.5}

        if not valid_candidates:
            # Fallback to high ESG leaders if everything is poor
            valid_candidates = {t: metrics[t] for t in ["NEE", "ENPH", "MSFT"]}

        # Distribute weights proportional to utility scores
        utilities = {t: max(0.1, m["utility"] + 1.0) for t, m in valid_candidates.items()} # Shift so all weights are positive
        total_utility = sum(utilities.values())

        target_weights = {t: u / total_utility for t, u in utilities.items()}

        # 4. Enforce ESG Constraint: Check if weighted ESG meets user target
        weighted_esg = sum(target_weights[t] * metrics[t]["esg_score"] for t in target_weights)

        # If ESG target is not met, dynamically tilt portfolio to higher-ESG assets
        if weighted_esg < portfolio.target_esg_score:
            # Boost utilities of assets with ESG score higher than user target
            esg_boost_factor = 1.5
            for t in target_weights:
                if metrics[t]["esg_score"] >= portfolio.target_esg_score:
                    utilities[t] *= esg_boost_factor

            # Re-calculate weights
            total_utility = sum(utilities.values())
            target_weights = {t: u / total_utility for t, u in utilities.items()}
            weighted_esg = sum(target_weights[t] * metrics[t]["esg_score"] for t in target_weights)

        # 5. Execute Trades (mock execution)
        # Sell existing assets that are not in target_weights or have excess shares
        trade_logs = []
        current_assets = {asset.ticker: asset for asset in portfolio.assets}

        # Liquidation and scaling down
        for ticker, asset in list(current_assets.items()):
            target_weight = target_weights.get(ticker, 0.0)
            target_value = total_funds * target_weight
            current_value = asset.shares * asset.current_price

            if current_value > target_value:
                # Sell excess shares
                val_to_sell = current_value - target_value
                shares_to_sell = round(val_to_sell / asset.current_price, 4)
                if shares_to_sell >= asset.shares:
                    # Full liquidation
                    portfolio.cash += current_value
                    trade_logs.append(f"Sold {asset.shares:.2f} shares of {ticker} (Full liquidation)")
                    self.db.delete(asset)
                else:
                    # Partial sale
                    asset.shares -= shares_to_sell
                    portfolio.cash += val_to_sell
                    trade_logs.append(f"Sold {shares_to_sell:.2f} shares of {ticker} for ${val_to_sell:.2f}")

        self.db.commit() # Save intermediate sales cash

        # Buy/scale up assets with target weights
        for ticker, weight in target_weights.items():
            target_value = total_funds * weight
            asset = self.db.query(PortfolioAsset).filter(
                PortfolioAsset.portfolio_id == portfolio.id,
                PortfolioAsset.ticker == ticker
            ).first()

            current_shares = asset.shares if asset else 0.0
            price = metrics[ticker]["current_price"]
            current_value = current_shares * price

            if target_value > current_value:
                # Buy additional shares
                val_to_buy = target_value - current_value
                # Ensure we have enough cash
                if portfolio.cash < val_to_buy:
                    val_to_buy = portfolio.cash

                if val_to_buy > 10.0: # Minimum trade threshold
                    shares_to_buy = round(val_to_buy / price, 4)
                    portfolio.cash -= val_to_buy

                    if asset:
                        # Update holding
                        total_cost = (asset.shares * asset.avg_buy_price) + val_to_buy
                        asset.shares += shares_to_buy
                        asset.avg_buy_price = round(total_cost / asset.shares, 2)
                        asset.current_price = price
                    else:
                        # New holding
                        asset = PortfolioAsset(
                            portfolio_id=portfolio.id,
                            ticker=ticker,
                            shares=shares_to_buy,
                            avg_buy_price=price,
                            current_price=price,
                            esg_score=metrics[ticker]["esg_score"]
                        )
                        self.db.add(asset)

                    trade_logs.append(f"Bought {shares_to_buy:.2f} shares of {ticker} for ${val_to_buy:.2f}")

        # Update current ESG score
        portfolio.current_esg_score = round(weighted_esg, 2)

        # 6. Log the rebalance event
        action_summary = " | ".join(trade_logs) if trade_logs else "No changes required. Portfolio aligned with targets."
        avg_sentiment = sum(m["sentiment"] for m in metrics.values()) / len(metrics) if metrics else 0.0

        log = RebalanceLog(
            portfolio_id=portfolio.id,
            action_summary=action_summary,
            old_esg_score=round(old_esg, 2),
            new_esg_score=round(weighted_esg, 2),
            old_sentiment=0.0, # Placeholder
            new_sentiment=round(avg_sentiment, 2)
        )
        self.db.add(log)

        # Commit to save all new assets and relations
        self.db.commit()
        self.db.refresh(portfolio)

        # Re-verify valuation
        self.update_asset_prices(portfolio)
        self.db.commit()

        return {
            "success": True,
            "portfolio": {
                "username": portfolio.username,
                "total_value": portfolio.total_value,
                "cash": round(portfolio.cash, 2),
                "esg_score": portfolio.current_esg_score,
                "target_esg_score": portfolio.target_esg_score,
                "risk_tolerance": portfolio.risk_tolerance
            },
            "metrics": metrics,
            "actions": trade_logs,
            "weighted_esg": round(weighted_esg, 2)
        }

if __name__ == "__main__":
    from backend.database import engine, Base, SessionLocal
    # Initialize SQLite tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    print("Testing Portfolio Rebalancer for user 'demo_investor'...")
    pm = PortfolioManager(db)

    # Run mock rebalance (will fetch real yahoo finance data)
    result = pm.rebalance("demo_investor")

    print("\nRebalance Actions Executed:")
    for action in result["actions"]:
        print(f" - {action}")

    print(f"\nNew Portfolio Valuation: ${result['portfolio']['total_value']:,}")
    print(f"Portfolio ESG Score: {result['portfolio']['esg_score']}")
    db.close()
