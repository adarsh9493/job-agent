---
name: portal-login
description: Use when creating or logging in to career-portal accounts. Handle password resets and portal OTPs, reuse sessions, and store shared credentials in the vault.
---

# Portal Login

**Goal:** get authenticated on a company's career portal so application-fill can submit.

> From here through final submission the browser is **VISIBLE** (`AGENTS.md`, section I).

## Inputs

- `data/profile/profile.json` — legal name, job email.
- `data/profile/answers-bank.json`.
- `data/vault/credentials.txt` — existing shared credentials.
- Mail tool for OTPs and reset links.

## Steps

1. **Check the vault before any password reset.** Use
   `python scripts/runtime/creds.py get --domain <tenant-or-portal>`; it masks the password by
   default and applies the portal-specific Workday credential before the shared fallback. Only
   when entering a password into the visible form, use `--reveal`; do not echo, quote, log, or pass
   the value as a tool argument.
2. **Try the existing login first** using the saved portal-specific or shared credential. Use
   "Forgot password" only if the matching credential is absent, or the portal explicitly rejects
   the attempted password as invalid. A stale application page, signed-out session, timeout, or
   generic portal error is not proof that the password is wrong.
3. If no account exists, **create one** with the user's job email.
4. If the account exists but no usable saved password is available, use "Forgot password" and reset
   it to the shared password. Update the vault only after the reset succeeds, by piping the value to
   `python scripts/runtime/creds.py set --key <credential-key> --password-stdin`; never put the
   password on the command line.
5. Handle email verification / OTP by querying the mailbox narrowly (sender domain + recent timestamp) and
   reading only the link or OTP (`AGENTS.md` rule 2).
6. **PASSWORD_MODE = shared.** Use one password for **all** portal accounts (never the user's email
   password). For a new portal account, use `python scripts/runtime/creds.py new --key <portal-key>
   --username <job-email>`; it generates and stores a strong password without printing it. Do not
   reset a working saved portal password merely to make accounts match; update an account only
   through the recovery flow when its saved password is absent or explicitly rejected.
7. Record portal, URL, username, and date in the vault using the documented portal-row format.
   `python scripts/runtime/creds.py list` shows stored accounts without secrets. **Never print the password in
   chat, tool output, logs, or screenshots.** Do not request a browser snapshot while a password is
   visible in an input, and do not paste a password if the browser tool may echo field values; if
   secure entry cannot be guaranteed, ask the user to enter it manually. Restrict the file to the
   owner (chmod 700 on POSIX; owner-only ACL on Windows).
8. **Reuse the session:** keep the logged-in tab/session for other roles at the same company. If
   unreliable, rely on the persistent browser profile's cookies.

## Rules

- Clear the cookie/consent banner before touching the form (`AGENTS.md` rule 8).
- One account per portal.
- Visible browser from here onward.

## Outputs

- Authenticated session; `data/vault/credentials.txt` updated.
