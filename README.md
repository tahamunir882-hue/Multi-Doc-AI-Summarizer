# Universal AI: Multilingual Document Intelligence

## Run (Windows)
    python -m pip install -r requirements.txt
    python -m streamlit run app.py
Then open http://localhost:8501 . No API key and no .env file are needed (offline mode is the default).

## Optional
- Scanned PDFs / images: install Tesseract OCR (with Urdu, Hindi language packs).
- Extra AI pages (study/business/contract modes, reports, deep research, podcast, mind map, agents, contradictions):
  install Ollama (ollama.com), run `ollama pull qwen2.5:7b`, then create a file named `.env` containing
  `LLM_PROVIDER=ollama` (or `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...`; then also `pip install anthropic`).
- Audio/video upload: `pip install faster-whisper`.  Better search: `pip install sentence-transformers`.
- Urdu PDF export: put a font such as NotoNastaliqUrdu-Regular.ttf in a `fonts/` folder.

## Before publishing on a website (put these in `.env` or your host's secrets)
    SMTP_HOST=smtp.gmail.com  SMTP_PORT=587  SMTP_USER=you@gmail.com  SMTP_PASS=app-password   # forgot-password emails
    DEMO_PLANS=0                       # users can no longer give themselves a paid plan
    ADMIN_EMAIL=you@gmail.com          # your account can activate plans on the Plans page
    PAYMENT_LINK_PRO=https://...  PAYMENT_LINK_BUSINESS=https://...   # e.g. Stripe Payment Links ($3 and $7)
Keep the `data/` folder on persistent storage (it holds users, documents and the encryption key). Use HTTPS.
