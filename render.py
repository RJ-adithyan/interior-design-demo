#!/usr/bin/env python3
"""Render this demonstration (five pages plus one page per project) with Python's standard library only."""
import argparse
import html
import hashlib
import json
import re
import struct
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parent
ROUTES = {"home": "index.html", "work": "work.html", "studio": "studio.html",
          "process": "process.html", "contact": "contact.html"}


def esc(value):
    return html.escape(str(value), quote=True)


def local_asset(value):
    path = ROOT / value
    if not value.startswith("assets/") or not path.resolve().is_relative_to((ROOT / "assets").resolve()):
        raise ValueError(f"Asset must stay inside assets/: {value}")
    if not path.is_file():
        raise ValueError(f"Missing asset: {value}")
    return path


@lru_cache(maxsize=None)
def dimensions(value):
    """Read JPEG frame dimensions without an imaging dependency."""
    data = local_asset(value).read_bytes()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"Not a JPEG: {value}")
    offset = 2
    while offset < len(data):
        if data[offset] != 255:
            raise ValueError(f"Invalid JPEG marker: {value}")
        while offset < len(data) and data[offset] == 255:
            offset += 1
        marker = data[offset]
        offset += 1
        if marker in (0xD9, 0xDA):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        size = struct.unpack_from(">H", data, offset)[0]
        if size < 2 or offset + size > len(data):
            raise ValueError(f"Invalid JPEG segment: {value}")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack_from(">HH", data, offset + 3)
            return width, height
        offset += size
    raise ValueError(f"No JPEG frame found: {value}")


def image(src, alt, small=None, position="50% 50%", eager=False, sizes="(max-width: 767px) calc(100vw - 44px), 50vw"):
    width, height = dimensions(src)
    if not re.fullmatch(r"\d{1,3}% \d{1,3}%", position):
        raise ValueError("Image position must contain two percentage values")
    srcset = ""
    if small:
        small_width, _ = dimensions(small)
        srcset = f' srcset="{esc(small)} {small_width}w, {esc(src)} {width}w" sizes="{esc(sizes)}"'
    priority = ' fetchpriority="high"' if eager else ''
    return (f'<img src="{esc(src)}"{srcset} width="{width}" height="{height}" '
            f'alt="{esc(alt)}" loading="{"eager" if eager else "lazy"}" decoding="async"'
            f'{priority} style="object-position:{esc(position)}">')


def project_card(project):
    media = image(project["image"], project["alt"], project.get("small_image"), project.get("position", "50% 50%"))
    return (f'<a class="project-card" data-work-project data-category="{esc(project["category"])}" href="{esc(project["id"])}.html">'
            f'<div class="media-frame" data-reveal="image">{media}</div>'
            f'<div class="project-card__caption"><h3>{esc(project["name"])}</h3>'
            f'<span>{esc(project["eyebrow"])} <span aria-hidden="true">↗</span></span></div></a>')


def partial(name, values):
    return Template((ROOT / "templates" / name).read_text()).substitute(values)


def context(data, page):
    values = {key: esc(value) for key, value in data["site"].items()}
    number = data["site"]["contact_whatsapp_number"]
    values["contact_whatsapp_url"] = esc("https://wa.me/" + number + "?text=" + quote(data["site"]["contact_whatsapp_message"], safe=""))
    values["contact_phone_display"] = esc(f"+91 {number[2:7]} {number[7:]}" if number.startswith("91") and len(number) == 12 else "+" + number)
    values["closing_cta_href"] = values["contact_whatsapp_url"] if page == "contact" else "contact.html"
    values["closing_cta_label"] = "WhatsApp RJ" if page == "contact" else "Start a conversation"
    values.update({f"nav_{key}_current": ' aria-current="page"' if key == page else ''
                   for key in ("work", "studio", "process", "contact")})
    return values


def shell(title, description, body_class, header, body, footer):
    style_version = hashlib.sha256((ROOT / "styles.css").read_bytes()).hexdigest()[:10]
    script_version = hashlib.sha256((ROOT / "site.js").read_bytes()).hexdigest()[:10]
    hero_preload = ('<link rel="preload" as="image" href="assets/hero-woven-laptop.jpg" media="(min-width:768px)">\n'
                    '<link rel="preload" as="image" href="assets/hero-woven-mobile.jpg" media="(max-width:767px)">') if body_class == "page-home" else ''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}">
