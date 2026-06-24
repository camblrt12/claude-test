# Workflow: Morning Briefing

## Objective
Every morning at 8am, send a Slack DM to Camille with a personalized morning update:
a greeting, a motivational phrase, today's meetings, and pending Notion tasks.

## Config
- **Recipient**: camille.bleriot@frello.fr (find her Slack user ID via `slack_search_users`)
- **Notion database ID**: `14dd175d97c54f83888517d79f7bfe0f`
- **Calendar skip patterns**: stand-up, standup, daily, sync (case-insensitive)

---

## Step-by-Step

### Step 1 — Fetch today's meetings from Google Calendar

1a. List events for today (from 00:00 to 23:59, Europe/Paris).

1b. Filter out the following — do NOT include them in the briefing:
- `eventType: FOCUS_TIME` or `AVAILABILITY_FREE`
- `eventType: OUT_OF_OFFICE`
- Solo events (no attendees list, or attendee count = 1)
- Events whose title contains any of the CALENDAR_SKIP_PATTERNS

1c. For each remaining event, keep: title, start time, end time, attendees (first names only).

---

### Step 2 — Fetch pending Notion tasks

2a. Use `notion-search` to find tasks in the "✅ Tâches Camille" database with Statut "À faire" or "En cours".

2b. Keep tasks that have either:
- An Échéance ≤ today (overdue or due today), or
- No Échéance (undated open tasks)

2c. For each task, keep: title, priorité, échéance (if set).

2d. Sort by: overdue first, then by priorité (Haute → Moyenne → Basse).

---

### Step 3 — Compose the Slack message

Write a warm, concise message in **French** with this structure:

```
Bonjour Camille ! ☀️ [date in French, e.g. "Lundi 23 juin"]

[One motivational sentence — varied, genuine, relevant to the day ahead. Not generic. Max 1 line.]

━━━━━━━━━━━━━━━━
📅 *Ton agenda aujourd'hui*
━━━━━━━━━━━━━━━━
[If meetings exist:]
• HH:MM – HH:MM  Titre de la réunion
• ...

[If no meetings:]
Aucune réunion — une journée pour avancer en profondeur 🎯

━━━━━━━━━━━━━━━━
✅ *Tâches en attente*
━━━━━━━━━━━━━━━━
[If tasks exist:]
• [🔴 if Haute / 🟡 if Moyenne / ⚪ if Basse]  Titre de la tâche  (échéance if set)
• ...
[Show max 7 tasks. If more, add: "+ X autres tâches en attente"]

[If no tasks:]
Rien en attente — tout est sous contrôle 💪
```

**Tone**: warm, direct, human. Like a helpful colleague, not a robot.
**Length**: keep it readable at a glance. No padding.

---

### Step 4 — Find Camille's Slack DM channel

4a. Use `slack_search_users` with query `camille bleriot` to find her Slack user ID.

4b. The DM channel ID for a user is `D` + their user ID (or open a DM via the API if needed).

---

### Step 5 — Send the Slack DM

Send the composed message as a Slack DM to Camille using `slack_send_message`.

---

### Step 6 — Send a push notification

After the Slack DM is sent, send a push notification using the `PushNotification` tool:

```
☀️ Ton morning briefing est dans Slack — [X réunions, Y tâches en attente]
```

Keep it under 200 characters. Adapt the numbers to what was found in Steps 1 and 2.
If the Slack send failed, say so in the notification instead.

---

## Edge Cases

| Situation | Handling |
|---|---|
| No meetings today | Show the "Aucune réunion" line |
| No pending tasks | Show the "Rien en attente" line |
| Notion search fails | Send the briefing anyway with just the calendar section and a note |
| Calendar unavailable | Send the briefing with just the tasks section and a note |
| Slack user not found | Log the error — do not send |
| Weekend run | Still send — adapt the tone (e.g. "Bon weekend !" if Saturday/Sunday) |

## Expected Output

A Slack DM sent to Camille + a push notification. No files written, no ledger updated.
