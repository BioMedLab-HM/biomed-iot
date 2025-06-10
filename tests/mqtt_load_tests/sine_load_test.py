#!/usr/bin/env python3
"""
Publish mock ECG data (sine wave) over MQTT at a chosen sample-rate
for a chosen run duration.

Examples
--------
# 100 samples per second for 1 second, millisecond timestamps          (default)
python3 sine_load_test.py

# 300 samples per second for 10 seconds, microsecond timestamps
python3 sine_load_test.py -s 300 -d 10 -p us
"""

import argparse
import json
import sys
import time
import paho.mqtt.client as mqtt

# ───────────────────────────────────────────────────────────────────────────────
# 100-sample base ECG waveform (mV)
BASE_SAMPLES = [
     0.000,  0.063,  0.125,  0.187,  0.249,  0.309,  0.368,  0.426,  0.482,  0.536,
     0.588,  0.637,  0.684,  0.728,  0.770,  0.809,  0.844,  0.876,  0.904,  0.929,
     0.951,  0.968,  0.982,  0.992,  0.998,  1.000,  0.998,  0.992,  0.982,  0.968,
     0.951,  0.929,  0.904,  0.876,  0.844,  0.809,  0.770,  0.728,  0.684,  0.637,
     0.588,  0.536,  0.482,  0.426,  0.368,  0.309,  0.249,  0.187,  0.125,  0.063,
     0.000, -0.063, -0.125, -0.187, -0.249, -0.309, -0.368, -0.426, -0.482, -0.536,
    -0.588, -0.637, -0.684, -0.728, -0.770, -0.809, -0.844, -0.876, -0.904, -0.929,
    -0.951, -0.968, -0.982, -0.992, -0.998, -1.000, -0.998, -0.992, -0.982, -0.968,
    -0.951, -0.929, -0.904, -0.876, -0.844, -0.809, -0.770, -0.728, -0.684, -0.637,
    -0.588, -0.536, -0.482, -0.426, -0.368, -0.309, -0.249, -0.187, -0.125, -0.063
]
BASE_LEN = len(BASE_SAMPLES)          # 100

# MQTT parameters
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC       = "in/sine_load_test"
QOS_LEVEL   = 0

# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────
_PRECISION_FACTORS = {
    "ms": 1_000_000,   # ns → ms
    "us": 1_000,       # ns → µs
    "ns": 1            # keep as-is
}

def unix_timestamp(precision: str) -> int:
    """Return current epoch in requested precision (ms / µs / ns)."""
    ns = time.time_ns()
    return ns // _PRECISION_FACTORS[precision]


def parse_args():
    p = argparse.ArgumentParser(
        description=("Publish mock ECG data at <samples-per-second> for a given "
                     "duration, spacing messages evenly across the run.")
    )
    p.add_argument("-s", "--samples", type=int, default=BASE_LEN,
                   help=(f"Samples **per second** (positive multiple of {BASE_LEN}; "
                         f"default {BASE_LEN})."))
    p.add_argument("-d", "--duration", type=float, default=1.0,
                   help="Duration of the test in seconds (float, default 1.0).")
    p.add_argument("-p", "--precision", choices=("ms", "us", "ns"), default="ms",
                   help="Timestamp precision (ms default, or us / ns).")
    args = p.parse_args()

    if args.samples <= 0 or args.samples % BASE_LEN != 0:
        p.error(f"--samples must be a positive multiple of {BASE_LEN}.")
    if args.duration <= 0:
        p.error("--duration must be > 0.")

    # Ensure total sample count is still a multiple of 100 so we can replicate the base list
    total_samples = args.samples * args.duration
    if total_samples % BASE_LEN != 0:
        p.error("samples_per_second × duration must yield a total sample count "
                f"that is a multiple of {BASE_LEN}.\n"
                "Try adjusting duration or sample rate.")

    return args.samples, args.duration, args.precision


def main() -> None:
    rate_per_sec, duration, precision = parse_args()
    total_samples = int(rate_per_sec * duration)
    repeats       = total_samples // BASE_LEN
    samples_mv    = BASE_SAMPLES * repeats

    interval = 1.0 / rate_per_sec          # seconds between publishes

    client = mqtt.Client()
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    start_t = time.perf_counter()

    for idx, mv in enumerate(samples_mv, start=1):
        payload = json.dumps({
            "mv": mv,
            "timestamp": unix_timestamp(precision)
        })
        client.publish(TOPIC, payload, qos=QOS_LEVEL, retain=False)

        next_slot  = start_t + idx * interval
        sleep_time = next_slot - time.perf_counter()

        # > 50 µs → let OS sleep; else busy-wait for best precision
        if sleep_time > 0.000050:
            time.sleep(sleep_time)
        else:
            while time.perf_counter() < next_slot:
                pass

    client.loop_stop()
    client.disconnect()
    print(f"Sent {total_samples} samples "
          f"({rate_per_sec}/s for {duration:g} s, "
          f"interval ≈ {interval*1e6:.1f} µs, precision {precision})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted by user")
