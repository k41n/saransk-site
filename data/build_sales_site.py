#!/usr/bin/env python3
"""Генератор внутреннего сайта для отдела продаж.

Пишет docs/index.html, docs/<slug>/compare.html, data/call_list_top10.csv и .md.
Не трогает docs/<slug>/index.html, call.md, img/, _preview_*.png.
Запуск: python3 data/build_sales_site.py
"""
import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"

# Данные из таблицы задания. Тексты про компании берём только отсюда и из call.md.
COMPANIES = [
    dict(slug="saranskkonserv", name="АО «Консервный завод \"Саранский\"»",
         sphere="консервы, молочная продукция",
         site="https://saranskkonserv.ru", site_href="https://saranskkonserv.ru",
         phone="8-800-250-41-13", extra=[("приёмная", "8 (8342) 24-71-41")],
         who="маркетинг или ген. директор Меркушкин А.Н.", note=""),
    dict(slug="sszhol", name="АО ХК «Саранскстройзаказчик»", sphere="строительный холдинг",
         site="http://sszhol.ru", site_href="http://sszhol.ru",
         phone="(8342) 47-73-01", extra=[], who="Ваганов М.А. (врио)", note=""),
    dict(slug="s-techno", name="ООО «Спецтехно-С»", sphere="запчасти для экскаваторов",
         site="http://с-техно.рф", site_href="http://xn----jtbyelhw.xn--p1ai",
         phone="+7 (8342) 23-25-43", extra=[], who="директор Самосудов А.А.", note=""),
    dict(slug="vcm-saransk", name="«Вторцветмет»",
         sphere="лом цветных металлов, алюминий в чушках",
         site="http://vcm-saransk.ru/", site_href="http://vcm-saransk.ru/",
         phone="+7 (8342) 24-10-57", extra=[], who="директор Ганаев Е.Н.",
         note="Уточнить форму: сайт называет ЗАО, справочник называет ООО"),
    dict(slug="ssk13", name="ООО «СантехСтройКомплект»", sphere="стальные отводы и фитинги",
         site="https://ssk13.ru", site_href="https://ssk13.ru",
         phone="+7 (8342) 77-72-72", extra=[], who="директор Чумаков С.А.", note=""),
    dict(slug="grimak", name="ООО «Гри-Мак»", sphere="рыба, солод, крафт-мешки",
         site="https://grimak.ru/", site_href="https://grimak.ru/",
         phone="+7 (8342) 32-59-22", extra=[], who="директор Корочков В.А.",
         note="Цены в демо могут быть устаревшими"),
    dict(slug="gk-konstanta", name="ООО «ГК Константа»", sphere="пищевые добавки",
         site="https://gk-konstanta.ru/ru/", site_href="https://gk-konstanta.ru/ru/",
         phone="8 800 250-92-91", extra=[], who="директор Арбузов А.А.", note=""),
    dict(slug="nano4", name="ООО «ТК «ЖНФ» (бренд NANO4)", sphere="антикоррозионные покрытия",
         site="https://nano4.ru/", site_href="https://nano4.ru/",
         phone="+7 (937) 673-49-50", extra=[], who="ген. директор Бояркин М.С.", note=""),
    dict(slug="mordovuzor", name="ООО «Мордовские узоры»",
         sphere="народные промыслы, швейная фабрика",
         site="https://mordovuzor.narod.ru/", site_href="https://mordovuzor.narod.ru/",
         phone="+7 (8342) 32-01-12", extra=[("второй номер", "(8342) 35-69-49")],
         who="руководителя уточнить",
         note="Телефон не проверен: на сайте подписан «факс». Второй номер (8342) 35-69-49"),
    dict(slug="rm-sfera", name="ООО «Сфера»", sphere="газовые баллоны",
         site="https://rm-sfera.ru/", site_href="https://rm-sfera.ru/",
         phone="+7 (8342) 25-34-42", extra=[], who="коммерческий директор Тарасова А.Е.",
         note="Звонить последней: прайс-лист говорит «отгрузка только по ранее заключённым договорам»"),
]


def tel(display):
    """Превращает номер в значение для href=tel:."""
    d = re.sub(r"\D", "", display)
    if len(d) == 10:
        d = "7" + d
    elif d.startswith("8") and len(d) == 11:
        d = "7" + d[1:]
    return "tel:+" + d


