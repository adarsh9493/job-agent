---
name: Portal Login
description: Create or log in to career-portal accounts in a visible browser, handle password resets and Gmail OTPs, reuse sessions, and store shared credentials in the vault.
---

# Portal Login

**Goal:** get authenticated on a company's career portal so application-fill can submit.

> From here through final submission the browser is **VISIBLE** (`AGENTS.md`, section I).

## Inputs

- `data/profile/profile.json` — legal name, job email.
- `data/profile/answers-bank.json`.
- `data/vault/credentials.txt` — existing shared credentials.
- Gmail MCP for OTPs and reset links.

## Steps

1. **Try the existing login first** using stored credentials.
2. If no account exists, **create one** with the user's job email.
3. If an account exists with an unknown password, use **"forgot password"** and reset it to the
   shared password.
4. Handle email verification / OTP by querying Gmail narrowly (sender domain + recent timestamp) and
   reading only the link or OTP (`AGENTS.md` rule 2).
5. **PASSWORD_MODE = shared.** One password for **all** portal accounts (never the user's email
   password). Ask the user once, or generate a strong 16+ char password and tell them. Reset
   existing accounts to it.
6. Store in `data/vault/credentials.txt`: portal, URL, username, date. **Never print the password in
   chat.** Restrict the file to the owner (chmod 700 on POSIX; owner-only ACL on Windows).
7. **Reuse the session:** keep the logged-in tab/session for other roles at the same company. If
   unreliable, rely on the persistent browser profile's cookies.

## Rules

- Clear the cookie/consent banner before touching the form (`AGENTS.md` rule 8).
- One account per portal.
- Visible browser from here onward.

## Outputs

- Authenticated session; `data/vault/credentials.txt` updated.
