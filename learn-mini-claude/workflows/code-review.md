---
name: code-review
description: Review a file for bugs and write the findings to a report
steps:
  - Read <target> with read_file. Do not review from memory or guesswork.
  - Identify concrete problems - bugs, crashes, edge cases. Cite line numbers.
  - Write the findings to <target>-review.md with write_file.
  - Save a one-line summary via notes__save_note, tagged "review".
---

Review guidance:
- Report only defects you can point at in the file you actually read.
  "Could be more readable" is not a finding; "IndexError when items is
  empty, line 12" is.
- If the file has no real defects, say so plainly. A review that invents
  problems to look thorough is worse than a short one.
