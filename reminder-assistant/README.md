# Reminder Assistant: showing what was heard so mishearings can be fixed

README prose word count: [FILL IN]

## Project status
- **Implemented:** text request → field extraction (task, time, day) → validation → confidence policy → confirmation card showing what was heard and understood → confirm, change one field, or cancel → saved list with undo. Out-of-scope requests (location-based or repeating reminders) get a reply saying what the assistant *can* do. Every step is logged to `interaction_log.jsonl`.
- **Simulated:** speech input (typed text stands in for speech recognition); per-word recognition confidence; mishearings (a test switch swaps, for example, "3:15" for "3:50" and marks that word as low confidence).
- **Planned:** real microphone input (browser speech recognition); spoken confirmation for screenless devices; real reminder notifications.

## Technology stack
- Python 3 standard library only (`http.server`); no packages to install.
- HTML and JavaScript front end (`static/index.html`).
- Field extraction (`extract.py`):
  - **LLM route:** Google Gemini (free tier, `gemini-3.8-flash`) through its OpenAI-compatible endpoint, asked for JSON fields. OpenAI or Anthropic keys also work. Used when an API key is set.
  - **Rule-based route:** a simple built-in parser used when no key is set. It stands in for the LLM so the prototype runs without a key.
- [FILL IN: AI coding tools you used]

## Running it
```
python app.py
```
Open http://localhost:8000.

Optional, to use an LLM instead of the rule-based parser. Get a free key at https://aistudio.google.com (API keys). Use your own key and never commit it:
```
# Windows PowerShell
$env:GEMINI_API_KEY="your-key"
python app.py
# macOS/Linux
export GEMINI_API_KEY=your-key
python app.py
```
`OPENAI_API_KEY` or `ANTHROPIC_API_KEY` also work. Set `MODEL` to change the model.

Try:
1. `Remind me to call mum at 3:15 tomorrow`: saved straight away with Undo (high confidence).
2. The same request with **Simulate a mishearing** ticked: shows 3:50 highlighted; change the time and save.
3. `Remind me to buy milk when I get home`: out of scope, so it says what it can do instead.
4. `Remind me to call the dentist`: no time given, so it asks for the time instead of guessing.

## Development record
[FILL IN as you go. A few entries are enough, each with what changed, why, and what you checked. Link commits.]
- Example format: *Test B (mishearing): after correcting the time, the card still said "I wasn't sure". Changed it to confirm what was changed. Retested and the message updated (commit abc123).*

## AI assistance
[FILL IN: tools used, what you asked for, what you changed or rejected, and how you checked it. For example: "Used Claude to generate the starter app; I tested the four cases above, changed X, rejected Y."]

## Additional files
None.