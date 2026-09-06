#!/usr/bin/env python3
"""_data/products.csv の catalog_pdfs 列にある file003.shop-pro.jp の PDF を
Cloudinary へ移行する。

- catalog_pdfs_original 列を新規追加し、移行前の catalog_pdfs の値を
  そのままバックアップする(2回目以降の実行では既存の
  catalog_pdfs_original を上書きしない)
- catalog_pdfs は [{"label": "...", "url": "..."}] 形式の JSON 文字列
- 同じ PDF が複数商品から参照されている場合があるため、ユニークな URL
  ごとに 1 回だけアップロードする
- 各 URL は cloudinary.uploader.upload(url, resource_type="raw",
  public_id="catalogs/<元のファイル名(拡張子なし)>", overwrite=True) で
  アップロードする
- 失敗した URL は catalog_pdfs 内で元の URL のまま残し、最後に失敗一覧を
  表示する
- 環境変数 CLOUDINARY_URL を cloudinary SDK が自動で読み込む
"""

import csv
import json
import pathlib
import sys
import time
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "_data" / "products.csv"

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 3
REQUEST_SLEEP_SECONDS = 0.2


def public_id_for(url: str) -> str:
    filename = urlparse(url).path.rsplit("/", 1)[-1]
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    return f"catalogs/{stem}"


def upload_with_retry(url: str):
    """成功したら secure_url を返す。全リトライ失敗なら (None, 最後のエラー文字列) を返す。"""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = cloudinary.uploader.upload(
                url,
                resource_type="raw",
                public_id=public_id_for(url),
                overwrite=True,
            )
            return result["secure_url"], None
        except Exception as exc:  # noqa: BLE001 - アップロード失敗理由をそのまま記録する
            last_error = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS)
    return None, last_error


def parse_catalog_pdfs(raw: str):
    raw = (raw or "").strip() or "[]"
    return json.loads(raw)


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV が見つかりません: {CSV_PATH}")

    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if "catalog_pdfs_original" not in fieldnames:
        idx = fieldnames.index("catalog_pdfs") + 1
        fieldnames = fieldnames[:idx] + ["catalog_pdfs_original"] + fieldnames[idx:]

    for row in rows:
        if not row.get("catalog_pdfs_original"):
            row["catalog_pdfs_original"] = row["catalog_pdfs"]

    # ユニークな file003.shop-pro.jp の URL を集める
    unique_urls = []
    seen = set()
    for row in rows:
        items = parse_catalog_pdfs(row["catalog_pdfs_original"])
        for item in items:
            url = item.get("url", "")
            if "file003.shop-pro.jp" in url and url not in seen:
                seen.add(url)
                unique_urls.append(url)

    total = len(unique_urls)
    print(f"ユニークな PDF URL: {total} 件")

    url_map = {}
    failures = []
    success_count = 0

    for i, url in enumerate(unique_urls, start=1):
        secure_url, error = upload_with_retry(url)
        if secure_url:
            url_map[url] = secure_url
            success_count += 1
            print(f"[{i}/{total}] OK {url} -> {secure_url}")
        else:
            failures.append((url, error))
            print(f"[{i}/{total}] FAILED {url}: {error}")
        time.sleep(REQUEST_SLEEP_SECONDS)

    # 全商品の catalog_pdfs を更新する
    for row in rows:
        items = parse_catalog_pdfs(row["catalog_pdfs_original"])
        for item in items:
            new_url = url_map.get(item.get("url", ""))
            if new_url:
                item["url"] = new_url
        row["catalog_pdfs"] = json.dumps(items, ensure_ascii=False)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"完了: 成功 {success_count} 件 / 失敗 {len(failures)} 件 (全 {total} 件)")

    if failures:
        print()
        print("失敗一覧:")
        for url, error in failures:
            print(f"  url={url} error={error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
