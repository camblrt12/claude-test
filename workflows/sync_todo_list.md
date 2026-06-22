# Workflow: Sync Todo List

## Objective
Scan Slack DMs/mentions, Gmail inbox, and Google Agenda for new action items directed at me. Extract tasks, infer priority and due dates, and write them to the "Tâches Camille" Notion database. Update the processed-IDs ledger so nothing is re-processed on the next run.

## Database
**"✅ Tâches Camille"** — in Home Camille  
- Notion database ID: `14dd175d97c54f83888517d79f7bfe0f`
- Data source ID: `collection://6d0be151-1ebb-4f3a-9607-0f7fa70d8ad2`

## Schema Reference

| Notion field | Type | Values / notes |
|---|---|---|
| Tâche | title | Task description |
| Statut | status | `À faire` / `En cours` / `Terminé` |
| Priorité | select | `Haute` / `Moyenne` / `Basse` |
| Type | select | `RH` / `Management` / `Produit` / `Administration` / `Stratégie` / `Autre` |
| Personne concernée | select | `Morgane` / `Romain` / `Tom` / `Louis` / `Laura` |
| Échéance | date | Due date |
| Source | select | `Slack` / `Gmail` / `Agenda` / `Manuel` *(automation field)* |
| Lien | url | Deep link to original message or event *(automation field)* |
| ID message | rich_text | Dedup key, not shown in views *(automation field)* |

## Inputs
- `.env` keys: `NOTION_DATABASE_ID`, `PROJECT_TAGS`, `CALENDAR_PREP_LEAD_DAYS`, `CALENDAR_SKIP_PATTERNS`
- `.tmp/processed_ids.json` — ledger of already-processed message/event IDs

## Tools Available
- Slack MCP: `slack_search_public_and_private`, `slack_read_thread`
- Gmail MCP: `search_threads`, `get_thread`
- Google Agenda MCP: list/read upcoming events
- Notion MCP: `notion-query-database-view`, `notion-create-pages`
- `tools/check_processed.py` — filters a list of IDs down to only new ones
- `tools/save_processed.py` — appends processed IDs to the ledger
- `tools/merge_tasks.py` — fuzzy-deduplicates extracted tasks across sources

---

## Step-by-Step

### Step 1 — Fetch new Slack messages

1a. Search Slack for DMs and mentions received in the last 25 hours:
```
slack_search_public_and_private(query="to:me after:yesterday")
slack_search_public_and_private(query="@camille after:yesterday")
```

1b. Collect all message IDs (format: `slack:<channel_id>:<message_ts>`).

1c. Run `python3 tools/check_processed.py '<json_array_of_ids>'` — keep only the returned new IDs.

1d. For each new message, fetch thread context if needed (`slack_read_thread`). Keep: message text, sender name, timestamp, deep link.

---

### Step 2 — Fetch new Gmail threads

2a. Search Gmail for unread threads in the last 25 hours:
```
search_threads(query="is:unread newer_than:1d -from:me -category:promotions -category:social")
```

2b. Collect thread IDs (format: `gmail:<thread_id>`).

2c. Run `python3 tools/check_processed.py '<json_array_of_ids>'` — keep only new ones.

2d. For each new thread, fetch full content with `get_thread`. Keep: subject, sender, body, date, deep link.

---

### Step 3 — Fetch upcoming Google Agenda events

3a. Fetch all calendar events for the next `CALENDAR_PREP_LEAD_DAYS` days (from .env, default 2).

3b. Collect event IDs (format: `cal:<event_id>`).

3c. Run `python3 tools/check_processed.py '<json_array_of_ids>'` — keep only new event IDs.

3d. **Skip an event if any of the following are true:**
- Attendee count is 1 (solo block / focus time)
- Event title contains any keyword from `CALENDAR_SKIP_PATTERNS` (case-insensitive)
- All-day non-meeting event (e.g. "Congés", "Férié")

---

### Step 4 — Extract tasks

For each new item, decide whether it requires action from me. Ask:

> "Is there something specific being asked of me, or that I need to prepare?"

**Extract a task if:**
- Someone is explicitly asking me to do something ("peux-tu", "merci de", "il faudrait que tu", "can you", "please")
- There's a deliverable with a deadline involving me
- A meeting requires preparation (agenda to write, materials to review, decision to prepare)
- A decision is being requested from me

**Do NOT extract a task if:**
- It's informational / FYI with no action
- It's an automated notification (CI/CD, tool alerts, calendar confirmations)
- The message is sent by me
- It's a vague open question with no deliverable ("qu'est-ce que tu penses ?")

