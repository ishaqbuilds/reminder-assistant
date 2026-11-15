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
## AI assistance
**Tools**
- **Claude (Anthropic, claude.ai):** development and writing assistant.
- **Google Gemini 3.6 Flash:** the model the app itself calls to extract reminder fields. It is part of the system, not a development aid.

**What I asked Claude to help with**
- Generating the starter prototype (Python server, rule-based parser, confirmation-card page) from my Assignment 1 design: show what was heard, confirm when unsure, correct one field.
- Diagnosing and fixing problems I found while testing: the Gemini 404, the timeouts, the "next Tuesday" refusal, the silent fallback and duplicate reminders.
- Drawing the system diagram, laying out the storyboards from my screenshots, and drafting the report text.

**How I used, changed or rejected its suggestions**
- Claude first suggested a paid OpenAI key. I chose a free option instead, so Gemini support was added.
- Claude's suggested default model (`gemini-2.5-flash`) returned 404 for my key. I listed the models my key could use, and the next suggestion (`gemini-3.8-flash`) timed out. I measured response times myself in PowerShell (3.6 Flash: 2.5 s) and picked the faster model.
- Each fix responded to a problem I found by testing, not one Claude predicted. The commit messages and development record show which problem each change addressed.
- [Add one or two edits you made yourself to the report or code, e.g. wording you rewrote or a value you changed.]

**How I checked the results**
- Ran the same test requests after every change (clear request, simulated mishearing, out of scope, missing time, "half three", "tonight", "next Tuesday") and compared the screens, keeping screenshots.
- Checked the parser label on screen (`parser: llm` versus `rules (LLM failed)`) and the terminal errors to confirm which route had actually run.
- Checked every reference in the report against my verified Assignment 1 sources and the lecture slides; none were taken from AI output without checking.
- Kept the API key out of every file: it is set only in the terminal.

## Additional files
None.
