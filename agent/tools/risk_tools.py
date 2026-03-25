def analyze_portfolio(portfolio_id):
    # simulate data fetch
    exposure = 1200000

    # simple rule
    if exposure > 1_000_000:
        risk = "High"
        decision = "Reduce exposure"
    else:
        risk = "Low"
        decision = "Maintain position"

    return {
        "portfolio_id": portfolio_id,
        "exposure": exposure,
        "risk": risk,
        "decision": decision
    }