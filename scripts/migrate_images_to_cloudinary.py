#!/usr/bin/env python3
"""_data/products.csv の image 列を旧ショップ(img21.shop-pro.jp)の URL から
Cloudinary の secure_url へ移行する。

- image_original 列を新規追加し、移行前の image 列の値をそのままバックアップする
  (2回目以降の実行では既存の image_original を上書きしない)
- 各行の image_original の URL を cloudinary.uploader.upload() でアップロードし、
  public_id を "products/<id>" にする
- 失敗した行は image を元の URL のまま残し、最後に失敗一覧を表示する
- 環境変数 CLOUDINARY_URL を cloudinary SDK が自動で読み込む
"""

import csv
import sys
import time

import cloudinary
import cloudinary.uploader

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "_data" / "products.csv"

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 3
REQUEST_SLEEP_SECONDS = 0.2


def upload_with_retry(url: str, public_id: str):
    """成功したら secure_url を返す。全リトライ失敗なら (None, 最後のエラー文字列) を返す。"""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = cloudinary.uploader.upload(
                url,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
            )
            return result["secure_url"], None
        except Exception as exc:  # noqa: BLE001 - アップロード失敗理由をそのまま記録する
            last_error = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS)
    return None, last_error


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV が見つかりません: {CSV_PATH}")

    with CSV_PATH.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if "image_original" not in fieldnames:
        # image の直後に image_original を挿入する
        idx = fieldnames.index("image") + 1
        fieldnames = fieldnames[:idx] + ["image_original"] + fieldnames[idx:]

    for row in rows:
        if not row.get("image_original"):
            row["image_original"] = row["image"]

    total = len(rows)
    failures = []
    success_count = 0

    for i, row in enumerate(rows, start=1):
        pid = row["id"]
        source_url = row["image_original"]
        public_id = f"products/{pid}"

        secure_url, error = upload_with_retry(source_url, public_id)

        if secure_url:
            row["image"] = secure_url
            success_count += 1
            print(f"[{i}/{total}] id={pid} OK -> {secure_url}")
        else:
            failures.append((pid, source_url, error))
            print(f"[{i}/{total}] id={pid} FAILED: {error}")

        time.sleep(REQUEST_SLEEP_SECONDS)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"完了: 成功 {success_count} 件 / 失敗 {len(failures)} 件 (全 {total} 件)")

    if failures:
        print()
        print("失敗一覧:")
        for pid, url, error in failures:
            print(f"  id={pid} url={url} error={error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
