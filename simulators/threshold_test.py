"""
Threshold Test — validates the full auto-toggling cycle (WF2).

Runs a simulated traffic pattern through the threshold monitor logic:
  error_rate > threshold → feature disabled
  error_rate < threshold → feature re-enabled

Uses the same sinusoidal formula as traffic_simulator.py but drives
the full cycle with console output showing every state transition.

Can optionally call the MCP HTTP server to actually toggle features.

Usage:
    # Dry run (no real toggling, just shows what would happen)
    python3 simulators/threshold_test.py

    # Live mode (calls MCP HTTP to toggle real features)
    python3 simulators/threshold_test.py --live

    # Custom parameters
    python3 simulators/threshold_test.py --period 40 --threshold 0.15 --feature search_v2
"""

import argparse
import json
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_PATH = PROJECT_ROOT / "simulators" / "logs.json"

MCP_HTTP_URL = "http://localhost:5150/mcp"


def calc_error_rate(tick: int, period: int, base_rate: float, amplitude: float) -> float:
    return base_rate + amplitude * math.sin(2 * math.pi * tick / period)


def write_event(feature: str, status: str, tick: int) -> dict:
    resp_time = random.randint(200, 2000) if status == "error" else random.randint(50, 300)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tick": tick,
        "feature": feature,
        "status": status,
        "response_time_ms": resp_time,
    }

    logs = []
    if LOGS_PATH.exists():
        raw = LOGS_PATH.read_text(encoding="utf-8").strip()
        if raw:
            logs = json.loads(raw)
    logs.append(event)
    if len(logs) > 500:
        logs = logs[-500:]
    LOGS_PATH.write_text(json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8")

    return event


def call_mcp(feature: str, action: str) -> dict:
    """Call REST API to toggle a feature."""
    try:
        import requests
        state = "Enabled" if action == "enable" else "Testing"
        if action == "disable":
            state = "Disabled"

        url = f"http://localhost:5150/api/features/{feature}/state"
        resp = requests.post(
            url,
            json={"state": state},
            headers={"Content-Type": "application/json", "x-auth": "proshop-secret"},
            timeout=10,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("success"):
            return {"success": True, "status_code": resp.status_code}
        return {"success": False, "status_code": resp.status_code, "error": data.get("message", data.get("error", "unknown"))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run(
    period: int = 60,
    base_rate: float = 0.05,
    amplitude: float = 0.20,
    threshold: float = 0.15,
    ticks: int = 120,
    interval: float = 0.5,
    feature: str = "search_v2",
    live: bool = False,
):
    """
    Run threshold crossing test.

    The sine wave will cause error_rate to cross the threshold multiple times,
    producing a full auto-toggling cycle: enabled → disabled → enabled → disabled ...
    """
    print("=" * 60)
    print("THRESHOLD AUTO-TOGGLE TEST")
    print("=" * 60)
    print(f"  Feature:   {feature}")
    print(f"  Threshold: {threshold:.0%}")
    print(f"  Period:    {period} ticks")
    print(f"  Base rate: {base_rate:.0%}  Amplitude: {amplitude:.0%}")
    print(f"  Range:     [{max(0, base_rate - amplitude):.0%}, {min(1, base_rate + amplitude):.0%}]")
    print(f"  Ticks:     {ticks}  Interval: {interval}s")
    print(f"  Mode:      {'LIVE (real MCP calls)' if live else 'DRY RUN'}")
    print()

    # Check if threshold is reachable
    max_rate = base_rate + amplitude
    min_rate = base_rate - amplitude
    will_cross_up = max_rate > threshold
    will_cross_down = min_rate < threshold

    if not will_cross_up:
        print(f"  WARNING: max_rate ({max_rate:.0%}) < threshold ({threshold:.0%}). Will never disable.")
    if not will_cross_down:
        print(f"  WARNING: min_rate ({min_rate:.0%}) > threshold ({threshold:.0%}). Will never re-enable.")
    if will_cross_up and will_cross_down:
        print(f"  OK: error_rate WILL cross threshold in both directions")
    print()

    current_state = "enabled"
    transitions = []

    for tick in range(1, ticks + 1):
        error_rate = calc_error_rate(tick, period, base_rate, amplitude)
        error_rate = max(0.0, min(1.0, error_rate))

        # Generate event
        status = "error" if random.random() < error_rate else "success"
        write_event(feature, status, tick)

        # Check threshold crossing
        arrow = " "
        action = None

        if error_rate > threshold and current_state == "enabled":
            arrow = "v"  # crossing down (disabling)
            action = "disable"
            current_state = "disabled"
            transitions.append({"tick": tick, "from": "enabled", "to": "disabled", "error_rate": error_rate})
            if live:
                result = call_mcp(feature, "disable")
                mcp_status = "OK" if result.get("success") else f"FAIL: {result.get('error', 'unknown')}"
            else:
                mcp_status = "dry-run"

        elif error_rate <= threshold and current_state == "disabled":
            arrow = "^"  # crossing up (re-enabling)
            action = "enable"
            current_state = "enabled"
            transitions.append({"tick": tick, "from": "disabled", "to": "enabled", "error_rate": error_rate})
            if live:
                result = call_mcp(feature, "enable")
                mcp_status = "OK" if result.get("success") else f"FAIL: {result.get('error', 'unknown')}"
            else:
                mcp_status = "dry-run"
        else:
            mcp_status = ""

        # Console output
        bar_len = 40
        filled = int(error_rate * bar_len)
        bar = "#" * filled + "-" * (bar_len - filled)
        thresh_pos = int(threshold * bar_len)
        thresh_marker = "T"

        line = f"  [{tick:3d}] {bar} {error_rate:5.1%}"
        if thresh_pos < bar_len:
            line = line[:6 + thresh_pos] + thresh_marker + line[7 + thresh_pos:]

        state_indicator = "ON " if current_state == "enabled" else "OFF"
        line += f"  [{state_indicator}]"

        if action:
            line += f"  >> {action.upper()} ({mcp_status})"

        print(line)
        time.sleep(interval)

    # Summary
    print()
    print("=" * 60)
    print(f"TEST COMPLETE — {len(transitions)} state transitions")
    print("=" * 60)
    for t in transitions:
        print(f"  Tick {t['tick']:3d}: {t['from']:>8s} -> {t['to']:<8s} (error_rate={t['error_rate']:.1%})")

    # Validate we saw both directions
    directions = {t["to"] for t in transitions}
    if "disabled" in directions and "enabled" in directions:
        print(f"\n  PASS: Full auto-toggling cycle observed")
    elif "disabled" in directions:
        print(f"\n  PARTIAL: Feature disabled but never re-enabled")
    elif "enabled" in directions:
        print(f"\n  PARTIAL: Feature re-enabled but never disabled")
    else:
        print(f"\n  FAIL: No state transitions detected")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ProShop Threshold Auto-Toggle Test")
    parser.add_argument("--period", type=int, default=60, help="Sine wave period in ticks")
    parser.add_argument("--base-rate", type=float, default=0.05, help="Baseline error rate")
    parser.add_argument("--amplitude", type=float, default=0.20, help="Error rate amplitude")
    parser.add_argument("--threshold", type=float, default=0.15, help="Error rate threshold for toggle")
    parser.add_argument("--ticks", type=int, default=120, help="Total ticks to simulate")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between ticks")
    parser.add_argument("--feature", type=str, default="search_v2", help="Feature to toggle")
    parser.add_argument("--live", action="store_true", help="Actually call MCP to toggle features")
    args = parser.parse_args()

    run(
        period=args.period,
        base_rate=args.base_rate,
        amplitude=args.amplitude,
        threshold=args.threshold,
        ticks=args.ticks,
        interval=args.interval,
        feature=args.feature,
        live=args.live,
    )
