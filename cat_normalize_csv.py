#!/usr/bin/env python3
import sys
import os
import glob
import csv

EXPECTED_HEADER_BASE = ["prefecture", "city", "number", "address", "name", "lat", "long"]
EXPECTED_HEADER_OPTION = EXPECTED_HEADER_BASE + ["note"]

def error_exit(msg):
    print(f"エラー: {msg}", file=sys.stderr)
    sys.exit(1)

def extract_wildcard_part(prefix, filename):
    base = os.path.basename(filename)
    if not base.startswith(os.path.basename(prefix)):
        return None
    wildcard = base[len(os.path.basename(prefix)) : -4]
    return wildcard if len(wildcard) > 0 else None

def main():
    if len(sys.argv) != 2:
        error_exit("使い方: python cat_normalize_csv.py <filename_prefix>")
    prefix = sys.argv[1]
    dirname = os.path.dirname(prefix) if os.path.dirname(prefix) else "."
    prefix_base = os.path.basename(prefix)
    glob_pattern = os.path.join(dirname, prefix_base + "*.csv")

    files = glob.glob(glob_pattern)
    candidate_files = []
    for f in files:
        wc = extract_wildcard_part(prefix, f)
        if wc:
            candidate_files.append((wc, f))

    if not candidate_files:
        error_exit(f"対象ファイルが見つかりません: {glob_pattern}")

    candidate_files.sort(key=lambda x: x[0])

    data_rows = []
    file_row_counts = []
    has_note = False
    file_headers = []

    for idx, (wc, file_path) in enumerate(candidate_files):
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                error_exit(f"{file_path} が空ファイルです。")
            file_headers.append(header)
            if set(header) == set(EXPECTED_HEADER_BASE):
                note_idx = None
            elif set(header) == set(EXPECTED_HEADER_OPTION):
                note_idx = header.index("note")
                has_note = True
            else:
                error_exit(
                    f"ヘッダが一致しません: '{file_path}'\n"
                    f"期待値: {','.join(EXPECTED_HEADER_BASE)} または {','.join(EXPECTED_HEADER_OPTION)}\n"
                    f"実際値: {','.join(header)}"
                )
            # 各行をnote列有無に応じて揃える
            for row in reader:
                if has_note:
                    # 出力にnote列が必要
                    if set(header) == set(EXPECTED_HEADER_OPTION):
                        # note列あり
                        data_rows.append(row if len(row) == 8 else row + [""])
                    else:
                        # note列なし
                        data_rows.append(row + [""])
                else:
                    # note列不要
                    data_rows.append(row)
            file_row_counts.append((file_path, len(data_rows) - sum(c for _, c in file_row_counts)))

    # ⑨: ファイル名＆データ行数出力（日本語）
    for file_path, row_count in file_row_counts:
        print(f"{file_path}: データ行数 {row_count}")

    output_file = os.path.join(dirname, prefix_base + ".csv")
    with open(output_file, "w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        if has_note:
            writer.writerow(EXPECTED_HEADER_OPTION)
        else:
            writer.writerow(EXPECTED_HEADER_BASE)
        writer.writerows(data_rows)

    print(f"{len(candidate_files)} 個のファイルを {output_file} に連結しました。")

if __name__ == "__main__":
    main()
