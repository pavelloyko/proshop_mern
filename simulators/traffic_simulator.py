"""
Traffic Simulator for ProShop Feature Flags.

Generates synthetic traffic logs with sinusoidal error rate.
Writes events to logs.json for the n8n scheduled monitor (WF2).

Error rate formula:
    error_rate(t) = base_rate + amplitude * sin(2π * t / period)

Usage:
    python3 simulators/traffic_simulator.py
    python3 simulators/traffic_simulator.py --period 60 --amplitude 0.3
"""

import json
import math
import os
import random
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Default paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_PATH = PROJECT_ROOT / "simulators" / "logs.json"

# Feature flags to simulate traffic for
FEATURES = [
    "search_v2",
    "dark_mode",
    "multi_step_checkout_v2",
]

# Response time ranges (ms)
RESPONSE_TIME_SUCCESS = (50, 300)
RESPONSE_TIME_ERROR = (200, 2000)


def read_logs(path: Path) -> list:
    if path.exists():
        raw = path.read_text(encoding="utf-8").strip()
        if raw:
            return json.loads(raw)
    return []


def write_logs(path: Path, logs: list) -> None:
    payload = json.dumps(logs, indent=2, ensure_ascii=False)
    path.write_text(payload, encoding="utf-8")


def generate_event(
    feature: str, status: str, tick: int
) -> dict:
    if status == "error":
        resp_time = random.randint(*RESPONSE_TIME_ERROR)
    else:
        resp_time = random.randint(*RESPONSE_TIME_SUCCESS)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tick": tick,
        "feature": feature,
        "status": status,
        "response_time_ms": resp_time,
    }


def calc_error_rate(tick: int, period: int, base_rate: float, amplitude: float) -> float:
    """Sinusoidal error rate: oscillates between base_rate - amplitude and base_rate + amplitude."""
    return base_rate + amplitude * math.sin(2 * math.pi * tick / period)


def run(
    interval: float = 1.0,
    period: int = 120,
    base_rate: float = 0.05,
    amplitude: float = 0.15,
    max_events: int = 0,
    max_log_size: int = 500,
    feature: str = None,
):
    """
    Generate traffic events in a loop.

    Args:
        interval: seconds between events
        period: sine wave period in ticks
        base_rate: baseline error rate (0.0 - 1.0)
        amplitude: error rate swing (0.0 - 1.0)
        max_events: stop after N events (0 = infinite)
        max_log_size: trim logs.json to this many events
        feature: simulate only this feature (default: all)
    """
    features = [feature] if feature else FEATURES
    tick = 0

    print(f"Traffic Simulator started")
    print(f"  Period: {period} ticks | Base rate: {base_rate:.0%} | Amplitude: {amplitude:.0%}")
    print(f"  Error rate range: [{max(0, base_rate - amplitude):.0%}, {min(1, base_rate + amplitude):.0%}]")
    print(f"  Interval: {interval}s | Features: {features}")
    print(f"  Writing to: {LOGS_PATH}")
    print(f"  Press Ctrl+C to stop\n")

    try:
        while True:
            tick += 1

            # Calculate current error rate from sine wave
            error_rate = calc_error_rate(tick, period, base_rate, amplitude)
            error_rate = max(0.0, min(1.0, error_rate))

            # Generate one event per feature
            new_events = []
            for feat in features:
                status = "error" if random.random() < error_rate else "success"
                event = generate_event(feat, status, tick)
                new_events.append(event)

            # Read existing logs, append, trim, write
            logs = read_logs(LOGS_PATH)
            logs.extend(new_events)
            if len(logs) > max_log_size:
                logs = logs[-max_log_size:]
            write_logs(LOGS_PATH, logs)

            # Console output
            statuses = [e["status"] for e in new_events]
            errors = statuses.count("error")
            total = len(statuses)
            marker = "!" if errors > 0 else "."
            print(
                f"  [{tick:4d}] error_rate={error_rate:.1%} | "
                f"{errors}/{total} errors {marker}"
            )

            if max_events and tick >= max_events:
                print(f"\nReached max_events={max_events}, stopping.")
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\nStopped after {tick} ticks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ProShop Traffic Simulator")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between events")
    parser.add_argument("--period", type=int, default=120, help="Sine wave period in ticks")
    parser.add_argument("--base-rate", type=float, default=0.05, help="Baseline error rate")
    parser.add_argument("--amplitude", type=float, default=0.15, help="Error rate amplitude")
    parser.add_argument("--max-events", type=int, default=0, help="Stop after N events (0=inf)")
    parser.add_argument("--max-log-size", type=int, default=500, help="Max events in logs.json")
    parser.add_argument("--feature", type=str, default=None, help="Simulate only this feature")
    args = parser.parse_args()

    run(
        interval=args.interval,
        period=args.period,
        base_rate=args.base_rate,
        amplitude=args.amplitude,
        max_events=args.max_events,
        max_log_size=args.max_log_size,
        feature=args.feature,
    )
