import csv
import io
import os
from collections import Counter, defaultdict


def parse_matches_csv(text):
    reader = csv.reader(io.StringIO(text))
    matches = []
    for row in reader:
        if len(row) < 5:
            continue
        try:
            home, away = row[1].strip(), row[2].strip()
            hg, ag = int(row[3]), int(row[4])
        except (ValueError, IndexError):
            continue
        matches.append(
            {"date": row[0].strip(), "home": home.lower(), "away": away.lower(),
             "home_goals": hg, "away_goals": ag}
        )
    return matches


class HistoryAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.matches = self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return parse_matches_csv(f.read())
        except Exception:
            return []

    def save_csv(self, text):
        parsed = parse_matches_csv(text)
        existing = []
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                existing = parse_matches_csv(f.read())
        seen = set((m["home"], m["away"], m["home_goals"], m["away_goals"], m["date"]) for m in existing)
        for m in parsed:
            key = (m["home"], m["away"], m["home_goals"], m["away_goals"], m["date"])
            if key not in seen:
                existing.append(m)
                seen.add(key)
        self.matches = existing
        with open(self.filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for m in existing:
                writer.writerow([m["date"], m["home"].title(), m["away"].title(), m["home_goals"], m["away_goals"]])
        return len(self.matches)

    def _resolve_team(self, query):
        q = query.strip().lower()
        if not q:
            return None
        for m in self.matches:
            if m["home"] == q:
                return m["home"]
            if m["away"] == q:
                return m["away"]
        for m in self.matches:
            if q in m["home"]:
                return m["home"]
            if q in m["away"]:
                return m["away"]
        return None

    def _team_match(self, actual, query):
        return actual == query or query in actual

    def h2h(self, team_a, team_b, limit=12):
        ta = self._resolve_team(team_a)
        tb = self._resolve_team(team_b)
        if not ta or not tb or ta == tb:
            return None
        head = [
            m for m in self.matches
            if (self._team_match(m["home"], ta) and self._team_match(m["away"], tb))
            or (self._team_match(m["home"], tb) and self._team_match(m["away"], ta))
        ]
        head.sort(key=lambda m: m["date"])
        head = head[-limit:]
        if not head:
            return None
        wins_a = wins_b = draws = 0
        for m in head:
            if m["home"] == ta:
                ha, aa = m["home_goals"], m["away_goals"]
            else:
                ha, aa = m["away_goals"], m["home_goals"]
            if ha > aa:
                wins_a += 1
            elif ha < aa:
                wins_b += 1
            else:
                draws += 1
        return {
            "team_a": ta.title(),
            "team_b": tb.title(),
            "matches": len(head),
            "wins_a": wins_a,
            "draws": draws,
            "wins_b": wins_b,
            "last": [
                {"date": m["date"], "home": m["home"].title(), "away": m["away"].title(),
                 "score": f"{m['home_goals']}-{m['away_goals']}"}
                for m in head
            ],
        }

    def scoreline_frequency(self, team_a, team_b, limit=12):
        h2h = self.h2h(team_a, team_b, limit=limit)
        if not h2h:
            return []
        counter = Counter()
        for m in h2h["last"]:
            counter[m["score"]] += 1
        ranked = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
        return [{"score": s, "count": c, "pct": round(c / len(h2h["last"]) * 100, 1)} for s, c in ranked]

    def repeated_patterns(self, team_a, team_b, limit=12):
        freq = self.scoreline_frequency(team_a, team_b, limit=limit)
        patterns = [f for f in freq if f["count"] >= 2]
        return patterns

    def goal_averages(self, team_a, team_b, limit=12):
        h2h = self.h2h(team_a, team_b, limit=limit)
        if not h2h:
            return None
        scored_a, conceded_a = [], []
        for m in h2h["last"]:
            if m["home"].lower() == team_a.lower():
                scored_a.append(int(m["score"].split("-")[0]))
                conceded_a.append(int(m["score"].split("-")[1]))
            else:
                scored_a.append(int(m["score"].split("-")[1]))
                conceded_a.append(int(m["score"].split("-")[0]))
        n = len(scored_a)
        return {
            "team_a_avg_scored": round(sum(scored_a) / n, 2),
            "team_a_avg_conceded": round(sum(conceded_a) / n, 2),
        }

    def lambdas(self, team_a, team_b, limit=12, min_matches=6):
        h2h = self.h2h(team_a, team_b, limit=limit)
        if not h2h or h2h["matches"] < min_matches:
            return None
        home_goals, away_goals = [], []
        for m in h2h["last"]:
            hg, ag = m["score"].split("-")
            home_goals.append(int(hg))
            away_goals.append(int(ag))
        n = len(home_goals)
        return {
            "home": max(0.1, round(sum(home_goals) / n, 2)),
            "away": max(0.1, round(sum(away_goals) / n, 2)),
            "matches": n,
        }

    def overall(self):
        total = len(self.matches)
        return {
            "total_matches": total,
            "teams": sorted({m["home"] for m in self.matches} | {m["away"] for m in self.matches}),
        }