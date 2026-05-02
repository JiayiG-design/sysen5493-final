"""Tiny local upload web app for ChartAccess image audits."""

from __future__ import annotations

import html
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .image_audit import audit_png


FORM_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChartAccess Image Upload</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f5ef; color: #172033; }
    main { max-width: 780px; margin: 48px auto; padding: 0 24px; }
    h1 { font-size: 34px; margin-bottom: 8px; }
    p { line-height: 1.55; color: #5a667d; }
    form, .result { background: white; border: 1px solid #d7dce5; padding: 24px; margin-top: 24px; }
    input[type=file] { display: block; margin: 16px 0; }
    button { background: #005ab5; color: white; border: 0; padding: 10px 16px; font-weight: 700; cursor: pointer; }
    .pass { color: #007a4d; font-weight: 700; }
    .fail { color: #b42318; font-weight: 700; }
    code { background: #eef2ff; padding: 2px 5px; }
    li { margin-bottom: 10px; }
  </style>
</head>
<body>
  <main>
    <h1>ChartAccess Image Upload</h1>
    <p>Upload a PNG chart export. The system estimates the background, prominent colors, text-like pixel density, and contrast risks. It does not OCR exact chart titles or axis labels.</p>
    <form action="/audit" method="post" enctype="multipart/form-data">
      <label for="chart">PNG chart image</label>
      <input id="chart" name="chart" type="file" accept="image/png" required>
      <button type="submit">Audit Chart Image</button>
    </form>
  </main>
</body>
</html>
"""


class ChartAccessHandler(BaseHTTPRequestHandler):
    """Serve the upload page and audit posted PNG files."""

    def do_GET(self) -> None:
        self._send_html(FORM_HTML)

    def do_POST(self) -> None:
        if self.path != "/audit":
            self.send_error(404)
            return

        try:
            image_bytes = self._extract_upload()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
                handle.write(image_bytes)
                image_path = Path(handle.name)
            findings, metadata = audit_png(image_path)
            image_path.unlink(missing_ok=True)
            self._send_html(render_result(findings, metadata))
        except Exception as exc:  # noqa: BLE001 - user-facing local tool
            self._send_html(render_error(str(exc)), status=400)

    def _extract_upload(self) -> bytes:
        content_type = self.headers.get("Content-Type", "")
        boundary_marker = "boundary="
        if boundary_marker not in content_type:
            raise ValueError("Upload must be multipart/form-data.")

        boundary = ("--" + content_type.split(boundary_marker, 1)[1].strip()).encode()
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        for part in body.split(boundary):
            if b'name="chart"' not in part:
                continue
            if b"\r\n\r\n" not in part:
                continue
            payload = part.split(b"\r\n\r\n", 1)[1]
            payload = payload.rsplit(b"\r\n", 1)[0]
            if not payload:
                raise ValueError("Uploaded file was empty.")
            return payload
        raise ValueError("No PNG file field named 'chart' was found.")

    def _send_html(self, content: str, status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def render_result(findings, metadata: dict[str, object]) -> str:
    summary = metadata["score"]
    status_class = "pass" if summary["overall_pass"] else "fail"
    status_text = "PASS" if summary["overall_pass"] else "NEEDS WORK"
    items = "\n".join(
        f"<li><span class=\"{'pass' if finding.passed else 'fail'}\">{'PASS' if finding.passed else 'FAIL'}</span> "
        f"{html.escape(finding.requirement)}<br><small>{html.escape(finding.detail)}</small></li>"
        for finding in findings
    )
    colors = ", ".join(f"<code>{html.escape(color)}</code>" for color in metadata["prominent_colors"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>ChartAccess Result</title>{_style()}</head>
<body><main>
<h1>ChartAccess Image Audit</h1>
<div class="result">
  <p class="{status_class}">Overall: {status_text} ({summary['passed']}/{summary['total']})</p>
  <p>Image size: {metadata['width']} x {metadata['height']} px</p>
  <p>Estimated background: <code>{html.escape(str(metadata['background']))}</code></p>
  <p>Prominent colors: {colors}</p>
  <ul>{items}</ul>
  <p><small>{html.escape(str(metadata['limitation']))}</small></p>
</div>
<p><a href="/">Audit another image</a></p>
</main></body></html>"""


def render_error(message: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>ChartAccess Error</title>{_style()}</head>
<body><main><h1>Upload Error</h1><div class="result"><p class="fail">{html.escape(message)}</p></div><p><a href="/">Try again</a></p></main></body></html>"""


def _style() -> str:
    return """<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f5ef; color: #172033; }
main { max-width: 780px; margin: 48px auto; padding: 0 24px; }
.result { background: white; border: 1px solid #d7dce5; padding: 24px; margin-top: 24px; }
.pass { color: #007a4d; font-weight: 700; }
.fail { color: #b42318; font-weight: 700; }
li { margin-bottom: 12px; }
code { background: #eef2ff; padding: 2px 5px; }
a { color: #005ab5; }
</style>"""


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ChartAccessHandler)
    print(f"ChartAccess upload app running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
