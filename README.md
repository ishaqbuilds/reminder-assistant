# When Assistants Mishear: A Reminder Assistant That Shows What It Heard

README prose word count: about 950 (excluding code and commands)

## Project status
- **Implemented:** text request → field extraction (task, time, day) by an LLM → validation → confidence policy → confirmation card showing what was heard and understood → confirm, change one field, or cancel → saved list with Undo. Out-of-scope requests (location-based or repeating reminders) get a reply saying what the assistant *can* do. Duplicate reminders are blocked. If the LLM call fails, a rule-based parser takes over and the screen says so. Every step is logged to `interaction_log.jsonl`.
- **Simulated:** speech input (typed text stands in for speech recognition); per-word recognition confidence; mishearings (a test switch swaps, for example, "3:15" for "3:50" and marks that word as low confidence).
- **Planned:** real microphone input (browser speech recognition); voice-only read-back of the uncertain field for screenless devices; reminder notifications.

## Technology stack
- Python 3 standard library only (`http.server`); no packages to install.
- HTML and JavaScript front end (`static/index.html`).
- Field extraction (`extract.py`):
  - **LLM route:** Google Gemini (free tier, `gemini-3.6-flash`) through its OpenAI-compatible endpoint. The prompt includes today's date and asks for JSON fields. OpenAI or Anthropic keys also work.
  - **Rule-based route:** a simple parser used when no key is set or the LLM call fails.
- Development tools: VS Code, Git and GitHub; Claude (Anthropic) as a coding and writing assistant (see AI assistance).

## Running it
```
python app.py
```
Open http://localhost:8000.

To use the LLM, get a free key at https://aistudio.google.com (API keys). Use your own key and never commit it:
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
1. `Remind me to take my tablets at 9pm today`: saved straight away with Undo.
2. Tick **Simulate a mishearing**, then `Remind me to call mum at 3:15 tomorrow`: 3:50 is highlighted; change the time and save.
3. `Remind me to buy milk when I get home`: out of scope, so it says what it can do instead.
4. `Remind me to call the dentist`: no time given, so it asks rather than guessing.
5. `Remind me to call mum next Tuesday at 10am`: the date is worked out from today's date.

## Development record
Each change came from a test that went wrong. The full history is in the [commit list](https://github.com/ishaqbuilds/reminder-assistant/commits/main); each entry below names its commit message.

1. **Starter prototype.** Generated with Claude and tested with four cases: clear request, simulated mishearing, out of scope, missing time. *(Initial starter app)*
2. **Rule parser limits.** "Half three tomorrow" gave no time and put "at half 3" into the task; "next Tuesday at 10am" was read as today, but the validator blocked it ("10:00 today has already passed"). This showed the need for an LLM and confirmed that model output must be checked in code.
3. **Free LLM.** Added Google Gemini's free tier so no paid key is needed. *(Add free Gemini API as the LLM provider)*
4. **HTTP 404 from Gemini.** Every request fell back to the rule parser. I listed the models my key could use and found the default (`gemini-2.5-flash`) was no longer offered, so I switched model. *(Fix 404 from Gemini)*
5. **Timeouts.** `gemini-3.8-flash` took over 30 seconds and timed out. I measured `gemini-3.6-flash` directly in PowerShell at 2.5 seconds, switched to it, lowered the model's reasoning effort and raised the timeout to 45 seconds. Retested: "half three tomorrow" now gives 15:30 tomorrow. *(Switch default model to gemini-3.6-flash)*
6. **Model didn't know the date.** "Next Tuesday at 10am" was declined as out of scope, and the screen showed the model's raw wording. A model has no clock, so today's date is now added to the prompt on every call, and the app shows only its own fixed wording for out-of-scope replies. Retested: saved as Tue 17 Nov, 10:00. *(Give the LLM today's date…)*
7. **Silent AI failure.** When Gemini failed, the backup parser still saved reminders straight away at 0.9 confidence with no warning. A failed AI call now always shows the confirmation card with a warning, and the saved message says which parser ran. *(…show when the AI fails…)*
8. **Duplicates.** "Call mum at 3:15 tomorrow" could be saved twice. Saving now refuses an identical reminder. Retested: "You already have this reminder." *(…block duplicate reminders)*
9. **Repository layout.** The files were inside a nested folder, so the README did not show on GitHub. Moved them to the repository root. *(Move project files to repository root)*

## AI assistance
**Tools**
- **Claude (Anthropic, claude.ai):** development and writing assistant.
- **Google Gemini 3.6 Flash:** the model the app itself calls to extract reminder fields. It is part of the system, not a development aid.

**What I asked Claude to help with**
- Generating the starter prototype from my Assignment 1 design: show what was heard, confirm when unsure, correct one field.
- Diagnosing and fixing problems I found while testing (entries 4–8 above).
- Drawing the system diagram, laying out the storyboards from my screenshots, and drafting the report.

**How I used, changed or rejected its suggestions**
- Claude first suggested a paid OpenAI key. I chose a free option instead, so Gemini support was added.
- Two of the model names it suggested failed for my key (404, then a timeout). I listed the available models and measured response times myself before choosing `gemini-3.6-flash`.
- Each fix responded to a problem I found by testing, not one Claude predicted.
- I rewrote the abstract and scope of the report in my own words, corrected errors in the draft, and chose which screenshots to use for the storyboards.

**How I checked the results**
- Ran the same test requests after every change and compared the screens, keeping screenshots.
- Checked the parser label on screen (`parser: llm` or `rules (LLM failed)`) and the terminal errors to confirm which route had actually run.
- Checked every reference in the report against my verified Assignment 1 sources and the lecture slides.
- Kept the API key out of every file: it is set only in the terminal.

## Additional files
None. The report is submitted separately.
