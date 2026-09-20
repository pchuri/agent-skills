#!/usr/bin/env python3
"""
SmartThings REST API CLI Helper

A zero-dependency CLI tool to query and control Samsung SmartThings devices
via the official REST API (https://api.smartthings.com/v1).

Environment variables:
  SMARTTHINGS_API_TOKEN or SMARTTHINGS_TOKEN: Personal Access Token (PAT)
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.smartthings.com/v1"


def get_token():
    token = os.environ.get("SMARTTHINGS_API_TOKEN") or os.environ.get("SMARTTHINGS_TOKEN")
    if not token:
        sys.stderr.write(
            "Error: SMARTTHINGS_API_TOKEN or SMARTTHINGS_TOKEN environment variable is required.\n"
        )
        sys.exit(1)
    return token.strip()


def api_request(path, method="GET", body=None):
    token = get_token()
    url = f"{API_BASE}{path}" if path.startswith("/") else f"{API_BASE}/{path}"

    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message") or err_json.get("message") or err_body
        except Exception:
            msg = err_body
        sys.stderr.write(f"HTTP {e.code} Error ({method} {url}): {msg}\n")
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write(f"Network error: {e.reason}\n")
        sys.exit(1)


def get_devices():
    res = api_request("/devices")
    return res.get("items", [])


def resolve_device_id(identifier):
    """Resolve a device ID directly or by partial case-insensitive label/name match."""
    devices = get_devices()
    # Check exact deviceId match
    for d in devices:
        if d.get("deviceId") == identifier:
            return d["deviceId"], d.get("label") or d.get("name")

    # Check exact label match
    for d in devices:
        label = d.get("label", "")
        if label.lower() == identifier.lower():
            return d["deviceId"], label

    # Check substring match
    matches = [
        d for d in devices
        if identifier.lower() in d.get("label", "").lower()
        or identifier.lower() in d.get("name", "").lower()
    ]
    if len(matches) == 1:
        return matches[0]["deviceId"], matches[0].get("label") or matches[0].get("name")
    elif len(matches) > 1:
        matched_names = ", ".join(f"'{m.get('label') or m.get('name')}' ({m['deviceId']})" for m in matches)
        sys.stderr.write(f"Ambiguous device identifier '{identifier}'. Matches: {matched_names}\n")
        sys.exit(1)

    sys.stderr.write(f"Device '{identifier}' not found.\n")
    sys.exit(1)


def send_command(device_id, capability, command, args=None, component="main"):
    payload = {
        "commands": [
            {
                "component": component,
                "capability": capability,
                "command": command,
                "arguments": args or [],
            }
        ]
    }
    return api_request(f"/devices/{device_id}/commands", method="POST", body=payload)


def cmd_devices(args):
    devices = get_devices()
    if args.filter:
        flt = args.filter.lower()
        devices = [
            d for d in devices
            if flt in d.get("label", "").lower() or flt in d.get("name", "").lower()
        ]

    if args.json:
        print(json.dumps(devices, indent=2, ensure_ascii=False))
        return

    if not devices:
        print("No devices found.")
        return

    print(f"{'DEVICE ID':<38} {'LABEL':<25} {'TYPE':<12} {'NAME'}")
    print("-" * 90)
    for d in devices:
        dev_id = d.get("deviceId", "")
        label = (d.get("label") or "")[:24]
        dtype = (d.get("type") or "")[:11]
        name = d.get("name") or ""
        print(f"{dev_id:<38} {label:<25} {dtype:<12} {name}")


def cmd_locations(args):
    res = api_request("/locations")
    items = res.get("items", [])
    if args.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return
    print(f"{'LOCATION ID':<38} {'NAME'}")
    print("-" * 60)
    for loc in items:
        print(f"{loc.get('locationId', ''):<38} {loc.get('name', '')}")


def cmd_status(args):
    dev_id, dev_name = resolve_device_id(args.device)
    res = api_request(f"/devices/{dev_id}/status")

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print(f"Device: {dev_name} ({dev_id})")
    components = res.get("components", {})
    for comp_name, comp_data in components.items():
        if len(components) > 1:
            print(f"  [Component: {comp_name}]")
        for cap_name, cap_data in comp_data.items():
            for attr_name, attr_data in cap_data.items():
                if isinstance(attr_data, dict) and "value" in attr_data:
                    val = attr_data.get("value")
                    unit = attr_data.get("unit") or ""
                    if val is not None:
                        val_str = f"{val} {unit}".strip()
                        print(f"    - {cap_name}.{attr_name}: {val_str}")


def cmd_on(args):
    dev_id, dev_name = resolve_device_id(args.device)
    send_command(dev_id, "switch", "on", component=args.component)
    print(f"Turned ON: {dev_name} ({dev_id})")


def cmd_off(args):
    dev_id, dev_name = resolve_device_id(args.device)
    send_command(dev_id, "switch", "off", component=args.component)
    print(f"Turned OFF: {dev_name} ({dev_id})")


def cmd_level(args):
    dev_id, dev_name = resolve_device_id(args.device)
    level = max(0, min(100, args.level))
    send_command(dev_id, "switchLevel", "setLevel", [level], component=args.component)
    print(f"Set brightness to {level}%: {dev_name} ({dev_id})")


def cmd_color_temp(args):
    dev_id, dev_name = resolve_device_id(args.device)
    send_command(dev_id, "colorTemperature", "setColorTemperature", [args.kelvin], component=args.component)
    print(f"Set color temperature to {args.kelvin}K: {dev_name} ({dev_id})")


def cmd_set_temp(args):
    dev_id, dev_name = resolve_device_id(args.device)
    cap = "thermostatHeatingSetpoint" if args.heating else "thermostatCoolingSetpoint"
    cmd = "setHeatingSetpoint" if args.heating else "setCoolingSetpoint"
    send_command(dev_id, cap, cmd, [args.temp], component=args.component)
    mode_str = "heating" if args.heating else "cooling"
    print(f"Set {mode_str} setpoint to {args.temp}°C: {dev_name} ({dev_id})")


def cmd_raw(args):
    dev_id, dev_name = resolve_device_id(args.device)
    parsed_args = []
    for a in args.args:
        try:
            parsed_args.append(json.loads(a))
        except Exception:
            parsed_args.append(a)
    res = send_command(dev_id, args.capability, args.command, parsed_args, component=args.component)
    print(f"Command executed on {dev_name} ({dev_id}):")
    print(json.dumps(res, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="SmartThings REST API CLI helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # devices
    p_dev = subparsers.add_parser("devices", aliases=["list", "ls"], help="List all devices")
    p_dev.add_argument("--filter", "-f", help="Filter by label or name")
    p_dev.add_argument("--json", action="store_true", help="Output raw JSON")
    p_dev.set_defaults(func=cmd_devices)

    # locations
    p_loc = subparsers.add_parser("locations", help="List locations")
    p_loc.add_argument("--json", action="store_true", help="Output raw JSON")
    p_loc.set_defaults(func=cmd_locations)

    # status
    p_stat = subparsers.add_parser("status", help="Get device status")
    p_stat.add_argument("device", help="Device ID or label/name")
    p_stat.add_argument("--json", action="store_true", help="Output raw JSON")
    p_stat.set_defaults(func=cmd_status)

    # on / off
    p_on = subparsers.add_parser("on", help="Turn device switch ON")
    p_on.add_argument("device", help="Device ID or label/name")
    p_on.add_argument("--component", default="main", help="Component name (default: main)")
    p_on.set_defaults(func=cmd_on)

    p_off = subparsers.add_parser("off", help="Turn device switch OFF")
    p_off.add_argument("device", help="Device ID or label/name")
    p_off.add_argument("--component", default="main", help="Component name (default: main)")
    p_off.set_defaults(func=cmd_off)

    # level
    p_level = subparsers.add_parser("level", help="Set light/switch level (0-100%%)")
    p_level.add_argument("device", help="Device ID or label/name")
    p_level.add_argument("level", type=int, help="Level percentage (0-100)")
    p_level.add_argument("--component", default="main", help="Component name (default: main)")
    p_level.set_defaults(func=cmd_level)

    # color-temp
    p_ct = subparsers.add_parser("color-temp", help="Set color temperature in Kelvin")
    p_ct.add_argument("device", help="Device ID or label/name")
    p_ct.add_argument("kelvin", type=int, help="Kelvin value (e.g. 2700, 3000, 6500)")
    p_ct.add_argument("--component", default="main", help="Component name (default: main)")
    p_ct.set_defaults(func=cmd_color_temp)

    # set-temp
    p_temp = subparsers.add_parser("temp", help="Set thermostat setpoint temperature")
    p_temp.add_argument("device", help="Device ID or label/name")
    p_temp.add_argument("temp", type=float, help="Target temperature in Celsius")
    p_temp.add_argument("--heating", action="store_true", help="Target heating instead of cooling")
    p_temp.add_argument("--component", default="main", help="Component name (default: main)")
    p_temp.set_defaults(func=cmd_set_temp)

    # raw command
    p_cmd = subparsers.add_parser("cmd", help="Send arbitrary capability command")
    p_cmd.add_argument("device", help="Device ID or label/name")
    p_cmd.add_argument("capability", help="Capability ID (e.g. switch, airConditionerMode)")
    p_cmd.add_argument("command", help="Command name (e.g. on, setAirConditionerMode)")
    p_cmd.add_argument("args", nargs="*", help="Command arguments")
    p_cmd.add_argument("--component", default="main", help="Component name (default: main)")
    p_cmd.set_defaults(func=cmd_raw)

    parsed = parser.parse_args()
    parsed.func(parsed)


if __name__ == "__main__":
    main()
