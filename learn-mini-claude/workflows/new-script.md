---
name: new-script
description: Create a Python script, verify it runs, and record it in notes
steps:
  - Write the script to <target> using write_file. Keep it small and self-contained.
  - Run it with run_command (`python <target>`) and check the exit code is 0.
  - If it failed, fix the script and run it again before continuing.
  - Save a note via notes__save_note summarising what the script does, tagged "script".
---

Use this whenever the user asks for a new script rather than an edit to
an existing one.

Notes:
- Step 2 is the point of the workflow. A script that was written but
  never executed is not done, however confident the code looks.
- If run_command is unavailable (the web UI blocks it), say so explicitly
  at step 2 and mark the step complete with that caveat rather than
  silently skipping it.
