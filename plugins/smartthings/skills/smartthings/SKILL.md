---
name: smartthings
description: Query and control Samsung SmartThings devices (lights, smart plugs, air conditioners, appliances, sensors) via the official SmartThings REST API using a Personal Access Token (PAT). Use when asked to list smart home devices, check status/readings, turn appliances or lights on/off, adjust brightness or color temperature, or set thermostat/AC temperatures.
---

# SmartThings REST API Skill

Query and control Samsung SmartThings smart home devices via the official REST API (`https://api.smartthings.com/v1`).

Includes both a zero-dependency Python 3 CLI tool (`scripts/st.py`) and standard `curl` recipes.

## Prerequisites

Set your SmartThings Personal Access Token (PAT) in your environment:

```sh
export SMARTTHINGS_API_TOKEN="your_personal_access_token"
```

*(Alternatively `SMARTTHINGS_TOKEN` is also recognized).*

To generate a token, visit [SmartThings Personal Access Tokens](https://account.smartthings.com/tokens) and grant the required scopes (`devices:*`, `locations:*`).

---

## Bundled CLI Tool (`st.py`)

A zero-dependency Python script is provided in `scripts/st.py`. It accepts either a **Device ID** or a **Device Label/Name** (case-insensitive substring match).

Locate the script relative to this skill directory:
```sh
ST_BIN="$(dirname "$0")/scripts/st.py"
# Or run directly if in skill folder:
python3 scripts/st.py <command>
```

### Common CLI Recipes

#### 1. List Devices
```sh
# List all devices
python3 scripts/st.py devices

# Filter by label or model name
python3 scripts/st.py devices --filter "light"
python3 scripts/st.py devices --filter "air conditioner"

# JSON output
python3 scripts/st.py devices --json
```

#### 2. Inspect Real-time Status
```sh
# By exact or partial label
python3 scripts/st.py status "Bed Light"
python3 scripts/st.py status "Living Room AC"

# Raw JSON status
python3 scripts/st.py status "Bed Light" --json
```

#### 3. Control Switches & Lights
```sh
# Turn ON / OFF
python3 scripts/st.py on "Bed Light"
python3 scripts/st.py off "Bed Light"

# Set brightness percentage (0-100)
python3 scripts/st.py level "Bed Light" 50

# Set color temperature in Kelvin (e.g., 2700 warm white to 6500 cool daylight)
python3 scripts/st.py color-temp "Bed Light" 2700
```

#### 4. Control Thermostats & Air Conditioners
```sh
# Set cooling target temperature in Celsius
python3 scripts/st.py temp "Living Room AC" 24.0

# Set heating target temperature
python3 scripts/st.py temp "Thermostat" 21.0 --heating
```

#### 5. Send Raw Capability Commands
```sh
# Set AC operating mode
python3 scripts/st.py cmd "Living Room AC" airConditionerMode setAirConditionerMode '"cool"'

# Multi-component devices (e.g., cooktop burner, sub-switches)
python3 scripts/st.py cmd "<device-id>" switch off --component "sub_component"
```

---

## Direct REST API (`curl`) Recipes

Base URL: `https://api.smartthings.com/v1`  
Header: `Authorization: Bearer $SMARTTHINGS_API_TOKEN`

### 1. List Devices

```sh
curl -s -H "Authorization: Bearer $SMARTTHINGS_API_TOKEN" \
  https://api.smartthings.com/v1/devices
```

### 2. Get Device Status

```sh
curl -s -H "Authorization: Bearer $SMARTTHINGS_API_TOKEN" \
  https://api.smartthings.com/v1/devices/<DEVICE_ID>/status
```

### 3. Send Commands

Commands are dispatched via `POST /devices/<DEVICE_ID>/commands` with a JSON payload:

```json
{
  "commands": [
    {
      "component": "main",
      "capability": "<CAPABILITY_NAME>",
      "command": "<COMMAND_NAME>",
      "arguments": []
    }
  ]
}
```

#### Turn Switch On / Off
```sh
curl -s -X POST -H "Authorization: Bearer $SMARTTHINGS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commands":[{"component":"main","capability":"switch","command":"on"}]}' \
  https://api.smartthings.com/v1/devices/<DEVICE_ID>/commands
```

#### Set Brightness (Level)
```sh
curl -s -X POST -H "Authorization: Bearer $SMARTTHINGS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commands":[{"component":"main","capability":"switchLevel","command":"setLevel","arguments":[50]}]}' \
  https://api.smartthings.com/v1/devices/<DEVICE_ID>/commands
```

#### Set Color Temperature
```sh
curl -s -X POST -H "Authorization: Bearer $SMARTTHINGS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commands":[{"component":"main","capability":"colorTemperature","command":"setColorTemperature","arguments":[3000]}]}' \
  https://api.smartthings.com/v1/devices/<DEVICE_ID>/commands
```

#### Set AC Cooling Setpoint
```sh
curl -s -X POST -H "Authorization: Bearer $SMARTTHINGS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commands":[{"component":"main","capability":"thermostatCoolingSetpoint","command":"setCoolingSetpoint","arguments":[25.0]}]}' \
  https://api.smartthings.com/v1/devices/<DEVICE_ID>/commands
```

---

## Standard Capabilities Reference

| Capability | Commands | Arguments | Example |
|---|---|---|---|
| `switch` | `on`, `off` | *(none)* | Turn device power on or off |
| `switchLevel` | `setLevel` | `[level: int (0-100)]` | Adjust dimmer / brightness |
| `colorTemperature` | `setColorTemperature` | `[kelvin: int]` | 2500K (warm) ~ 6500K (cool) |
| `colorControl` | `setColor` | `[{"hue": float, "saturation": float}]` | Hue (0-100), Saturation (0-100) |
| `thermostatCoolingSetpoint` | `setCoolingSetpoint` | `[temperature: float]` | Target cooling temperature (°C) |
| `thermostatHeatingSetpoint` | `setHeatingSetpoint` | `[temperature: float]` | Target heating temperature (°C) |
| `airConditionerMode` | `setAirConditionerMode` | `[mode: string]` | `"cool"`, `"auto"`, `"dry"`, `"wind"` |
| `airConditionerFanMode` | `setFanMode` | `[mode: string]` | `"low"`, `"medium"`, `"high"`, `"auto"` |

---

## Tips & Troubleshooting

- **Multi-component devices**: While most bulbs, outlets, and sensors use `component: "main"`, some appliances (such as multi-burner cooktops or multi-door refrigerators) use discrete components (e.g. `cooler`, `freezer`, `burnerLeft`). Check `curl .../devices/<DEVICE_ID>` to inspect available components.
- **HTTP 401 Unauthorized**: Check that `SMARTTHINGS_API_TOKEN` is set and hasn't expired.
- **HTTP 403 Forbidden**: Verify that the PAT was created with scopes for the requested device or location.
- **Offline Devices**: In `status`, check `healthCheck.DeviceWatch-DeviceStatus`. If `offline`, commands may fail or time out.
