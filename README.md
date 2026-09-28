# ComicCraft — AI Comic Story Creator (Gemini + Stable Diffusion)

A FastAPI web app that turns a short story prompt into a full, illustrated
comic strip and lets you download it as a PDF.

- **Story outline** → Gemini Flash (`generate_outline`)
- **Narration & dialogue** → Gemini Pro (`generate_story`)
- **Panel illustrations** → Stable Diffusion via Hugging Face Diffusers
  (`generate_image`), with an automatic lightweight placeholder-image
  fallback if Diffusers/torch/a GPU aren't available
- **PDF export** → FPDF (`save_pdf`)

## 1. Project structure

```
comiccraft/
├── app/
│   ├── main.py            FastAPI app + static mount
│   ├── routes.py          All routes (pages + JSON API)
│   ├── config.py          Env vars, paths, model names
│   ├── gemini_flash.py    generate_outline()
│   ├── gemini_pro.py      generate_story()
│   ├── image_generator.py generate_image() (SD + placeholder fallback)
│   ├── layout_builder.py  build_comic_layout()
│   └── exporters.py       save_pdf()
├── templates/
│   ├── index.html
│   ├── comic_preview.html
│   └── export_success.html
├── static/
│   ├── panels/            Generated panel images land here
│   ├── exports/           Generated PDFs land here
│   └── fonts/             Optional: drop DejaVuSans.ttf here for full
│                          Unicode support in the PDF
├── .env.example
├── requirements.txt
└── README.md
```

## 2. Setup

```bash
cd comiccraft

python -m venv comiccraft-env
# Windows:
comiccraft-env\Scripts\activate
# macOS/Linux:
source comiccraft-env/bin/activate

pip install -r requirements.txt
```

> The last five packages in `requirements.txt` (`diffusers`, `transformers`,
> `accelerate`, `torch`) are only needed for **real** Stable Diffusion image
> generation. If you skip them (or they fail to install/load — e.g. no
> GPU, no internet to download the model), the app still runs fine and
> automatically draws lightweight placeholder panel images instead, so you
> can test the whole pipeline (outline → story → layout → PDF) immediately.

Copy the env template and add your key:

```bash
cp .env.example .env
```

Edit `.env`:

```
GEMINI_API_KEY=your_real_gemini_api_key
```

Get a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).
Without a key set, `generate_outline`/`generate_story` fall back to a
deterministic local story generator, so the app is still fully runnable
for testing/demoing the UI and pipeline without any API keys at all.

## 3. Run

```bash
uvicorn app.main:app --reload
```

- App: <http://127.0.0.1:8000>
- Interactive API docs: <http://127.0.0.1:8000/docs>

## 4. Routes

| Route                      | Method | Purpose                                         |
|-----------------------------|--------|--------------------------------------------------|
| `/`                          | GET    | Homepage — story input form                     |
| `/generate`                  | POST   | Form submission → full pipeline → comic preview |
| `/generate-comic/json`       | POST   | Same pipeline, JSON in/out, for API clients      |
| `/export-success`            | GET    | Confirms export, links to the generated PDF      |
| `/test-image`                | GET    | Generates one image from a prompt, for testing   |

Example JSON request:

```bash
curl -X POST http://127.0.0.1:8000/generate-comic/json \
  -H "Content-Type: application/json" \
  -d '{
        "prompt": "A brave fox explores an enchanted forest.",
        "character_name": "Finn",
        "setting": "forest",
        "tone": "dramatic",
        "style": "anime"
      }'
```

## 5. Notes on the fallbacks (so nothing ever crashes)

- **No `GEMINI_API_KEY`** → `generate_outline`/`generate_story` return a
  deterministic 5-panel outline/story instead of calling the API.
- **No `diffusers`/`torch`, or model load fails** → `generate_image` draws
  a simple labeled placeholder panel with Pillow instead of calling
  Stable Diffusion. Force this mode any time by setting
  `COMICCRAFT_FORCE_PLACEHOLDER_IMAGES=true` in `.env`.
- **No `static/fonts/DejaVuSans.ttf`** → PDF export uses FPDF's built-in
  Helvetica font (with non-Latin-1 characters safely replaced) instead of
  crashing on a missing font file.

To enable real image generation, install the optional dependencies and
make sure you have enough RAM/VRAM (a GPU is strongly recommended —
Stable Diffusion is slow on CPU):

```bash
pip install diffusers transformers accelerate torch
```