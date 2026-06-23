"""Minimal FastAPI app for the budget web page."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="가계부 웹")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Return the local budget web home page."""
    return """
    <!doctype html>
    <html lang="ko">
      <head>
        <meta charset="utf-8">
        <title>가계부 웹</title>
      </head>
      <body>
        <main>
          <h1>가계부 웹</h1>
        </main>
      </body>
    </html>
    """
