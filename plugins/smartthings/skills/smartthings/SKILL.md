---
name: smartthings
description: Query and control Samsung SmartThings devices (lights, smart plugs, air conditioners, appliances, sensors) via the official SmartThings CLI or REST API. Supports persistent OAuth sessions via SmartThings CLI as well as Personal Access Tokens (PAT). Use when asked to list smart home devices, check status/readings, turn appliances or lights on/off, adjust brightness or color temperature, or set thermostat/AC temperatures.
---

# SmartThings CLI & REST API Skill

Query and control Samsung SmartThings smart home devices via the official SmartThings CLI (`smartthings`) or REST API (`https://api.smartthings.com/v1`).

Includes:
- Official SmartThings CLI (`smartthings`) commands.
- A zero-dependency Python 3 CLI tool (`scripts/st.py` or `st` on `PATH`) with fuzzy label lookup.
- Direct `curl` REST API recipes.

---

## Authentication & Prerequisites

SmartThings supports two authentication mechanisms:

### 1. Official CLI OAuth Login (Recommended & Persistent)
Personal Access Tokens (PATs) created via the web console expire after **24 hours**. For permanent, non-expiring access, authenticate via the official CLI:

```sh
# 1. Install CLI
npm install -g @smartthings/cli

# 2. Login once via browser
smartthings devices
```

The CLI saves an OAuth access token and **refresh token** to local storage:
- macOS: `~/Library/Application Support/@smartthings/cli/credentials.json`
- Linux: `~/.config/@smartthings/cli/credentials.json`

The CLI and the bundled `st.py` helper automatically use and rotate these tokens without manual intervention.

### 2. Personal Access Token (PAT) (Short-lived)
For temporary or headless testing, set an environment variable:

```sh
export SMARTTHINGS_API_TOKEN="your_personal_access_token"
# Or:
export SMARTTHINGS_TOKEN="your_personal_access_token"
```

*(Generated from [account.smartthings.com/tokens](https://account.smartthings.com/tokens); valid for 24 hours).*

---

## Method 1: Official SmartThings CLI (`smartthings`)

The official CLI is installed globally as `smartthings`.

### 1. List Devices
```sh
# Formatted table of all devices
smartthings devices

# Output as JSON
smartthings devices -j

# Filter by capability
smartthings devices --capability switch
smartthings devices --capability airConditionerMode
```

### 2. Check Device Status
```sh
# Human-readable status overview
smartthings devices:status <DEVICE_ID>

# Detailed JSON (shows all components like main, edgelight, cooler)
smartthings devices:status <DEVICE_ID> -j
```

### 3. Send Commands
Syntax: `smartthings devices:commands <DEVICE_ID> [<component>:]<capability>:<command>([<args>])`

```sh
# Simple switch (main component)
smartthings devices:commands <DEVICE_ID> switch:on
smartthings devices:commands <DEVICE_ID> switch:off

# Multi-component devices (e.g. AC indirect lighting / edgelight)
smartthings devices:commands <DEVICE_ID> edgelight:switch:on
smartthings devices:commands <DEVICE_ID> edgelight:switch:off

# Dimmer / Brightness (0-100)
smartthings devices:commands <DEVICE_ID> 'switchLevel:setLevel(50)'

# Color Temperature (Kelvin)
smartthings devices:commands <DEVICE_ID> 'colorTemperature:setColorTemperature(3000)'

# Air Conditioner Temperature Setpoint (°C)
smartthings devices:commands <DEVICE_ID> 'thermostatCoolingSetpoint:setCoolingSetpoint(24)'

# Air Conditioner Operating Mode
smartthings devices:commands <DEVICE_ID> 'airConditionerMode:setAirConditionerMode("cool")'
```

---

## Method 2: Bundled Helper (`st.py` / `st`)

A standalone, zero-dependency Python script is provided at `scripts/st.py` (or symlinked to `st` on `PATH`). It automatically discovers active tokens from the official CLI credentials file or environment variables, and resolves devices by **fuzzy label match**.

```sh
# Run via PATH (if symlinked):
st <command>

# Or run via Python directly:
python3 scripts/st.py <command>
```

### Common Commands

```sh
# List devices (supports keyword filter)
st devices
st devices -f "air conditioner"
st devices -f "light"

# Status lookup by device label
st status "Living Room AC"
st status "Bed Light"

# On / Off
st on "Bed Light"
st off "Bed Light"

# Dimmer & Color Temperature
st level "Bed Light" 60
st color-temp "Bed Light" 2700

# Climate
st temp "Living Room AC" 24.0
st temp "Thermostat" 21.0 --heating

# Custom command on sub-component
st cmd "<DEVICE_LABEL_OR_ID>" samsungce.airConditionerLighting on --component edgelight
```

---

## Method 3: Direct REST API (`curl`)

Base URL: `https://api.smartthings.com/v1`  
Header: `Authorization: Bearer <TOKEN>`

### 1. List Devices
```sh
curl -s -H "Authorization: Bearer $TOKEN" https://api.smartthings.com/v1/devices
```

### 2. Device Status
```sh
curl -s -H "Authorization: Bearer $TOKEN" https://api.smartthings.com/v1/devices/<DEVICE_ID>/status
```

### 3. Send Command Payload
Endpoint: `POST https://api.smartthings.com/v1/devices/<DEVICE_ID>/commands`

```json
{
  "commands": [
    {
      "component": "edgelight",
      "capability": "switch",
      "command": "on",
      "arguments": []
    }
  ]
}
```

```sh
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commands":[{"component":"main","capability":"switch","command":"on"}]}' \
  https://api.smartthings.com/v1/devices/<DEVICE_ID>/commands
```

---

## Capability Reference Summary

| Capability | Component | Command | Example Argument | Purpose |
|---|---|---|---|---|
| `switch` | `main` | `on` / `off` | *(none)* | Main power |
| `switch` | `edgelight` | `on` / `off` | *(none)* | AC ceiling indirect light |
| `switchLevel` | `main` | `setLevel` | `50` | Brightness level (0-100%) |
| `colorTemperature` | `main` | `setColorTemperature` | `2700` | Warm to cool (Kelvin) |
| `colorControl` | `main` | `setColor` | `{"hue": 0, "saturation": 0}` | RGB Color |
| `thermostatCoolingSetpoint` | `main` | `setCoolingSetpoint` | `24.0` | Cooling target temperature (°C) |
| `thermostatHeatingSetpoint` | `main` | `setHeatingSetpoint` | `21.0` | Heating target temperature (°C) |
| `airConditionerMode` | `main` | `setAirConditionerMode` | `"cool"` | AC mode (`cool`, `auto`, `dry`, `fan`) |
| `samsungce.airConditionerLighting` | `edgelight` | `setLightingLevel` | `"smart"` | AC light level (`smart`, `high`, `low`) |

---

## Troubleshooting

- **HTTP 401 Unauthorized**: Run `smartthings devices` to re-authenticate via browser and refresh the OAuth session, or update the `SMARTTHINGS_API_TOKEN` environment variable.
- **Component Names**: If commands against `main` fail on appliances (cooktops, air conditioners, refrigerators), run `smartthings devices:status <id> -j` and inspect `.components` for specialized parts like `edgelight`, `light`, `cooler`, `freezer`, `burnerLeft`.
