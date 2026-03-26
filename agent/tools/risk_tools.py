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
def calculate_var(portfolio_id):
    # simulate VaR calculation
    var_95 = 250000  # dummy value

    return {
        "portfolio_id": portfolio_id,
        "var_95": var_95,
        "confidence": "95%"
    }