from __future__ import annotations

import datetime as dt
import re
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SPACE = " " * 5
NR_RE = re.compile(r"^(\d{2,})([A-Za-z])$")
CALL_RE = re.compile(r"^[A-Z0-9]{2,}[A-Z0-9/]*$")


@dataclass(frozen=True)
class Contest:
    key: str
    name: str
    short: str
    out_dir: str
    url_template: str
    output_bands: tuple[str, ...]


@dataclass(frozen=True)
class QsoRecord:
    contest: str
    year: int
    band_group: str
    callsign: str
    number: str | None


CONTESTS: dict[str, Contest] = {
    "j": Contest(
        "j",
        "ALL JA",
        "ALLJA",
        "SCP_for_ALLJA",
        "https://www.jarl.org/Japanese/1_Tanoshimo/1-1_Contest/all_ja/{YEAR}/publiclog-{YEAR}_allja.zip",
        ("HF", "50"),
    ),
    "6": Contest(
        "6",
        "6m AND DOWN",
        "6D",
        "SCP_for_6D",
        "https://www.jarl.org/Japanese/1_Tanoshimo/1-1_Contest/6m/{YEAR}/publiclog-{YEAR}_6d.zip",
        ("50", "VU", "1.2", "SH"),
    ),
    "f": Contest(
        "f",
        "Field Day",
        "FD",
        "SCP_for_FD",
        "https://www.jarl.org/Japanese/1_Tanoshimo/1-1_Contest/fd/{YEAR}/publiclog-{YEAR}_fd.zip",
        ("HF", "50", "VU", "1.2", "SH"),
    ),
    "a": Contest(
        "a",
        "全市全郡",
        "ACAG",
        "SCP_for_ACAG",
        "https://www.jarl.org/Japanese/1_Tanoshimo/1-1_Contest/all_cg/{YEAR}/publiclog-{YEAR}_acag.zip",
        ("HF", "50", "VU", "1.2", "SH"),
    ),
}


BAND_LABELS: dict[str, str] = {
    "HF": "HF",
    "50": "50MHz",
    "VU": "144/430MHz",
    "1.2": "1200MHz",
    "SH": "2.4GHz and UP",
}


def target_years() -> list[int]:
    current_year = dt.date.today().year
    return [year for year in range(current_year, current_year - 5, -1) if year >= 2025]


def band_group(band: str) -> str | None:
    b = band.strip().upper()

    mapping: dict[str, str] = {
        "1.8": "HF",
        "1.9": "HF",
        "3.5": "HF",
        "7": "HF",
        "14": "HF",
        "21": "HF",
        "28": "HF",
        "50": "50",
        "144": "VU",
        "430": "VU",
        "1200": "1.2",
        "1.2G": "1.2",
    }

    if b in mapping:
        return mapping[b]

    try:
        freq = float(b.replace("G", ""))
    except ValueError:
        return None

    if freq >= 2400:
        return "SH"

    return None


def is_pref_number(number: str) -> bool:
    match = NR_RE.match(number)
    return bool(match and 2 <= len(match.group(1)) <= 3)


def is_city_number(number: str) -> bool:
    match = NR_RE.match(number)
    return bool(match and len(match.group(1)) >= 4)


def number_without_power(number: str) -> str:
    match = NR_RE.match(number)
    if match is None:
        return number
    return match.group(1)


def download_zip(contest: Contest, year: int, cache_dir: Path) -> Path | None:
    cache_dir.mkdir(parents=True, exist_ok=True)

    zip_path = cache_dir / f"{contest.short}_{year}.zip"

    if zip_path.exists() and zip_path.stat().st_size > 0:
        return zip_path

    url = contest.url_template.replace("{YEAR}", str(year))

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            status = getattr(response, "status", 200)

            if status != 200:
                print(f"警告: 取得失敗 {contest.name} {year} HTTP {status}")
                return None

            zip_path.write_bytes(response.read())

        return zip_path

    except urllib.error.HTTPError as exc:
        print(f"警告: 取得失敗 {contest.name} {year} HTTP {exc.code}")
        return None

    except urllib.error.URLError as exc:
        print(f"警告: 取得失敗 {contest.name} {year}: {exc.reason}")
        return None

    except TimeoutError:
        print(f"警告: 取得失敗 {contest.name} {year}: timeout")
        return None

    except OSError as exc:
        print(f"警告: 取得失敗 {contest.name} {year}: {exc}")
        return None


