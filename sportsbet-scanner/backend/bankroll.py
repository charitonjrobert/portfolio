class Bankroll:
    def __init__(self, initial=1000.0):
        self.initial = initial
        self.balance = initial
        self.bets = []

    def kelly_stake(self, probability, decimal_odds, fraction=0.25):
        if decimal_odds <= 1:
            return 0.0
        b = decimal_odds - 1
        p = probability
        q = 1.0 - p
        full_kelly = (b * p - q) / b
        if full_kelly <= 0:
            return 0.0
        return round(self.balance * full_kelly * fraction, 2)

    def place_bet(self, stake, odds, outcome_label, edge_pct, event_label=""):
        if stake <= 0 or stake > self.balance:
            return None
        self.balance -= stake
        bet = {
            "event": event_label,
            "outcome": outcome_label,
            "stake": stake,
            "odds": odds,
            "edge_pct": edge_pct,
            "status": "open",
        }
        self.bets.append(bet)
        return bet

    def settle(self, bet_index, won):
        bet = self.bets[bet_index]
        if bet["status"] != "open":
            return None
        if won:
            profit = bet["stake"] * (bet["odds"] - 1)
            self.balance += bet["stake"] + profit
            bet["profit"] = round(profit, 2)
        else:
            bet["profit"] = -round(bet["stake"], 2)
        bet["status"] = "won" if won else "lost"
        return bet

    def summary(self):
        settled = [b for b in self.bets if b["status"] != "open"]
        won = [b for b in settled if b["status"] == "won"]
        total_staked = sum(b["stake"] for b in settled)
        profit = sum(b.get("profit", 0) for b in settled)
        roi = (profit / total_staked * 100) if total_staked else 0.0
        return {
            "initial": self.initial,
            "balance": round(self.balance, 2),
            "profit": round(profit, 2),
            "total_bets": len(settled),
            "won": len(won),
            "lost": len(settled) - len(won),
            "win_rate_pct": round(len(won) / len(settled) * 100, 1) if settled else 0.0,
            "roi_pct": round(roi, 2),
        }