def parse_call(slug):
    text = (DOCS / slug / "call.md").read_text(encoding="utf-8")
    m = re.search(r"## Три проверенные проблемы.*?\n(.*?)\n## ", text, re.S)
    problems = re.findall(r"^\d\.\s+(.*)$", m.group(1), re.M)
    p = re.search(r"## Первая фраза оператора\s*\n+(.*?)\n", text, re.S)
    phrase = p.group(1).strip()
    assert len(problems) == 3, slug
    return problems, phrase


for i, c in enumerate(COMPANIES, 1):
    c["n"] = i
    c["problems"], c["phrase"] = parse_call(c["slug"])

esc = html.escape


def rich(s):
    """Экранирует текст и превращает `код` в <code>."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(s, quote=False))


def phone_links(c, cls="phone"):
    out = f'<a class="{cls}" href="{tel(c["phone"])}">{esc(c["phone"])}</a>'
    for label, num in c["extra"]:
        out += f' <span class="extra-phone">{esc(label)}: <a href="{tel(num)}">{esc(num)}</a></span>'
    return out


HEAD = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title}</title>
<link rel="stylesheet" href="{css}">
</head>
"""


def build_compare(c):
    idx = c["n"] - 1
    prev_c = COMPANIES[idx - 1] if idx > 0 else None
    next_c = COMPANIES[idx + 1] if idx < len(COMPANIES) - 1 else None
    prev_html = (f'<a class="btn" href="../{prev_c["slug"]}/compare.html" title="{esc(prev_c["name"])}">'
                 f'← Предыдущая (№{prev_c["n"]})</a>') if prev_c else '<span class="btn disabled">← Предыдущая</span>'
    next_html = (f'<a class="btn" href="../{next_c["slug"]}/compare.html" title="{esc(next_c["name"])}">'
                 f'Следующая (№{next_c["n"]}) →</a>') if next_c else '<span class="btn disabled">Следующая →</span>'
    note = f'<p class="note"><b>Пометка.</b> {esc(c["note"])}</p>' if c["note"] else ""
    probs = "\n".join(f"<li>{rich(p)}</li>" for p in c["problems"])
    body = f"""<body class="compare-page">
<header class="panel" id="panel">
  <div class="panel-top">
    <div class="panel-title">
      <span class="num">№{c["n"]} из {len(COMPANIES)}</span>
      <h1>{esc(c["name"])}</h1>
    </div>
    <div class="panel-phone">{phone_links(c, "phone big")}</div>
    <button type="button" class="btn" id="panel-toggle" aria-expanded="true" aria-controls="panel-body">Свернуть панель</button>
  </div>
  <div class="panel-body" id="panel-body">
    <div class="panel-cols">
      <div>
        <p><b>Сфера.</b> {esc(c["sphere"])}</p>
        <p><b>Кого спросить.</b> {esc(c["who"])}</p>
        {note}
      </div>
      <div>
        <p><b>Три проверенные проблемы текущего сайта</b></p>
        <ol>
{probs}
        </ol>
      </div>
      <div>
        <p><b>Первая фраза оператора</b></p>
        <p class="phrase">{esc(c["phrase"])}</p>
      </div>
    </div>
  </div>
</header>

<nav class="toolbar" aria-label="Навигация">
  <div class="nav-links">
    <a class="btn" href="../index.html">← Ко всему списку</a>
    {prev_html}
    {next_html}
  </div>
  <div class="seg" role="group" aria-label="Режим просмотра">
    <button type="button" data-mode="desktop" aria-pressed="true">Компьютер</button>
    <button type="button" data-mode="phone" aria-pressed="false">Телефон</button>
  </div>
  <div class="seg tabs" role="group" aria-label="Что показать">
    <button type="button" data-tab="old" aria-pressed="true">Было</button>
    <button type="button" data-tab="new" aria-pressed="false">Стало</button>
  </div>
</nav>

<main class="stage" id="stage" data-mode="desktop" data-tab="old">
  <section class="col col-old" aria-label="Было">
    <div class="col-head">
      <h2>Было</h2>
      <a class="btn" href="{esc(c["site_href"])}" target="_blank" rel="noopener">Открыть живой сайт ↗</a>
    </div>
    <div class="frame frame-old" id="frame-old" tabindex="0">
      <img id="old-img" src="_old_desktop.jpg" data-desktop="_old_desktop.jpg" data-phone="_old_mobile.jpg"
           alt="Снимок старого сайта: {esc(c["name"])}">
    </div>
  </section>
  <section class="col col-new" aria-label="Стало">
    <div class="col-head">
      <h2>Стало</h2>
      <a class="btn" href="index.html" target="_blank" rel="noopener">Открыть демо отдельно ↗</a>
    </div>
    <div class="frame frame-new" id="frame-new">
      <iframe id="demo" src="index.html" title="Демо нового сайта: {esc(c["name"])}"></iframe>
    </div>
  </section>
</main>
<script src="../_assets/compare.js"></script>
</body>
</html>
"""
    page = HEAD.format(title=f"Было / Стало: {esc(c['name'])} — внутренний сайт",
                       css="../_assets/compare.css") + body
    (DOCS / c["slug"] / "compare.html").write_text(page, encoding="utf-8")