def decode_bytes(data: bytes) -> str | None:
    for encoding in ("utf-8", "shift_jis", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    return None


def parse_log_text(text: str, contest_short: str, year: int) -> list[QsoRecord]:
    records: list[QsoRecord] = []

    for line in text.splitlines():
        parts = line.split()

        if len(parts) < 10:
            continue

        band = parts[0]
        group = band_group(band)

        if group is None:
            continue

        callsign = parts[7].upper()
        number = parts[9].upper()

        if not CALL_RE.match(callsign):
            continue

        if not NR_RE.match(number):
            number = None

        records.append(
            QsoRecord(
                contest=contest_short,
                year=year,
                band_group=group,
                callsign=callsign,
                number=number,
            )
        )

    return records


def read_zip_logs(zip_path: Path, contest_short: str, year: int) -> list[QsoRecord]:
    records: list[QsoRecord] = []

    try:
        with zipfile.ZipFile(zip_path) as zip_file:
            for name in zip_file.namelist():
                if name.endswith("/"):
                    continue

                data = zip_file.read(name)
                text = decode_bytes(data)

                if text is None:
                    print(f"警告: 文字コード判定失敗 {zip_path.name}:{name}")
                    continue

                records.extend(parse_log_text(text, contest_short, year))

    except zipfile.BadZipFile:
        print(f"警告: zip展開失敗 {zip_path}")

    return records


def collect_all_records(base_dir: Path) -> list[QsoRecord]:
    cache_dir = base_dir / ".jarl_publiclog_cache"
    records: list[QsoRecord] = []

    for year in target_years():
        for contest in CONTESTS.values():
            zip_path = download_zip(contest, year, cache_dir)

            if zip_path is None:
                continue

            records.extend(read_zip_logs(zip_path, contest.short, year))

    return records


def rank_record(record: QsoRecord, selected: Contest, output_band: str) -> tuple[int, int]:
    same_contest = record.contest == selected.short
    same_band = record.band_group == output_band

    if same_contest and same_band:
        group_rank = 0
    elif same_band:
        group_rank = 1
    elif same_contest:
        group_rank = 2
    else:
        group_rank = 3

    return group_rank, -record.year


def uses_city_rule(selected: Contest, output_band: str) -> bool:
    return selected.short == "ACAG" or output_band == "SH"


def build_entries(
    records: Iterable[QsoRecord],
    selected: Contest,
    output_band: str,
) -> list[str]:
    by_call: dict[str, list[QsoRecord]] = defaultdict(list)

    for record in records:
        by_call[record.callsign].append(record)

    lines: list[str] = []

    for callsign, call_records in by_call.items():
        if uses_city_rule(selected, output_band):
            valid = [
                record
                for record in call_records
                if record.number is not None and is_city_number(record.number)
            ]

            if valid:
                best_rank = min(
                    rank_record(record, selected, output_band)
                    for record in valid
                )

                numbers = sorted(
                    {
                        record.number
                        for record in valid
                        if rank_record(record, selected, output_band) == best_rank
                    }
                )

                for number in numbers:
                    lines.append(f"{callsign}{SPACE}{number}")
            else:
                lines.append(callsign)

        else:
            valid = [
                record
                for record in call_records
                if record.number is not None and is_pref_number(record.number)
            ]

            if not valid:
                continue

            best_rank = min(
                rank_record(record, selected, output_band)
                for record in valid
            )

            numbers = sorted(
                {
                    record.number
                    for record in valid
                    if rank_record(record, selected, output_band) == best_rank
                }
            )

            for number in numbers:
                lines.append(f"{callsign}{SPACE}{number}")

    return sorted(lines)


def build_other_entries(records: Iterable[QsoRecord]) -> list[str]:
    by_call: dict[str, list[QsoRecord]] = defaultdict(list)

    for record in records:
        if record.number is not None and is_pref_number(record.number):
            by_call[record.callsign].append(record)

    lines: list[str] = []

    for callsign, call_records in by_call.items():
        best_year = max(record.year for record in call_records)

        numbers = sorted(
            {
                number_without_power(record.number)
                for record in call_records
                if record.year == best_year and record.number is not None
            }
        )

        for number in numbers:
            lines.append(f"{callsign}{SPACE}{number}")

    return sorted(lines)


def write_scp_files(
    selected: Contest,
    records: list[QsoRecord],
    base_dir: Path,
) -> list[Path]:
    out_dir = base_dir / selected.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    for band in selected.output_bands:
        entries = build_entries(records, selected, band)
        path = out_dir / f"{selected.short}_{band}.scp"

        header = f"# Super Check File for {selected.name} {BAND_LABELS[band]}"
        path.write_text(
            header + "\n" + "\n".join(entries) + "\n",
            encoding="utf-8",
        )

        written.append(path)

    return written


def write_other_scp_file(records: list[QsoRecord], base_dir: Path) -> list[Path]:
    out_dir = base_dir / "SCP_Files"
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / "Super_Check_file.scp"
    entries = build_other_entries(records)

    header = "# Super Check File"
    path.write_text(
        header + "\n" + "\n".join(entries) + "\n",
        encoding="utf-8",
    )

    return [path]


def choose_contest() -> Contest | None:
    print("コンテストを選択してください")
    print("ALL JA      : j")
    print("6m AND DOWN : 6")
    print("Field Day   : f")
    print("全市全郡     : a")
    print("その他       : o")

    key = input("> ").strip().lower()

    if key == "o":
        return None

    if key not in CONTESTS:
        raise SystemExit("無効な選択です。")

    return CONTESTS[key]


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    selected = choose_contest()

    if selected is None:
        print("その他用 SCP を生成します。")
    else:
        print(f"{selected.name} 用 SCP を生成します。")

    records = collect_all_records(base_dir)

    if not records:
        raise SystemExit("有効なログデータを取得できませんでした。")

    if selected is None:
        written = write_other_scp_file(records, base_dir)
    else:
        written = write_scp_files(selected, records, base_dir)

    print("\n生成したファイル:")
    for path in written:
        print(path.relative_to(base_dir))


if __name__ == "__main__":
    main()
