"""Build submission_sokcheapanha_5.7.pdf from submission.md.  Run:  python3 build_pdf.py"""
import html, re, subprocess, pathlib

HERE = pathlib.Path(__file__).resolve().parent
md = (HERE / "submission.md").read_text()


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return s


out, table, code, in_code = [], [], [], False

def flush_table():
    if not table:
        return
    rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table if not re.match(r"^\|[-| ]+\|$", r.strip())]
    out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr>")
    for r in rows[1:]:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out.append("</table>"); table.clear()

for line in md.splitlines():
    if line.startswith("```"):
        if in_code:
            out.append("<pre>" + html.escape("\n".join(code)) + "</pre>"); code.clear()
        in_code = not in_code; continue
    if in_code:
        code.append(line); continue
    if line.startswith("|"):
        table.append(line); continue
    flush_table()
    if m := re.match(r"!\[(.*?)\]\((.*?)\)", line):
        out.append(f'<figure><img src="{m.group(2)}" alt="{html.escape(m.group(1))}"></figure>')
    elif m := re.match(r"(#+) (.*)", line):
        n = len(m.group(1)); out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
    elif line.strip():
        out.append(f"<p>{inline(line)}</p>")
flush_table()

page = """<!doctype html><meta charset="utf-8"><title>Task 5.7 submission</title><style>
@page{size:A4;margin:14mm 13mm}
body{font:10pt/1.45 system-ui,'Segoe UI',sans-serif;color:#1e1e1e}
h1{font-size:18pt;margin:0 0 6pt} h2{font-size:13.5pt;margin:14pt 0 6pt;border-bottom:1.5px solid #ccc;padding-bottom:3pt}
h3{font-size:11pt;margin:10pt 0 4pt} h2,h3{break-after:avoid}
code{font:8.6pt ui-monospace,Consolas,monospace;background:#f1f3f5;padding:0 3px;border-radius:3px}
pre{font:8pt/1.35 ui-monospace,Consolas,monospace;background:#f6f8fa;border:1px solid #ddd;padding:6pt;white-space:pre-wrap;break-inside:avoid}
table{border-collapse:collapse;width:100%;margin:6pt 0;font-size:8.8pt} th,td{border:1px solid #999;padding:3pt 5pt;text-align:left;vertical-align:top}
th{background:#f1f3f5} tr{break-inside:avoid}
figure{margin:6pt 0;break-inside:avoid} img{max-width:100%;border:1px solid #ddd}
a{color:#1971c2}
</style>
""" + "\n".join(out)
(HERE / "submission.html").write_text(page)
pdf = HERE / "submission_sokcheapanha_5.7.pdf"
subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", (HERE / "submission.html").as_uri()], check=True, stderr=subprocess.DEVNULL)
print("wrote", pdf, pdf.stat().st_size // 1024, "KB")