<meta name="theme-color" content="#1b1613">
<title>{esc(title)}</title>
{hero_preload}
<link rel="preload" href="assets/fonts/prata.ttf" as="font" type="font/ttf" crossorigin>
<link rel="preload" href="assets/fonts/manrope.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="styles.css?v={style_version}">
<script src="site.js?v={script_version}" defer></script>
</head>
<body class="{esc(body_class)}">
{header}
<main id="main-content">{body}</main>
{footer}
</body>
</html>
'''


def load_content():
    data = json.loads((ROOT / "content.json").read_text())
    ids = [project["id"] for project in data["projects"]]
    # Templates place projects by position ($project_1_image ... $project_4_image), so four is the floor.
    if len(ids) < 4 or len(set(ids)) != len(ids) or not all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) for key in ids):
        raise ValueError("Provide at least four uniquely named lowercase project IDs")
    if not re.fullmatch(r"[1-9][0-9]{7,14}", data["site"]["contact_whatsapp_number"]):
        raise ValueError("WhatsApp number must contain 8–15 digits including country code, without a leading zero")
    for project in data["projects"]:
        for field in ("source_url", "detail_source_url"):
            if field in project and urlsplit(project[field]).scheme != "https":
                raise ValueError(f"Photo credit {field} must use HTTPS")
        dimensions(project["image"])
    return data


def render(data, selected=None):
    pages = []
    for key, route in ROUTES.items():
        if selected and selected != key:
            continue
        values = context(data, key)
        info = data["home"] if key == "home" else data["pages"][key]
        values.update({name: esc(value) for name, value in info.items() if not isinstance(value, (dict, list))})
        values["project_cards"] = "\n".join(project_card(p) for p in data["projects"])
        values["showcase_cards"] = "\n".join(
            f'<a class="showcase-card" href="{esc(p["id"])}.html" data-showcase-card>'
            f'<div class="media-frame">{image(p["image"], p["alt"], p.get("small_image"), p.get("position", "50% 50%"))}</div>'
            f'<div class="showcase-caption"><h3>{esc(p["name"])}</h3><span>{esc(p["eyebrow"])}</span></div></a>'
            for p in data["projects"])
        values["textile_image"] = image("assets/textile.jpg", "Fine red woven fabric texture", "assets/textile-800.jpg")
        categories = list(dict.fromkeys(p["category"] for p in data["projects"]))
        values["category_filters"] = "\n".join(
            f'<a href="work.html?category={quote(c)}#projects" data-work-category-filter="{esc(c)}">{esc(c)}</a>' for c in categories)
        for slot, project in enumerate(data["projects"], 1):
            values[f"project_{slot}_href"] = esc(project["id"] + ".html")
            values[f"project_{slot}_name"] = esc(project["name"])
            values[f"project_{slot}_category"] = esc(project["category"])
            values[f"project_{slot}_image"] = image(project["image"], project["alt"], project.get("small_image"), project.get("position", "50% 50%"))
            values[f"project_{slot}_detail_image"] = image(project["detail_image"], project["detail_caption"], project.get("detail_small_image"))
        body = partial(f'{key}.html', values)
        text = shell(f'{info["title"]} — {data["site"]["studio_name"]}', data["site"]["site_description"],
                     "page-home" if key == "home" else f"page-interior page-{key}",
                     partial("header.html", values), body, partial("footer.html", values))
        (ROOT / route).write_text(text)
        pages.append(route)
    for number, project in enumerate(data["projects"]):
        if selected and selected != project["id"]:
            continue
        values = context(data, "work")
        values.update({key: esc(value) for key, value in project.items() if not isinstance(value, (dict, list))})
        values["project_number"] = f"0{number + 1}"
        values["detail_source_url"] = esc(project.get("detail_source_url", project["source_url"]))
        values["project_hero"] = image(project["image"], project["alt"], project.get("small_image"), project.get("position", "50% 50%"), True, "100vw")
        values["project_detail_image"] = image(project["detail_image"], project["detail_caption"], project.get("detail_small_image"))
        next_project = data["projects"][(number + 1) % len(data["projects"])]
        values.update(next_name=esc(next_project["name"]), next_href=esc(next_project["id"] + ".html"),
                      next_image=image(next_project["image"], next_project["alt"], next_project.get("small_image")))
        body = partial("project.html", values)
        text = shell(f'{project["name"]} — {data["site"]["studio_name"]}', project["intro"], "page-interior page-project",
                     partial("header.html", values), body, partial("footer.html", values))
        route = project["id"] + ".html"
        (ROOT / route).write_text(text)
        pages.append(route)
    if not pages:
        raise ValueError(f"Unknown page: {selected}")
    return pages


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images = set(), [], []
        self.h1_count = 0
        self.duplicate_ids = []

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if tag == "h1":
            self.h1_count += 1
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.duplicate_ids.append(attrs["id"])
            self.ids.add(attrs["id"])
        if tag in ("a", "link", "script"):
            self.links.append(attrs.get("href", attrs.get("src", "")))
        if tag == "video":
            self.links.extend(attrs[key] for key in ("src", "poster", "data-src", "data-desktop-src", "data-mobile-src") if key in attrs)
        if tag == "source":
            if "src" in attrs:
                self.links.append(attrs["src"])
            for candidate in attrs.get("srcset", "").split(","):
                if candidate.strip():
                    self.links.append(candidate.strip().split()[0])
        if tag == "img":
            self.images.append(attrs)
            self.links.append(attrs.get("src", ""))
            for candidate in attrs.get("srcset", "").split(","):
                if candidate.strip():
                    self.links.append(candidate.strip().split()[0])


def check(data):
    expected = list(ROUTES.values()) + [p["id"] + ".html" for p in data["projects"]]
    parsed = {}
    failures = []
    for filename in expected:
        path = ROOT / filename
        if not path.exists():
            failures.append(f"Missing page: {filename}")
            continue
        page = PageLinks()
        page.feed(path.read_text())
        parsed[filename] = page
        if page.h1_count != 1 or page.duplicate_ids:
            failures.append(f"Heading/ID structure problem in {filename}")
        for attrs in page.images:
            if "alt" not in attrs or not attrs.get("width") or not attrs.get("height"):
                failures.append(f"Image lacks alt/dimensions in {filename}")
    for filename, page in parsed.items():
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target = unquote(url.path) or filename
            if not (ROOT / target).is_file():
                failures.append(f"Missing local reference in {filename}: {href}")
            if url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
                failures.append(f"Missing anchor in {filename}: {href}")
    # A substituted client name must remain text, never executable HTML.
    assert esc('<img src=x onerror="bad()">') == '&lt;img src=x onerror=&quot;bad()&quot;&gt;'
    assert dimensions(data["projects"][0]["image"])[0] > 0
    if "contact.html" in parsed:
        contact_links = parsed["contact.html"].links
        whatsapp = [urlsplit(href) for href in contact_links if urlsplit(href).netloc == "wa.me"]
        if not whatsapp or any(link.path != "/" + data["site"]["contact_whatsapp_number"] or parse_qs(link.query).get("text") != [data["site"]["contact_whatsapp_message"]] for link in whatsapp):
            failures.append("WhatsApp destination or prefilled text does not match content.json")
        if any(href.startswith("mailto:") for href in contact_links):
            failures.append("Contact still contains an email action")
    print(f"Pages: {len(parsed)}/{len(expected)}; links/images/structure/escaping/WhatsApp: {'FAIL' if failures else 'PASS'}")
    for failure in failures:
        print(failure)
    return not failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", help="Render one page during development, e.g. home")
    parser.add_argument("--check", action="store_true", help="Check the complete generated site without rewriting it")
    args = parser.parse_args()
    content = load_content()
    if args.check:
        raise SystemExit(0 if check(content) else 1)
    print("Rendered: " + ", ".join(render(content, args.page)))
