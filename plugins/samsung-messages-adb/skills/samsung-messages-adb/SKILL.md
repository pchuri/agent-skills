---
name: samsung-messages-adb
description: Read and search text messages on a Samsung Galaxy (Android) phone from a computer using adb — SMS, MMS (long/picture messages), and RCS chats (Samsung 채팅+) — plus call recordings and screenshots. Use when the user asks to find, read, export, or analyze phone text messages (문자/채팅+) via adb, or when a message visible in the Samsung Messages app doesn't show up in a content query.
---

# Samsung Messages over adb (SMS · MMS · RCS)

Query text messages on a Samsung Galaxy phone directly from a computer with
`adb shell content query` — no app installs, no root (tested on One UI /
recent Galaxy models; some devices or carrier builds may restrict access).

## The one thing to know: there are THREE message stores

The Samsung Messages app displays a single conversation, but under the hood
messages are split across three content providers. **A keyword search that
only checks one store will silently miss messages that are plainly visible
on the phone screen.**

| What the app shows | Store (content URI) | Body location | `date` unit |
|---|---|---|---|
| Short text (SMS) | `content://sms` | `body` column | **milliseconds** |
| Long text / picture (MMS) | `content://mms` | **NOT in this table** — text lives in `content://mms/part` | **seconds** |
| Chat+ / RCS (채팅+) | `content://im/chat` (Samsung-specific) | `body` column | **milliseconds** |

Two classic traps, both encountered in real use:

1. **Long messages are MMS.** Korean academies, banks, and businesses send
   anything over ~90 bytes as MMS (the app labels it "MMS"). Its text is
   stored per-part in `content://mms/part`, so `body LIKE '%keyword%'`
   against `content://sms` or `content://im/chat` finds nothing.
2. **`date` units differ.** Copy-pasting a millisecond range from an SMS
   query into an MMS query matches zero rows. Divide by 1000 for MMS.

## Prerequisites

- Phone connected via USB with **USB debugging** enabled and authorized
  (`adb devices` shows state `device`, not `unauthorized`).
- `adb` installed — macOS: `brew install --cask android-platform-tools`.

## Quoting

`content query --where` needs the SQL wrapped in escaped quotes so it
survives both the local shell and the remote `adb shell`:

```sh
adb shell content query --uri content://sms --where "\"address='0212345678'\""
```

Same for `--sort`: `--sort '"date DESC"'`.

## Recipes

### Recent SMS (short texts)

```sh
adb shell content query --uri content://sms \
  --projection address,date,type,body --sort '"date DESC"' | head -60
```

`type`: 1 = received, 2 = sent. `date` is Unix **ms**.

### Search a keyword everywhere (all three stores)

```sh
# 1. SMS
adb shell content query --uri content://sms \
  --projection address,date,type,body --where "\"body LIKE '%keyword%'\""

# 2. MMS — search the part table directly (text parts only)
adb shell content query --uri content://mms/part \
  --projection mid,ct,text --where "\"ct='text/plain' AND text LIKE '%keyword%'\""

# 3. RCS (Chat+)
adb shell content query --uri content://im/chat \
  --projection address,date,type,body --where "\"body LIKE '%keyword%'\""
```

Only after all three return nothing can you conclude the message isn't on
this phone (e.g., it was sent to a family member's number instead).

### Read a full MMS (date, sender, text)

```sh
# Find the message id (note: date in SECONDS)
adb shell content query --uri content://mms \
  --projection _id,date --where "\"date BETWEEN 1787356800 AND 1787443200\""

# Text parts for that message (mid = the _id above)
adb shell content query --uri content://mms/part \
  --projection mid,ct,text --where "\"mid=12539 AND ct='text/plain'\""

# Sender address (type 137 = From, 151 = To)
adb shell content query --uri "content://mms/12539/addr" \
  --projection address,type
```

Image/file parts: rows in `mms/part` with `ct='image/jpeg'` etc. Dump one
with `adb shell content read --uri content://mms/part/<part_id> > out.jpg`.

### Read a conversation with one number

```sh
adb shell content query --uri content://sms \
  --projection date,type,body --where "\"address='0212345678'\"" --sort '"date ASC"'
```

Repeat against `im/chat` (and `mms` via the addr table) for the complete
thread. Numbers may be stored with or without hyphens/country code — if an
exact match fails, try `address LIKE '%1234567%'` with the last digits.

### Convert timestamps

```sh
python3 -c "import datetime; print(datetime.datetime.fromtimestamp(1787380060))"   # MMS (s)
python3 -c "import datetime; print(datetime.datetime.fromtimestamp(1787380060045/1000))"  # SMS/RCS (ms)
```

## Related: recordings and screenshots

Often wanted in the same session (e.g., analyzing a call the message refers to):

- Call recordings (Samsung call recorder): `/sdcard/Recordings/Call/` — `adb pull`
- Screenshots: `/sdcard/DCIM/Screenshots/`

## Pitfalls

- **"No result found" is not proof.** Check the other two stores, the date
  unit, and hyphen/format variants of the address first.
- **Rows are multi-line.** Message bodies contain newlines, so `head -40`
  may show only a dozen rows. Filter with `--where`, not by truncating output.
- **RCS bodies may be JSON.** Rich cards (banks, brands) arrive as
  `generalPurposeCard` JSON in the `body` column — `LIKE` still works, but
  the human-readable text is inside the `description` field.
- **Read-only by intent.** Query, don't `content insert/update/delete` —
  corrupting the messages DB is not recoverable. Treat exported contents as
  sensitive personal data: keep them local and out of commits/logs.
- **Permission denied?** Some builds block shell access to these providers.
  There is no safe workaround via adb alone; fall back to on-phone export or
  Samsung Smart Switch backup parsing.
