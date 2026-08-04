#!/usr/bin/env python3
"""Hong Kong Pools Engine - Prediction for HONGKONG_POOLS market.

Implements the logic specified in logic_hkpools.md:

1. Twin classifier : each historical result -> NONE | PAIR | DOUBLE_PAIR | TRIPLE | QUAD
2. Day & modulo dimensions (day, m10, m20, m30) -> weighted twin probability
3. Result-1 ratio : previous draw twin status affects the next draw
4. Digit scoring : positional + global-pair + slot-pair + last-result penalty
5. Sydney cross-match : 7-draw weekly frequency + latest SDY result overlap
6. Final Touch : prioritize 2 digits from the latest HK result.

Output format : 5 main digits + 1 backup digit  (e.g. "59108 + 3").
"""

from typing import Dict, Any, List
from collections import Counter, defaultdict

from engines.base_engine import BaseEngine, PredictionResult
from core.data_loader import DataLoader


# ---------------------------------------------------------------------- #
# Twin classifier helpers
# ---------------------------------------------------------------------- #
def _day_counter():
    """Factory returning a dict with twin and total counters."""
    return {"twin": 0, "total": 0}


def _classify(result: str) -> Dict[str, Any]:
    """Classify a 4-digit result into a twin type.

    Args:
        result: 4-digit string (e.g. "6723").

    Returns:
        Dict with twin_class, counts and max_count.
    """
    counts = Counter(result)
    max_count = max(counts.values()) if counts else 0
    pairs = sum(1 for c in counts.values() if c >= 2)

    if max_count >= 4:
        twin_type = "QUAD"
    elif max_count == 3:
        twin_type = "TRIPLE"
    elif pairs == 2:
        twin_type = "DOUBLE_PAIR"
    elif pairs == 1:
        twin_type = "PAIR"
    else:
        twin_type = "NONE"

    return {"twin_class": twin_type, "counts": dict(counts), "max_count": max_count}


