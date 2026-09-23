import csv
from http.server import BaseHTTPRequestHandler, HTTPServer
from html import escape
from pathlib import Path
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = 8000
CSV_FILE = Path(__file__).with_name("inquiries.csv")


STYLE = """
<style>
  :root {
    color-scheme: light;
    --ink: #18313b;
    --muted: #60747a;
    --paper: #fffdf7;
    --line: #d9e3df;
    --accent: #df684a;
    --accent-dark: #b94d34;
    --wash: #e9f1ed;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    color: var(--ink);
    background: linear-gradient(135deg, #f7eee3 0%, #e9f1ed 100%);
    font-family: Georgia, "Yu Mincho", "Hiragino Mincho ProN", serif;
  }
  main { width: min(100% - 32px, 720px); margin: 48px auto; }
  .form-shell {
    overflow: hidden;
    background: var(--paper);
    border: 1px solid rgba(24, 49, 59, .12);
    box-shadow: 0 18px 50px rgba(24, 49, 59, .12);
  }
  header { padding: 36px 40px 28px; background: var(--wash); }
  .eyebrow {
    margin: 0 0 10px;
    color: var(--accent-dark);
    font: 700 12px/1.2 Arial, sans-serif;
    letter-spacing: .16em;
  }
  h1 { margin: 0; font-size: clamp(30px, 6vw, 48px); font-weight: 500; }
  header p { max-width: 520px; margin: 16px 0 0; color: var(--muted); line-height: 1.8; }
  form, .success { padding: 34px 40px 40px; }
  .field { margin-bottom: 22px; }
  label { display: block; margin-bottom: 8px; font-weight: 700; }
  .required { color: var(--accent-dark); font: 700 12px Arial, sans-serif; }
  input, select, textarea {
    width: 100%;
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 13px 14px;
    color: var(--ink);
    background: #fff;
    font: 16px/1.5 Arial, sans-serif;
  }
  input:focus, select:focus, textarea:focus { outline: 3px solid rgba(223, 104, 74, .2); border-color: var(--accent); }
  textarea { min-height: 170px; resize: vertical; }
  .hint { margin: 7px 0 0; color: var(--muted); font: 13px/1.5 Arial, sans-serif; }
  .error {
    margin: 0 0 24px;
    padding: 12px 14px;
    color: #8d2f20;
    border-left: 4px solid var(--accent);
    background: #fff0eb;
    font: 14px/1.6 Arial, sans-serif;
  }
  button {
    width: 100%;
    border: 0;
    border-radius: 2px;
    padding: 15px 20px;
    color: #fff;
    background: var(--accent);
    cursor: pointer;
    font: 700 16px Arial, sans-serif;
  }
  button:hover { background: var(--accent-dark); }
  .success h2 { margin-top: 0; font-size: 30px; font-weight: 500; }
  .success p { color: var(--muted); line-height: 1.8; }
  .back { display: inline-block; margin-top: 12px; color: var(--accent-dark); font: 700 14px Arial, sans-serif; }
  @media (max-width: 560px) {
    main { width: min(100% - 20px, 720px); margin: 20px auto; }
    header, form, .success { padding-left: 22px; padding-right: 22px; }
  }
</style>
"""


def page(content):
    return f"<!doctype html><html lang='ja'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>お問い合わせフォーム</title>{STYLE}</head><body><main><section class='form-shell'>{content}</section></main></body></html>"


def form_page(error="", values=None):
    values = values or {}
    error_html = f"<p class='error'>{escape(error)}</p>" if error else ""
    return page(f"""
<header>
  <p class='eyebrow'>CONTACT</p>
  <h1>お問い合わせ</h1>
  <p>ご質問やご相談をお聞かせください。内容を確認のうえ、担当者よりご連絡します。</p>
</header>
<form method='post' action='/'>
  {error_html}
  <div class='field'>
    <label for='name'>お名前 <span class='required'>必須</span></label>
    <input id='name' name='name' type='text' value='{escape(values.get('name', ''))}' maxlength='80' required>
  </div>
  <div class='field'>
    <label for='email'>メールアドレス <span class='required'>必須</span></label>
    <input id='email' name='email' type='email' value='{escape(values.get('email', ''))}' maxlength='254' required>
  </div>
  <div class='field'>
    <label for='category'>お問い合わせ種別 <span class='required'>必須</span></label>
    <select id='category' name='category' required>
      <option value=''>選択してください</option>
      {''.join(f"<option {'selected' if values.get('category') == category else ''}>{category}</option>" for category in ('サービスについて', 'ご意見・ご要望', 'その他'))}
    </select>
  </div>
  <div class='field'>
    <label for='message'>お問い合わせ内容 <span class='required'>必須</span></label>
    <textarea id='message' name='message' maxlength='2000' required>{escape(values.get('message', ''))}</textarea>
    <p class='hint'>2,000文字以内で入力してください。</p>
  </div>
  <button type='submit'>送信する</button>
</form>
""")


class ContactFormHandler(BaseHTTPRequestHandler):
    def send_html(self, body, status=200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        self.send_html(form_page())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        values = {key: data.get(key, [""])[0].strip() for key in ("name", "email", "category", "message")}
        error = validate(values)
        if error:
            self.send_html(form_page(error, values), 400)
            return
        try:
          save_inquiry(values)
        except OSError:
          self.send_html(form_page("お問い合わせを保存できませんでした。時間をおいて再度お試しください。", values), 500)
          return
        self.send_html(page("""
<header>
  <p class='eyebrow'>THANK YOU</p>
  <h1>送信しました</h1>
  <p>お問い合わせありがとうございます。内容を確認のうえ、メールアドレス宛にご連絡します。</p>
</header>
<div class='success'>
  <h2>受付完了</h2>
  <p>お問い合わせ内容を受け付け、CSVファイルに保存しました。</p>
  <a class='back' href='/'>フォームに戻る</a>
</div>
"""))

    def log_message(self, format, *args):
        return



def save_inquiry(values):
    fieldnames = ("name", "email", "category", "message")
    file_exists = CSV_FILE.exists()
    with CSV_FILE.open("a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if not file_exists or CSV_FILE.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({field: values[field] for field in fieldnames})


def validate(values):
    if any(not values[field] for field in ("name", "email", "category", "message")):
        return "必須項目をすべて入力してください。"
    if "@" not in values["email"] or "." not in values["email"].split("@")[-1]:
        return "メールアドレスの形式を確認してください。"
    if len(values["message"]) > 2000:
        return "お問い合わせ内容は2,000文字以内で入力してください。"
    return ""


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), ContactFormHandler)
    print(f"お問い合わせフォームを http://{HOST}:{PORT}/ で起動しました。終了するには Ctrl+C を押してください。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを終了しました。")
    finally:
        server.server_close()
