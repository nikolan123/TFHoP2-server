import csv
import json
import re
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


ORIGIN_HOST = "www.gameslice.com"
COMMENTS_PATH = "/p2/index.php5"
DNS_URL = f"https://dns.google/resolve?name={ORIGIN_HOST}&type=A"
CSV_PATH = Path(__file__).resolve().parent / "comments.csv"


class CommentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.comments = []
        self.current = None
        self.div_depth = 0
        self.paragraph_class = None
        self.paragraph_text = []
        self.in_strong = False
        self.strong_text = []

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "div":
            if self.current is not None:
                self.div_depth += 1
            elif attributes.get("class", "").strip() == "comment":
                self.current = {"paragraphs": [], "name": "", "posttime": ""}
                self.div_depth = 1
            return

        if self.current is None:
            return
        if tag == "p":
            self.paragraph_class = attributes.get("class", "")
            self.paragraph_text = []
        elif tag == "strong" and self.paragraph_class == "posttime":
            self.in_strong = True
            self.strong_text = []
        elif tag == "br" and self.paragraph_class is not None:
            self.paragraph_text.append("\n")

    def handle_endtag(self, tag):
        if self.current is None:
            return
        if tag == "strong" and self.in_strong:
            self.current["name"] = "".join(self.strong_text).strip()
            self.in_strong = False
        elif tag == "p" and self.paragraph_class is not None:
            text = "".join(self.paragraph_text).strip()
            if self.paragraph_class == "posttime":
                self.current["posttime"] = text
            elif text:
                self.current["paragraphs"].append(text)
            self.paragraph_class = None
            self.paragraph_text = []
        elif tag == "div":
            self.div_depth -= 1
            if self.div_depth == 0:
                self.comments.append(self.current)
                self.current = None

    def handle_data(self, data):
        if self.current is None or self.paragraph_class is None:
            return
        self.paragraph_text.append(data)
        if self.in_strong:
            self.strong_text.append(data)


def resolve_origin():
    request = Request(DNS_URL, headers={"User-Agent": "Portal-2-Final-Hours-Preservation/1.0"})
    with urlopen(request, timeout=30) as response:
        answer = json.load(response)
    addresses = [entry["data"] for entry in answer.get("Answer", []) if entry.get("type") == 1]
    if not addresses:
        raise RuntimeError(f"Public DNS returned no address for {ORIGIN_HOST}")
    return addresses[0]


def download_page(page, origin_ip):
    query = "" if page == 1 else f"?page={page}"
    url = f"http://{origin_ip}{COMMENTS_PATH}{query}"
    request = Request(
        url,
        headers={
            "Host": ORIGIN_HOST,
            "User-Agent": "Portal-2-Final-Hours-Preservation/1.0",
        },
    )
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as error:
            last_error = error
            if attempt < 2:
                time.sleep(attempt + 1)
    raise RuntimeError(f"Could not download page {page}: {last_error}")


def parse_page(html, page):
    parser = CommentParser()
    parser.feed(html)
    rows = []
    for position, entry in enumerate(parser.comments, start=1):
        posttime = re.sub(r"\s+", " ", entry["posttime"]).strip()
        posttime_match = re.search(r"\bposted at (.+)$", posttime, re.IGNORECASE)
        if posttime_match is None:
            raise ValueError(
                f"Could not parse timestamp on page {page}, comment {position}: {posttime!r}"
            )
        timestamp = posttime_match.group(1).strip()
        try:
            created_at = datetime.strptime(
                timestamp, "%I:%M %p on %B %d, %Y"
            ).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as error:
            raise ValueError(
                f"Could not parse timestamp on page {page}, comment {position}: {timestamp!r}"
            ) from error
        rows.append(
            {
                "source_key": f"gameslice:p{page}:c{position}",
                "source_page": page,
                "source_position": position,
                "name": entry["name"],
                "comment": "\n\n".join(entry["paragraphs"]),
                "created_at": created_at,
            }
        )
    return rows


def export_comments():
    origin_ip = resolve_origin()
    print(f"Resolved the original {ORIGIN_HOST} server to {origin_ip}.")
    first_html = download_page(1, origin_ip)
    page_numbers = [int(number) for number in re.findall(r"[?&]page=(\d+)", first_html)]
    total_pages = max(page_numbers, default=1)
    rows = parse_page(first_html, 1)

    for page in range(2, total_pages + 1):
        rows.extend(parse_page(download_page(page, origin_ip), page))
        if page % 10 == 0 or page == total_pages:
            print(f"Downloaded {page}/{total_pages} pages ({len(rows)} comments)")
        time.sleep(0.05)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = CSV_PATH.with_suffix(".csv.tmp")
    with temporary_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "source_key",
                "source_page",
                "source_position",
                "name",
                "comment",
                "created_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    temporary_path.replace(CSV_PATH)
    print(f"Saved {len(rows)} comments to {CSV_PATH}.")


if __name__ == "__main__":
    export_comments()