class HongKongPoolsEngine(BaseEngine):
    """Hong Kong Pools prediction engine."""

    DAY_WEIGHT = 0.25
    M10_WEIGHT = 0.15
    M20_WEIGHT = 0.20
    M30_WEIGHT = 0.20
    RESULT_MINUS_1_WEIGHT = 0.20

    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()

    # ------------------------------------------------------------------ #
    # predict()
    # ------------------------------------------------------------------ #
    def predict(self, input_data: Dict[str, Any]) -> PredictionResult:
        """Generate 5 main digits + 1 backup for the next HK pool period."""
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data for HongKongPools engine")

        # Full HK history via DataLoader (large limit loads all records)
        full_hk = self.data_loader.load_market("HONGKONG_POOLS", history_limit=5000)
        hk_history = full_hk.get("history", [])
        latest_hk = full_hk.get("latest", {})

        if not hk_history:
            raise ValueError(f"No history available for HONGKONG_POOLS")

        # Sydney data (optional)
        sydney = self._load_sydney()
        sydney_history = sydney.get("history", [])
        sydney_latest = sydney.get("latest", {})

        target_period = self._compute_target_period(hk_history)
        result = PredictionResult("hongkong_pools", "HONGKONG_POOLS", target_period)

        # ---- 1. Twin classifier over full history ------------------- #
        twin_dist = self._compute_twin_distribution(hk_history)

        # ---- 2. Dimensional twin probabilities ---------------------- #
        day_signal = self._day_dimension(hk_history)
        m10 = self._mod_dimension(hk_history, 10)
        m20 = self._mod_dimension(hk_history, 20)
        m30 = self._mod_dimension(hk_history, 30)
        result_dim = self._result_minus_1_dimension(hk_history)

        # ---- 3. Aggregate twin probability -------------------------- #
        rasio_twin_pct = self._aggregate_twin_probability(
            hk_history, day_signal, m10, m20, m30, result_dim
        )

        # ---- 4. Digit scoring --------------------------------------- #
        digit_scores = self._digit_scoring(hk_history, latest_hk)

        # ---- 5/6. Sydney cross-match -> intermediate ----------------- #
        intermediate_main, intermediate_backup, ranked_digits, sydney_stats = (
            self._sydney_cross_match(sydney_history, sydney_latest, digit_scores)
        )

        # ---- 7. Final Touch ----------------------------------------- #
        final = self._final_touch(intermediate_main, intermediate_backup, latest_hk, hk_history)

        # ---- 8. Output ---------------------------------------------- #
        confidence = self._confidence(rasio_twin_pct, hk_history, sydney_history)

        result.set_prediction(
            main_digits=[final["true_main"]],
            backup_digits=[final["true_backup"]],
            confidence=confidence,
            method="hk_pools_twin_analysis + sydney_week_crossmatch + hk_last_result_priority",
        )

        analysis = self._build_analysis(
            hk_history=hk_history,
            sydney_history=sydney_history,
            latest_hk=latest_hk,
            twin_dist=twin_dist,
            rasio_twin_pct=rasio_twin_pct,
            day_signal=day_signal,
            ranked_digits=ranked_digits,
            sydney_stats=sydney_stats,
            intermediate=f"{intermediate_main} + {intermediate_backup}",
            final=final,
        )
        result.set_analysis(analysis)

        return result

    # ------------------------------------------------------------------ #
    # Data loading
    # ------------------------------------------------------------------ #
    def _load_sydney(self) -> Dict[str, Any]:
        """Load Sydney pools data. Returns empty dict on any error."""
        try:
            return self.data_loader.load_market("SYDNEY_POOLS", history_limit=5000)
        except Exception:
            return {"history": [], "latest": {}}

    def _compute_target_period(self, history: List[Dict]) -> str:
        """Return target period = latest period + 1."""
        for rec in history:
            p = rec.get("period", "")
            if str(p).isdigit():
                return str(int(p) + 1)
        return "9999"

    # ------------------------------------------------------------------ #
    # Twin distribution
    # ------------------------------------------------------------------ #
    def _compute_twin_distribution(self, history: List[Dict]):
        """Classify all results and return {twin_class: count}."""
        dist = Counter()
        for rec in history:
            result = rec.get("result", "")
            if not result:
                continue
            dist[_classify(result)["twin_class"]] += 1
        return dict(dist)

    # ------------------------------------------------------------------ #
    # Dimensions
    # ------------------------------------------------------------------ #
    def _day_dimension(self, history: List[Dict]) -> Dict[str, Any]:
        """Twin ratio by day name. Return next-draw day + twin_rate.

        The next draw day is computed from the latest record's date + 1 day so
        that the day-multiple dimension refers to the *target* draw, not the
        most recent one.
        """
        by_day = defaultdict(_day_counter)
        for rec in history:
            day = rec.get("day", "")
            result = rec.get("result", "")
            by_day[day]["total"] += 1
            if _classify(result)["twin_class"] != "NONE":
                by_day[day]["twin"] += 1

        stats = {}
        for day, d in by_day.items():
            stats[day] = d["twin"] / d["total"] if d["total"] else 0.0

        next_day = self._next_day_name(history)
        return {
            "day": next_day,
            "twin_rate": round(stats.get(next_day, 0.0), 4),
            "stats": stats,
        }

    @staticmethod
    def _next_day_name(history: List[Dict]) -> str:
        """Compute the weekday name of the next draw from the latest date."""
        DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]
        if not history:
            return "Monday"
        latest_day = history[0].get("day", "")
        if latest_day in DAYS:
            idx = DAYS.index(latest_day)
            return DAYS[(idx + 1) % 7]
        return latest_day or "Monday"

    def _mod_dimension(self, history: List[Dict], interval: int) -> Dict[str, Any]:
        """Twin ratio by period % interval. Return next slot + ratio."""
        by_mod = defaultdict(_day_counter)
        next_period = 0
        for rec in history:
            p = rec.get("period", "")
            if not str(p).isdigit():
                continue
            if next_period == 0:
                next_period = int(p) + 1
            m = int(p) % interval
            by_mod[m]["total"] += 1
            if _classify(rec.get("result", ""))["twin_class"] != "NONE":
                by_mod[m]["twin"] += 1

        stats = {}
        for m, d in by_mod.items():
            stats[m] = d["twin"] / d["total"] if d["total"] else 0.0

        next_mod = next_period % interval
        return {
            "interval": interval,
            "next_mod": next_mod,
            "next_ratio": round(stats.get(next_mod, 0.0), 4),
            "stats": stats,
        }

    def _result_minus_1_dimension(self, history: List[Dict]) -> Dict[str, Any]:
        """Next twin ratio depending on previous draw twin status."""
        stats = {"twin_prev": {"twin": 0, "total": 0}, "none_prev": {"twin": 0, "total": 0}}
        prev_class = None
        for rec in history:
            curr_class = _classify(rec.get("result", ""))["twin_class"]
            if prev_class is not None:
                key = "twin_prev" if prev_class != "NONE" else "none_prev"
                stats[key]["total"] += 1
                if curr_class != "NONE":
                    stats[key]["twin"] += 1
            prev_class = curr_class

        twin_prev = stats["twin_prev"]["twin"] / stats["twin_prev"]["total"] if stats["twin_prev"]["total"] else 0.0
        none_prev = stats["none_prev"]["twin"] / stats["none_prev"]["total"] if stats["none_prev"]["total"] else 0.0

        latest_class = _classify(history[0].get("result", ""))["twin_class"]
        branch = "twin_prev" if latest_class != "NONE" else "none_prev"
        next_ratio = twin_prev if branch == "twin_prev" else none_prev

        return {
            "twin_prev_ratio": round(twin_prev, 4),
            "none_prev_ratio": round(none_prev, 4),
            "last_class": latest_class,
            "branch": branch,
            "next_ratio": round(next_ratio, 4),
        }

    # ------------------------------------------------------------------ #
    # Aggregate
    # ------------------------------------------------------------------ #
    def _aggregate_twin_probability(self, history, day, m10, m20, m30, result_dim) -> float:
        total = len(history)
        twin_count = 0
        for rec in history:
            if _classify(rec.get("result", ""))["twin_class"] != "NONE":
                twin_count += 1
        baseline = twin_count / total if total else 0.0

        weighted = (
            self.DAY_WEIGHT * day["twin_rate"]
            + self.M10_WEIGHT * m10["next_ratio"]
            + self.M20_WEIGHT * m20["next_ratio"]
            + self.M30_WEIGHT * m30["next_ratio"]
            + self.RESULT_MINUS_1_WEIGHT * result_dim["next_ratio"]
        )
        return round(weighted * 100, 2)

    # ------------------------------------------------------------------ #
    # Digit scoring
    # ------------------------------------------------------------------ #
    def _digit_scoring(self, history: List[Dict], latest: Dict) -> Dict[str, float]:
        """Score digits 0-9 from positional + global + pair + penalty."""
        pos_freq = [Counter() for _ in range(4)]
        all_freq = Counter()
        pair_freq = Counter()

        for rec in history:
            result = rec.get("result", "")
            if not result:
                continue
            all_freq.update(result)
            c = _classify(result)
            for d, cnt in c["counts"].items():
                if cnt >= 2:
                    pair_freq[d] += 1
            for i, ch in enumerate(result[:4]):
                pos_freq[i][ch] += 1

        # Positional score
        positional = {str(i): 0.0 for i in range(10)}
        for i in range(4):
            if not pos_freq[i]:
                continue
            maxp = max(pos_freq[i].values())
            for d, cnt in pos_freq[i].items():
                positional[d] += cnt / maxp
        pos_max = max(positional.values()) if positional else 1.0
        for d in positional:
            positional[d] /= pos_max

        # Global frequency
        global_max = max(all_freq.values()) if all_freq else 1
        global_norm = {str(i): all_freq.get(str(i), 0) / global_max for i in range(10)}

        # Pair frequency
        pair_max = max(pair_freq.values()) if pair_freq else 1
        pair_norm = {str(i): pair_freq.get(str(i), 0) / pair_max for i in range(10)}

        penalty = set(latest.get("result", "")) if latest else set()

        scores = {}
        for d in range(10):
            ds = str(d)
            score = 0.30 * positional.get(ds, 0) + 0.25 * global_norm.get(ds, 0) + 0.25 * pair_norm.get(ds, 0)
            if ds in penalty:
                score -= 0.10
            scores[ds] = round(score, 4)
        return scores

    # ------------------------------------------------------------------ #
    # Sydney crossmatch
    # ------------------------------------------------------------------ #
    def _sydney_cross_match(self, sydney_history, sydney_latest, hk_scores):
        """Rank digits using Sydney-only rules (spec 8A.5).

        Ranking order (desc):
          1. weekly frequency (7 latest SDY draws)
          2. tie-break: appears in the latest SDY result
          3. tie-break: all-time SDY frequency
          4. tie-break: smaller digit wins

        The HK digit scores are retained in the returned metadata for the
        analysis, but do not alter the Sydney ranking order defined by the spec.
        """
        weekly = Counter()
        for rec in sydney_history[:7]:
            weekly.update(rec.get("result", ""))
        latest_digits = set(sydney_latest.get("result", ""))
        all_time = Counter()
        for rec in sydney_history:
            all_time.update(rec.get("result", ""))

        def rank_key(d):
            ds = str(d)
            in_latest = 1 if ds in latest_digits else 0
            return (-weekly.get(ds, 0), -in_latest, -all_time.get(ds, 0), int(ds))

        ranked = sorted([str(i) for i in range(10)], key=rank_key)
        main_digits = ranked[:5]
        backup = ranked[5] if len(ranked) > 5 else "0"

        sydney_stats = {
            "window": 7,
            "digits": dict(weekly),
            "all_time": dict(all_time),
            "latest": sydney_latest.get("result", ""),
            "latest_date": sydney_latest.get("date", ""),
            "overlap_with_main": len(set(main_digits) & latest_digits),
        }

        return "".join(main_digits), backup, ranked, sydney_stats

    # ------------------------------------------------------------------ #
    # Final touch
    # ------------------------------------------------------------------ #
    def _final_touch(self, intermediate_main, intermediate_backup, latest, hk_history) -> Dict[str, Any]:
        """Prioritize the 2 hottest digits from the latest HK result."""
        last_result = (latest or {}).get("result", "")
        if not last_result or len(last_result) < 2:
            return {
                "true_main": intermediate_main,
                "true_backup": intermediate_backup,
                "penentu": [],
                "matched": [],
                "missing": [],
                "backup_new": intermediate_backup,
                "hk_7day_freq": {},
            }

        # 7-day HK frequency
        hk7 = Counter()
        for rec in hk_history[:7]:
            hk7.update(rec.get("result", ""))
        hk7_dict = {str(i): hk7.get(str(i), 0) for i in range(10)}

        unique = list(set(last_result))
        unique_sorted = sorted(unique, key=lambda d: (-hk7.get(d, 0), int(d)))
        penentu = unique_sorted[:2]

        matched = [d for d in penentu if d in intermediate_main]
        missing = [d for d in penentu if d not in intermediate_main]

        # Rebuild main: matched digits first
        if matched:
            sisa = [d for d in intermediate_main if d not in matched]
            true_main = "".join(matched + sisa)
        else:
            true_main = intermediate_main

        # Backup
        if missing:
            backup_new = max(missing, key=lambda d: (hk7.get(d, 0), -int(d)))
        else:
            backup_new = intermediate_backup

        return {
            "true_main": true_main,
            "true_backup": backup_new,
            "penentu": penentu,
            "matched": matched,
            "missing": missing,
            "backup_new": backup_new,
            "hk_7day_freq": hk7_dict,
        }

    # ------------------------------------------------------------------ #
    # Confidence
    # ------------------------------------------------------------------ #
    def _confidence(self, rasio_pct, hk_history, sydney_history) -> float:
        hk_count = len(hk_history)
        sdy_count = len(sydney_history)

        data_score = min(1.0, hk_count / 1000.0) * 0.5 + min(1.0, sdy_count / 30.0) * 0.2
        signal_score = min(1.0, max(0.0, (rasio_pct - 44.0) / 15.0)) * 0.3
        return round(min(1.0, data_score + signal_score), 2)

    # ------------------------------------------------------------------ #
    # Analysis
    # ------------------------------------------------------------------ #
    def _build_analysis(self, hk_history, sydney_history, latest_hk, twin_dist,
                        rasio_twin_pct, day_signal, ranked_digits, sydney_stats,
                        intermediate, final) -> Dict[str, Any]:
        return {
            "algorithm": "hk_pools_twin_analysis + sydney_week_crossmatch + hk_last_result_priority",
            "data_count_hk": len(hk_history),
            "data_count_sdy": len(sydney_history),
            "hk_latest": latest_hk.get("result", ""),
            "hk_latest_period": latest_hk.get("period", ""),
            "twin_type_dist": twin_dist,
            "rasio_twin_pct": rasio_twin_pct,
            "day_signal": day_signal,
            "ranked_digits": ranked_digits,
            "sydney_week": sydney_stats.get("digits", {}),
            "sydney_latest": {
                "result": sydney_stats.get("latest", ""),
                "date": sydney_stats.get("latest_date", ""),
            },
            "sydney_overlap_main": sydney_stats.get("overlap_with_main", 0),
            "final_touch": {
                "penentu": final.get("penentu", []),
                "matched": final.get("matched", []),
                "missing": final.get("missing", []),
                "backup_new": final.get("backup_new", ""),
                "hk_7day_freq": final.get("hk_7day_freq", {}),
            },
            "output_intermediate": intermediate,
            "output_final": f"{final.get('true_main', '')} + {final.get('true_backup', '')}",
        }


if __name__ == "__main__":
    print("HongKongPoolsEngine loaded (see specs: logic_hkpools.md)")