**For each extracted task, produce a JSON object:**
```json
{
  "tache": "Short, actionable description (imperative: 'Relire la spec de X', 'Préparer l'ordre du jour de Y')",
  "statut": "À faire",
  "priorite": "Haute | Moyenne | Basse",
  "type": "RH | Management | Produit | Administration | Stratégie | Autre",
  "personne": "Name matching one of [Morgane, Romain, Tom, Louis, Laura], or empty string",
  "echeance": "YYYY-MM-DD if inferable, else null",
  "source": "Slack | Gmail | Agenda",
  "lien": "Deep link URL to original message or event",
  "id_message": "The source ID (e.g. slack:C12345:1234567890.123)"
}
```

**Priorité mapping:**
- `Haute`: "ASAP", "urgent", "bloquant", "critique", "ce soir", "ce matin", "avant midi", meeting within 24h
- `Moyenne`: "pour demain", "cette semaine", "important"; meeting within CALENDAR_PREP_LEAD_DAYS
- `Basse`: "quand tu as le temps", "pas urgent", "si possible"; everything else

**Échéance inference:**
- Parse: "pour vendredi" → next Friday, "fin de semaine" → Sunday, "EOD" / "ce soir" → today
- Calendar prep tasks: échéance = meeting date
- No date mentioned → null

**Type mapping (match by context, channel, or keywords):**
- `Produit`: product specs, features, UX, design, sprint, backlog, roadmap
- `Management`: 1:1s, team feedback, hiring, performance, org decisions
- `RH`: leave, payroll, onboarding, HR admin, contracts
- `Administration`: invoices, legal, tools, subscriptions, access
- `Stratégie`: OKRs, positioning, partnerships, fundraising, business decisions
- `Autre`: anything that doesn't fit the above

**Personne concernée mapping:**
- Only set if the sender name closely matches one of: Morgane, Romain, Tom, Louis, Laura
- Leave empty if sender is unknown or doesn't match

---

### Step 5 — Deduplicate across sources

Pass all extracted tasks to:
```
python3 tools/merge_tasks.py '<json_array_of_tasks>'
```

The script fuzzy-matches titles (edit distance < 15%) and merges duplicates (same request via Slack AND Gmail → one task, source becomes "Slack + Gmail").

---

### Step 6 — Check for existing tasks in Notion

Query the Notion database for tasks NOT yet "Terminé":
```
notion-query-database-view(database_id=14dd175d97c54f83888517d79f7bfe0f)
```

For each merged task:
- If a task with the same `ID message` already exists → **skip**
- If a task with an identical title and Statut ≠ "Terminé" already exists → **skip**
- Otherwise → **create**

---

### Step 7 — Write new tasks to Notion

For each task to create, call `notion-create-pages` with:

```
parent: { database_id: "14dd175d97c54f83888517d79f7bfe0f" }
properties:
  Tâche        → tache
  Statut       → "À faire"
  Priorité     → priorite
  Type         → type
  Personne concernée → personne (omit if empty)
  Échéance     → echeance (date, omit if null)
  Source       → source
  Lien         → lien (omit if empty)
  ID message   → id_message
```

---

### Step 8 — Save processed IDs

Collect ALL message/event IDs fetched in Steps 1–3 (not just those that became tasks).

Run:
```
python3 tools/save_processed.py '<json_array_of_all_fetched_ids>'
```

---

## Edge Cases

| Situation | Handling |
|---|---|
| Slack thread with multiple messages | Process as one unit; use the root message ID |
| Forwarded email | The ask may be in the forwarding note — parse both |
| Agenda event with no description | Generic prep task: "Préparer la réunion : [Titre]" |
| Same task from Slack + Gmail | merge_tasks.py merges; source shows "Slack + Gmail" |
| Ambiguous ask ("tes retours ?") | Skip unless there's a clear deliverable or deadline |
| No new items found | Log "Aucun nouvel élément à traiter" and exit cleanly |
| Notion write fails | Log the error, continue — don't lose other tasks |

## Expected Output

After a successful run, new rows appear in "Tâches Camille" for every actionable item found. No duplicates. The `.tmp/processed_ids.json` ledger is updated.

Log a brief summary:
- Slack: X messages scanned → Y tasks extracted
- Gmail: X threads scanned → Y tasks extracted
- Agenda: X events scanned → Y prep tasks created
- Notion: X tasks written
