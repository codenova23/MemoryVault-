# Memory Vault

Memory Vault is a local-first photo memory app built with Streamlit and SQLite. Upload photos, group them into memory chapters, search by people/places/tags, favorite moments, generate a story locally, and leave date-locked notes for your future self.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

The SQLite database is created at `data/memory_vault.sqlite3`. Override the path with `MEMORY_VAULT_DB` if needed. Five demo memories are seeded on first run; remove or restore them from **Privacy**.

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create an app from the repository and select `app.py` as the entrypoint.
3. Add a password under the app's **Settings → Secrets**:

	```toml
	APP_PASSWORD = "choose-a-private-password"
	```

4. Deploy. Community Cloud installs the packages in `requirements.txt` automatically.

The SQLite file is local to the app process. Streamlit Community Cloud may reset local files after a restart or redeploy, so this MVP is suitable for a hackathon/demo but not yet a durable multi-user photo service. Use a managed database and object storage before relying on it for irreplaceable uploads.

## Privacy and AI behavior

- The optional `APP_PASSWORD` secret adds a single shared password gate; it is not per-user authentication.
- Photos are resized and compressed before their bytes are stored in SQLite. Sample cover photography is loaded from Unsplash.
- Story generation and search matching run in Python without an external AI API.
- The app does not encrypt the database or provide remote backups. Restrict deployment access and keep backups for personal data.
