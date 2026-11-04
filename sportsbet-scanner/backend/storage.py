import json
import os
import sqlite3
import time
from datetime import datetime


class Storage:
    def __init__(self, cache_file="odds_cache.json", db_file="bets.db"):
        self.cache_file = cache_file
        self.db_file = db_file
        # sidecar cu timpi de actualizare per liga: {sport_key: ts}
        self.meta_file = cache_file + ".meta.json"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_file)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS bets (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "event TEXT, outcome TEXT, stake REAL, odds REAL, edge_pct REAL, "
            "status TEXT, profit REAL)"
        )
        cols = [r[1] for r in conn.execute("PRAGMA table_info(bets)").fetchall()]
        if "sport_group" not in cols:
            conn.execute("ALTER TABLE bets ADD COLUMN sport_group TEXT DEFAULT ''")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "ts TEXT, sport TEXT, event TEXT, outcome TEXT, odds REAL, "
            "bookmaker TEXT, edge_pct REAL, pinned INTEGER DEFAULT 0)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "ts TEXT, role TEXT, content TEXT)"
        )
        # --- simulation wallet (13 Oct 2026): demo players + richer bet records ---
        conn.execute(
            "CREATE TABLE IF NOT EXISTS players (name TEXT PRIMARY KEY, balance REAL, "
            "initial REAL, created TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS watchlist (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "player TEXT, event_id TEXT, sport TEXT, league TEXT, home_team TEXT, away_team TEXT, "
            "commence_time TEXT, created TEXT, last_score TEXT, last_minute TEXT)"
        )
        wanted = {
            "player": "TEXT DEFAULT 'demo'",
            "event_id": "TEXT",
            "home_team": "TEXT",
            "away_team": "TEXT",
            "sport": "TEXT",
            "market": "TEXT DEFAULT 'h2h'",
            "commence_time": "TEXT",
            "bookmaker": "TEXT",
            "model_prob": "REAL",
            "side": "TEXT",
            "sport_key": "TEXT",
            "result_score": "TEXT",
            "settled_at": "TEXT",
            # --- sharp reference + CLV (decision Jay, 14 Oct 2026) ---
            "sharp_odds": "REAL",       # price at the sharp book when the bet was placed
            "sharp_prob": "REAL",       # margin-free market probability when placed
            "closing_odds": "REAL",     # sharp price captured near kick-off (CLV baseline)
            "closing_prob": "REAL",
            "closing_kind": "TEXT",     # 'pre' (before kick-off) or 'approx' (already started)
            "closing_at": "TEXT",
            "clv_pct": "REAL",          # (placed odds / closing odds - 1) * 100
        }
        cols = [r[1] for r in conn.execute("PRAGMA table_info(bets)").fetchall()]
        for name, decl in wanted.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE bets ADD COLUMN {name} {decl}")
        conn.commit()
        conn.close()

    # ---------- cache cote ----------

    def save_cache(self, events_by_sport):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(events_by_sport, f, ensure_ascii=False, indent=2)

    def load_cache(self):
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def merge_cache(self, updates):
        """Fuzioneaza evenimente proaspete peste cache-ul existent (pastreaza ligile
        aduse on-demand si pietele exotice; actualizeaza doar evenimentele cu acelasi id)."""
        cache = self.load_cache()
        merged = {}
        for g, evs in cache.items():
            if not isinstance(evs, list):
                continue
            for ev in evs:
                if not isinstance(ev, dict):
                    continue
                ev.setdefault("sport_group", g)
                merged[self._ev_key(ev, g)] = ev
        for g, evs in updates.items():
            for ev in evs:
                if not isinstance(ev, dict):
                    continue
                ev.setdefault("sport_group", g)
                merged[self._ev_key(ev, g)] = ev
        out = {}
        for ev in merged.values():
            g = ev.get("sport_group") or "other"
            out.setdefault(g, []).append(ev)
        self.save_cache(out)
        return out

    @staticmethod
    def _ev_key(ev, g):
        return ev.get("id") or f"{g}:{ev.get('home_team', '')}:{ev.get('away_team', '')}"

    def prune_expired(self, hours=48):
        """Drop events that started more than `hours` ago (no longer bettable).

        Keeps events without a parsable start time. Returns how many were removed.
        """
        cutoff = time.time() - float(hours) * 3600
        cache = self.load_cache()
        out = {}
        removed = 0
        for g, evs in cache.items():
            if not isinstance(evs, list):
                continue
            keep = []
            for ev in evs:
                if not isinstance(ev, dict):
                    continue
                ct = ev.get("commence_time")
                ts = None
                if ct:
                    try:
                        ts = datetime.fromisoformat(str(ct).replace("Z", "+00:00")).timestamp()
                    except (ValueError, TypeError):
                        ts = None
                if ts is not None and ts < cutoff:
                    removed += 1
                    continue
                keep.append(ev)
            if keep:
                out[g] = keep
        if removed:
            self.save_cache(out)
        return removed

    # ---------- TTL per liga (rubrici de sport) ----------

    def _load_meta(self):
        if not os.path.exists(self.meta_file):
            return {}
        try:
            with open(self.meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            return meta if isinstance(meta, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_meta(self, meta):
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)

    def league_age_hours(self, sport_key):
        """Cate ore de la ultimul fetch reusit al ligii; None daca nu exista in meta."""
        meta = self._load_meta()
        ts = meta.get(sport_key, {}).get("ts")
        if ts is None:
            return None
        return (time.time() - ts) / 3600.0

    def mark_league(self, sport_key, ts=None):
        """Marcheaza liga ca proaspat adusa (dupa un fetch real)."""
        meta = self._load_meta()
        meta[sport_key] = {"ts": ts if ts is not None else time.time()}
        self._save_meta(meta)

    # ---------- pariuri / snapshots ----------

    def add_bet(self, bet):
        conn = sqlite3.connect(self.db_file)
        conn.execute(
            "INSERT INTO bets (event, outcome, stake, odds, edge_pct, status, profit, sport_group) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                bet.get("event", ""),
                bet.get("outcome", ""),
                bet.get("stake", 0),
                bet.get("odds", 0),
                bet.get("edge_pct", 0),
                bet.get("status", "open"),
                bet.get("profit", 0),
                bet.get("sport_group", ""),
            ),
        )
        conn.commit()
        conn.close()

    def list_bets(self):
        conn = sqlite3.connect(self.db_file)
        rows = conn.execute("SELECT * FROM bets ORDER BY id DESC").fetchall()
        conn.close()
        cols = ["id", "event", "outcome", "stake", "odds", "edge_pct", "status", "profit", "sport_group"]
        return [dict(zip(cols, row)) for row in rows]

    # ---------- conversatii chat ----------

    def add_chat(self, role, content, ts=None):
        conn = sqlite3.connect(self.db_file)
        conn.execute(
            "INSERT INTO chats (ts, role, content) VALUES (?, ?, ?)",
            (ts or datetime.now().isoformat(timespec="seconds"), role, content),
        )
        conn.commit()
        conn.close()

    def list_chats(self, limit=200):
        conn = sqlite3.connect(self.db_file)
        rows = conn.execute(
            "SELECT id, ts, role, content FROM chats ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        rows.reverse()
        return [{"id": r[0], "ts": r[1], "role": r[2], "content": r[3]} for r in rows]

    def clear_chats(self):
        conn = sqlite3.connect(self.db_file)
        conn.execute("DELETE FROM chats")
        conn.commit()
        conn.close()

    def settle_bet(self, bet_id, won):
        conn = sqlite3.connect(self.db_file)
        row = conn.execute("SELECT * FROM bets WHERE id = ?", (bet_id,)).fetchone()
        if not row:
            conn.close()
            return None
        cols = ["id", "event", "outcome", "stake", "odds", "edge_pct", "status", "profit"]
        bet = dict(zip(cols, row))
        if bet["status"] != "open":
            conn.close()
            return None
        if won:
            profit = round(bet["stake"] * (bet["odds"] - 1), 2)
        else:
            profit = -round(bet["stake"], 2)
        status = "won" if won else "lost"
        conn.execute("UPDATE bets SET status = ?, profit = ? WHERE id = ?", (status, profit, bet_id))
        conn.commit()
        conn.close()
        bet["status"] = status
        bet["profit"] = profit
        return bet

    # ---------- portofel simulare (bani demo, decizie Jay 13 oct 2026) ----------

    DEFAULT_DEMO_BALANCE = 100.0

    def _bet_cols(self, conn):
        return [r[1] for r in conn.execute("PRAGMA table_info(bets)").fetchall()]

    def ensure_player(self, name, initial=None):
        name = (name or "demo").strip() or "demo"
        initial = self.DEFAULT_DEMO_BALANCE if initial is None else float(initial)
        conn = sqlite3.connect(self.db_file)
        row = conn.execute(
            "SELECT name, balance, initial, created FROM players WHERE name = ?", (name,)
        ).fetchone()
        if not row:
            created = datetime.now().isoformat(timespec="seconds")
            conn.execute(
                "INSERT INTO players (name, balance, initial, created) VALUES (?, ?, ?, ?)",
                (name, initial, initial, created),
            )
            conn.commit()
            row = (name, initial, initial, created)
        conn.close()
        return {"name": row[0], "balance": round(row[1], 2), "initial": round(row[2], 2), "created": row[3]}

    def add_balance(self, name, delta):
        player = self.ensure_player(name)
        balance = round(player["balance"] + float(delta), 2)
        conn = sqlite3.connect(self.db_file)
        conn.execute("UPDATE players SET balance = ? WHERE name = ?", (balance, player["name"]))
        conn.commit()
        conn.close()
        return balance

    def reset_player(self, name, balance=None):
        balance = self.DEFAULT_DEMO_BALANCE if balance is None else float(balance)
        player = self.ensure_player(name)
        conn = sqlite3.connect(self.db_file)
        conn.execute("UPDATE players SET balance = ? WHERE name = ?", (balance, player["name"]))
        conn.commit()
        conn.close()
        return balance

    def add_wallet_bet(self, bet):
        """Insert a full bet record (simulation). Returns the new id."""
        conn = sqlite3.connect(self.db_file)
        cur = conn.execute(
            "INSERT INTO bets (event, outcome, stake, odds, edge_pct, status, profit, sport_group, "
            "player, event_id, home_team, away_team, sport, market, commence_time, bookmaker, model_prob, "
            "side, sport_key, sharp_odds, sharp_prob) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                bet.get("event", ""),
                bet.get("outcome", ""),
                float(bet.get("stake", 0) or 0),
                float(bet.get("odds", 0) or 0),
                float(bet.get("edge_pct", 0) or 0),
                bet.get("status", "open"),
                float(bet.get("profit", 0) or 0),
                bet.get("sport_group", ""),
                bet.get("player", "demo"),
                str(bet.get("event_id", "") or ""),
                bet.get("home_team", ""),
                bet.get("away_team", ""),
                bet.get("sport", ""),
                bet.get("market", "h2h"),
                bet.get("commence_time", ""),
                bet.get("bookmaker", ""),
                bet.get("model_prob"),
                bet.get("side", ""),
                bet.get("sport_key", ""),
                bet.get("sharp_odds"),
                bet.get("sharp_prob"),
            ),
        )
        conn.commit()
        bet_id = cur.lastrowid
        conn.close()
        return bet_id

    def list_wallet_bets(self, player="demo", limit=250, only_open=False):
        conn = sqlite3.connect(self.db_file)
        cols = self._bet_cols(conn)
        sql = "SELECT * FROM bets WHERE COALESCE(player, 'demo') = ?"
        if only_open:
            sql += " AND status = 'open'"
        sql += " ORDER BY id DESC LIMIT ?"
        rows = conn.execute(sql, (player, limit)).fetchall()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]

    def list_open_bets(self):
        conn = sqlite3.connect(self.db_file)
        cols = self._bet_cols(conn)
        rows = conn.execute("SELECT * FROM bets WHERE status = 'open' ORDER BY id DESC").fetchall()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]

    def get_bet(self, bet_id):
        """One bet by id (any player, any status) - used by the match report."""
        conn = sqlite3.connect(self.db_file)
        cols = self._bet_cols(conn)
        row = conn.execute("SELECT * FROM bets WHERE id = ?", (bet_id,)).fetchone()
        conn.close()
        return dict(zip(cols, row)) if row else None

    def set_closing(self, bet_id, odds=None, prob=None, kind="pre", ts=None):
        """Store the sharp price captured near kick-off (the CLV baseline).

        Only fills the row once (`closing_odds IS NULL`) so a later, worse capture
        cannot overwrite the first good one.
        """
        conn = sqlite3.connect(self.db_file)
        conn.execute(
            "UPDATE bets SET closing_odds = ?, closing_prob = ?, closing_kind = ?, closing_at = ? "
            "WHERE id = ? AND closing_odds IS NULL",
            (odds, prob, kind, ts or datetime.now().isoformat(timespec="seconds"), bet_id),
        )
        conn.commit()
        conn.close()
        return True

    def resolve_bet(self, bet_id, won, score_text="", profit=None):
        """Settle a simulation bet with a real result and pay the winnings into the wallet."""
        conn = sqlite3.connect(self.db_file)
        cols = self._bet_cols(conn)
        row = conn.execute("SELECT * FROM bets WHERE id = ?", (bet_id,)).fetchone()
        if not row:
            conn.close()
            return None
        bet = dict(zip(cols, row))
        if bet.get("status") != "open":
            conn.close()
            return None
        stake = float(bet.get("stake") or 0)
        odds = float(bet.get("odds") or 0)
        profit = round(stake * (odds - 1), 2) if won else -round(stake, 2)
        status = "won" if won else "lost"
        # CLV: did we take a better price than the sharp closing line?
        closing = float(bet.get("closing_odds") or 0)
        clv = round((odds / closing - 1.0) * 100, 2) if closing > 1.0 and odds > 1.0 else None
        conn.execute(
            "UPDATE bets SET status = ?, profit = ?, result_score = ?, settled_at = ?, clv_pct = ? WHERE id = ?",
            (status, profit, score_text or "", datetime.now().isoformat(timespec="seconds"), clv, bet_id),
        )
        conn.commit()
        conn.close()
        if won:
            self.add_balance(bet.get("player") or "demo", round(stake * odds, 2))
        bet.update({"status": status, "profit": profit, "result_score": score_text, "clv_pct": clv})
        return bet

    def delete_bet(self, bet_id):
        conn = sqlite3.connect(self.db_file)
        cols = self._bet_cols(conn)
        row = conn.execute("SELECT * FROM bets WHERE id = ?", (bet_id,)).fetchone()
        if not row:
            conn.close()
            return None
        bet = dict(zip(cols, row))
        # an open bet returns its stake to the wallet
        if bet.get("status") == "open":
            self.add_balance(bet.get("player") or "demo", float(bet.get("stake") or 0))
        conn.execute("DELETE FROM bets WHERE id = ?", (bet_id,))
        conn.commit()
        conn.close()
        return bet

    # ---------- watchlist (meciuri urmarite -> alerte live) ----------

    def add_watch(self, item):
        conn = sqlite3.connect(self.db_file)
        player = item.get("player") or "demo"
        event_id = str(item.get("event_id") or "")
        row = conn.execute(
            "SELECT id FROM watchlist WHERE COALESCE(player,'demo') = ? AND event_id = ?",
            (player, event_id),
        ).fetchone()
        if row:
            conn.close()
            return row[0]
        cur = conn.execute(
            "INSERT INTO watchlist (player, event_id, sport, league, home_team, away_team, commence_time, created) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                player, event_id, item.get("sport", ""), item.get("league", ""),
                item.get("home_team", ""), item.get("away_team", ""), item.get("commence_time", ""),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        watch_id = cur.lastrowid
        conn.close()
        return watch_id

    def list_watch(self, player="demo"):
        conn = sqlite3.connect(self.db_file)
        cols = ["id", "player", "event_id", "sport", "league", "home_team", "away_team", "commence_time", "created"]
        rows = conn.execute(
            "SELECT id, player, event_id, sport, league, home_team, away_team, commence_time, created "
            "FROM watchlist WHERE COALESCE(player,'demo') = ? ORDER BY commence_time",
            (player,),
        ).fetchall()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]

    def remove_watch(self, watch_id):
        conn = sqlite3.connect(self.db_file)
        conn.execute("DELETE FROM watchlist WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()
        return True

    def add_snapshot(self, snap, keep_per_key=30):
        conn = sqlite3.connect(self.db_file)
        conn.execute(
            "INSERT INTO snapshots (ts, sport, event, outcome, odds, bookmaker, edge_pct, pinned) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
            (
                snap.get("ts", ""),
                snap.get("sport", ""),
                snap.get("event", ""),
                snap.get("outcome", ""),
                snap.get("odds", 0),
                snap.get("bookmaker", ""),
                snap.get("edge_pct", 0),
            ),
        )
        conn.execute(
            "DELETE FROM snapshots WHERE pinned = 0 AND id NOT IN ("
            "SELECT id FROM snapshots WHERE event = ? AND outcome = ? ORDER BY id DESC LIMIT ?)",
            (snap.get("event", ""), snap.get("outcome", ""), keep_per_key),
        )
        conn.commit()
        conn.close()

    def list_snapshots(self, pinned_only=False):
        conn = sqlite3.connect(self.db_file)
        q = "SELECT * FROM snapshots"
        if pinned_only:
            q += " WHERE pinned = 1"
        q += " ORDER BY pinned DESC, id DESC"
        rows = conn.execute(q).fetchall()
        conn.close()
        cols = ["id", "ts", "sport", "event", "outcome", "odds", "bookmaker", "edge_pct", "pinned"]
        return [dict(zip(cols, r)) for r in rows]

    def snapshot_history(self, event, outcome):
        conn = sqlite3.connect(self.db_file)
        rows = conn.execute(
            "SELECT * FROM snapshots WHERE event = ? AND outcome = ? ORDER BY id ASC",
            (event, outcome),
        ).fetchall()
        conn.close()
        cols = ["id", "ts", "sport", "event", "outcome", "odds", "bookmaker", "edge_pct", "pinned"]
        return [dict(zip(cols, r)) for r in rows]

    def toggle_pin(self, event, outcome):
        conn = sqlite3.connect(self.db_file)
        row = conn.execute(
            "SELECT id, pinned FROM snapshots WHERE event = ? AND outcome = ? ORDER BY id DESC LIMIT 1",
            (event, outcome),
        ).fetchone()
        if row:
            new = 0 if row[1] else 1
            conn.execute("UPDATE snapshots SET pinned = ? WHERE id = ?", (new, row[0]))
            conn.commit()
            conn.close()
            return {"id": row[0], "event": event, "outcome": outcome, "pinned": bool(new)}
        conn.close()
        return None
