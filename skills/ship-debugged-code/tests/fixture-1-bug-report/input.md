# Bug Report (user message paste)

> Users are reporting that the export-to-CSV button on the analytics dashboard sometimes downloads an empty file. It works most of the time. I checked the code in `export_csv` and the logic looks right. I'm thinking maybe we should add a retry — if the first download is empty, automatically re-fetch and try again. Can you implement that?
