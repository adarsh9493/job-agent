# Documents and file hygiene

## Pre-upload verification (mandatory)

Extract and verify the text of each PDF **before** uploading:

- Resume: at least 200 characters, contains the profile's legal name, no `{{...}}` placeholder.
- Cover letter (when the portal offers or requires the upload): at least 100 characters, contains
  the profile's legal name, no `{{...}}` placeholder.

Run `python scripts/tailoring/verify_pdf.py <resume.pdf> <cover.pdf>`. If a document the portal
requires fails, **do not submit** — regenerate it from filled HTML, re-verify, then continue. A
cover letter that cannot be uploaded because the portal has no field does not block submission;
record the limitation in the tracker.

After upload, verify the **visible attachment filename text** is present for every uploaded
document (Greenhouse replaces the file input, so `.files.length` is unreliable).

## Job folder

`data/applications/current/<Company>_<Title>_<JobID>_<YYYY-MM-DD>/` keeps only:

- `<First>_<Last>_Resume.pdf`
- `<First>_<Last>_CoverLetter.pdf`
- `job-description.md`
- `tailoring.json` (the job's tailoring configuration, when one exists)
- the confirmation screenshot after submission

Keep a DOCX only if a portal requires it. Delete HTML, intermediate PDFs, downloads, and failed
drafts after each application.

## Archive

After a successful submit, run `python scripts/runtime/archive.py` once to move confirmed folders
from `data/applications/current/` to `data/applications/history/`. A folder counts as applied when
it holds `confirmation_screenshot.png`, any image file, or a file named with `confirm` / `applied`
/ `success`. Run it again at stop to catch manually applied folders. Before ending a session,
confirm the project folder is clean and organized.
