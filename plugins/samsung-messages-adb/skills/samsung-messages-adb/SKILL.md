---
name: samsung-messages-adb
description: Read, search, and send text messages on a Samsung Galaxy (Android) phone from a computer using adb — SMS, MMS (long/picture messages), and RCS chats (Samsung 채팅+) — plus call recordings and screenshots. Use when the user asks to find, read, export, or analyze phone text messages (문자/채팅+) via adb, when a message visible in the Samsung Messages app doesn't show up in a content query, or when they want to send a message from the computer.
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

## Sending a message (draft by intent, send by UI tap)

There is no clean adb path that puts a message on the air. Two routes that
look like they should work are dead ends:

- **`content insert` into `content://sms`** writes a row into the phone's
  local database. That fabricates a "sent" record with no radio traffic at
  all, and recent Android blocks writes from anything but the default SMS
  app anyway.
- **`service call isms <txn> ...`** — the telephony binder is present
  (`service list | grep isms`), but the transaction numbers move between
  Android versions, arguments have to be marshalled into a Parcel by hand,
  and since Android 10 the shell UID has no `SEND_SMS`, so the call dies
  with a SecurityException.

What works is two steps: hand the text to the Messages app with an intent,
then press its Send button through UI automation.

### 1. Prefill the draft — reversible, nothing is sent

```sh
adb shell am start -a android.intent.action.SENDTO \
  -d "sms:01012345678" --es sms_body "\"message text\"" --ez exit_on_sent true
```

Opens the compose screen with recipient and body filled in and stops there.
`exit_on_sent` closes the app once a send completes.

**The escaped quotes on `sms_body` are required**, for the same reason as
[Quoting](#quoting) above: `adb shell` joins its arguments with spaces and
re-parses them on the device, so a plain `"message text"` arrives as two
separate arguments and only the first word becomes the body. Verify with
`adb shell printf '[%s]\n' --es sms_body "\"a b\""`.

### 2. Find the Send button, then tap it

Eyeballing coordinates lands taps on the wrong control. Dump the live view
hierarchy instead:

```sh
adb shell uiautomator dump /sdcard/ui.xml
adb shell cat /sdcard/ui.xml | tr '>' '\n' | grep -i "send\|보내기"
```

Take `bounds="[x1,y1][x2,y2]"` from the matching node and tap its centre —
this is the moment the message actually goes out:

```sh
adb shell input tap 1000 2150
```

### Constraints

- **Screen on and unlocked.** This is UI automation, not an API.
- **SMS vs RCS is not yours to pick.** Samsung Messages decides per
  recipient (Chat+/RCS where supported, SMS otherwise); the intent has no
  knob for it. A thread that lives in `content://im/chat` will go out as RCS.
- **Confirm before the tap.** Step 1 is reversible; step 2 delivers
  immediately and cannot be recalled. Show the user the exact recipient and
  final wording and get an explicit yes before running `input tap`.
- **Check who owns the SMS role** if the layout in step 2 looks unfamiliar:
  `adb shell cmd role get-role-holders android.app.role.SMS`.

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
- **The message DB is read-only.** Query, don't `content insert/update/
  delete` — corrupting it is not recoverable, and inserting a row is not
  sending (see Sending above). Treat exported contents as sensitive personal
  data: keep them local and out of commits/logs.
- **Permission denied?** Some builds block shell access to these providers.
  There is no safe workaround via adb alone; fall back to on-phone export or
  Samsung Smart Switch backup parsing.