def build_index():
    cards = []
    for c in COMPANIES:
        note = f'<p class="note">{esc(c["note"])}</p>' if c["note"] else ""
        cards.append(f"""    <article class="card" id="{c["slug"]}">
      <a class="thumb" href="{c["slug"]}/compare.html" tabindex="-1" aria-hidden="true">
        <img src="_assets/thumbs/{c["slug"]}.jpg" width="640" height="400" loading="lazy" alt="">
      </a>
      <div class="card-body">
        <p class="num">№{c["n"]}</p>
        <h2>{esc(c["name"])}</h2>
        <p class="sphere">{esc(c["sphere"])}</p>
        <p>{phone_links(c)}</p>
        <p><b>Кого спросить.</b> {esc(c["who"])}</p>
        {note}
        <div class="actions">
          <a class="btn primary" href="{c["slug"]}/compare.html">Было / Стало</a>
          <a class="btn" href="{c["slug"]}/index.html">Демо</a>
        </div>
      </div>
    </article>""")
    body = f"""<body class="index-page">
<header class="top">
  <h1>Звонки в 10 компаний Саранска</h1>
  <p class="sub">Внутренний список для отдела продаж. Компании стоят в порядке звонка.</p>
  <div class="memo">
    <h2>Памятка оператору</h2>
    <p>Отправляйте клиенту только ссылку на демо: <code>…/&lt;slug&gt;/</code>. Страницы «Было / Стало» и этот список внутренние, клиенту их не отправляйте. Не говорите «у вас плохой сайт». Говорите только о трёх проверенных пунктах из панели. Цену не называйте.</p>
  </div>
</header>
<main class="grid">
{chr(10).join(cards)}
</main>
</body>
</html>
"""
    page = HEAD.format(title="Звонки в 10 компаний Саранска — внутренний список",
                       css="_assets/compare.css") + body
    (DOCS / "index.html").write_text(page, encoding="utf-8")


def build_lists():
    cols = ["порядок", "компания", "сфера", "текущий_сайт", "телефон", "кого_спросить",
            "пометка", "демо", "сравнение", "проблема_1", "проблема_2", "проблема_3", "первая_фраза"]
    with open(DATA / "call_list_top10.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cols)
        for c in COMPANIES:
            phone = c["phone"] + "".join(f" ({l}: {n})" for l, n in c["extra"])
            w.writerow([c["n"], c["name"], c["sphere"], c["site"], phone, c["who"], c["note"],
                        f"docs/{c['slug']}/", f"docs/{c['slug']}/compare.html",
                        *c["problems"], c["phrase"]])
    lines = ["# Список для звонка: 10 компаний Саранска", "",
             "Порядок звонка сохранён. Клиенту отправляйте только ссылку на демо. "
             "Цену не называйте.", ""]
    for c in COMPANIES:
        phone = c["phone"] + "".join(f"; {l}: {n}" for l, n in c["extra"])
        lines += [f"## {c['n']}. {c['name']}", "",
                  f"- Сфера: {c['sphere']}",
                  f"- Текущий сайт: {c['site']}",
                  f"- Телефон: {phone}",
                  f"- Кого спросить: {c['who']}"]
        if c["note"]:
            lines.append(f"- Пометка: **{c['note']}**")
        lines += [f"- Демо: `docs/{c['slug']}/`",
                  f"- Сравнение: `docs/{c['slug']}/compare.html`",
                  "- Три проверенные проблемы:"]
        lines += [f"  {i}. {p}" for i, p in enumerate(c["problems"], 1)]
        lines += [f"- Первая фраза: {c['phrase']}", ""]
    (DATA / "call_list_top10.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    for c in COMPANIES:
        build_compare(c)
    build_index()
    build_lists()
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print("ok")
