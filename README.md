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
  - **LLM route:** Google Gemini (free tier, `gemini-3.6-flash`) through its OpenAI-compatible endpoint, asked for JSON fields. OpenAI or Anthropic keys also work. Used when an API key is set.
  - **Rule-based route:** a simple built-in parser used when no key is set or the LLM call fails.
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
- **Starter prototype.** Generated with Claude and tested with four cases: clear request, simulated mishearing, out of scope, missing time. ([commit])
- **Rule parser limits.** "Half three tomorrow" gave no time and put "at half 3" into the task; "next Tuesday at 10am" was read as today, but the validator blocked it ("10:00 today has already passed"). This showed the need for an LLM and confirmed that validating model output matters.
- **Free LLM.** Added Google Gemini's free tier so no paid key is needed. ([commit])
- **HTTP 404 from Gemini.** Every request fell back to the rule parser. I listed the models my key could use and found the default (`gemini-2.5-flash`) was no longer offered; switched to an available model. ([commit])
- **Timeouts.** `gemini-3.8-flash` took over 30 seconds and timed out. I measured `gemini-3.6-flash` directly at 2.5 seconds, switched to it, lowered the model's reasoning effort, and raised the timeout to 45 seconds. Retested: "half three tomorrow" now gives 15:30 tomorrow, saved at confidence 0.95. ([commit])

## AI assistance
[FILL IN: tools used, what you asked for, what you changed or rejected, and how you checked it. For example: "Used Claude to generate the starter app; I tested the four cases above, changed X, rejected Y."]

## Additional files
None.