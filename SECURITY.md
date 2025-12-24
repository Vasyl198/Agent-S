Security and API keys

- Never hardcode API keys or secrets in source files (e.g., `setup.py`).
- Use environment variables or a `.env` file (and add `.env` to `.gitignore`).
- For local development, copy `.env.example` to `.env` and populate keys.
- Rotate keys immediately if a secret was accidentally committed.
- Restrict model and API keys with least privilege and network/IP restrictions when possible.

If you need, I can create/update `.gitignore` to include `.env` and help scan the repo for other leaked secrets.
