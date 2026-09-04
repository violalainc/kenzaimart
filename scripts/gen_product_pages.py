#!/usr/bin/env python3
"""_data/products.csv から 1商品1ファイルの _products/<id>.md を生成する。

CSV 列: id, major, minor, model, name, image, price, blurb, price_fmt,
        description, catalog_pdfs
catalog_pdfs は [{"label": "...", "url": "..."}] 形式の JSON 文字列（空なら "[]"）。

各 md ファイルの front matter に商品データを埋め込むので、レイアウト側から
CSV を毎回読みに行く必要がなくなる。description は改行・記号を含むため、
PyYAML の dump で安全にエスケープして書き出す。
"""

import csv
import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "_data" / "products.csv"
OUT_DIR = ROOT / "_products"

# front matter に埋め込む列（title は name から生成）
FIELDS = ["id", "major", "minor", "model", "name", "image", "price", "price_fmt"]


def normalize_text(value: str) -> str:
    """改行コードを LF に統一し、前後の空白を落とす。"""
    return (value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def parse_catalog_pdfs(raw: str):
    raw = (raw or "").strip() or "[]"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"catalog_pdfs の JSON が壊れています: {raw!r} ({exc})")
    cleaned = []
    for item in data:
        cleaned.append(
            {
                "label": normalize_text(str(item.get("label", ""))),
                "url": normalize_text(str(item.get("url", ""))),
            }
        )
    return cleaned


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV が見つかりません: {CSV_PATH}")

    OUT_DIR.mkdir(exist_ok=True)
    # 再実行できるよう既存の生成物を掃除する
    for old in OUT_DIR.glob("*.md"):
        old.unlink()

    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    written = 0
    for row in rows:
        pid = normalize_text(row["id"])
        if not pid:
            continue

        front = {"layout": "product"}
        for key in FIELDS:
            front[key] = normalize_text(row.get(key, ""))
        # Jekyll のコレクションドキュメントでは page.id が予約済みで、
        # front matter の id は page.id からは読めない（/products/<id> を返す）。
        # レイアウトから確実に参照できるよう別名でも持たせる。
        front["product_id"] = front["id"]
        front["title"] = front["name"]
        front["description"] = normalize_text(row.get("description", ""))
        front["catalog_pdfs"] = parse_catalog_pdfs(row.get("catalog_pdfs", ""))

        # すべてのスカラーを単一引用符で囲む。
        # Ruby(Jekyll)の YAML パーサは "36,720" のようなカンマ区切り値を
        # 整数 36720 と解釈してしまうため、全項目を明示的に文字列化する
        # （CSV 由来の site.data.products と型を揃える意味もある）。
        body = yaml.safe_dump(
            front,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            default_style="'",
            width=4096,
        )

        out_path = OUT_DIR / f"{pid}.md"
        out_path.write_text(f"---\n{body}---\n", encoding="utf-8")
        written += 1

    print(f"{written} 件の商品ページを {OUT_DIR.relative_to(ROOT)}/ に生成しました。")
    if written != len(rows):
        print(
            f"注意: CSV 行数 {len(rows)} と生成数 {written} が一致しません。",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
