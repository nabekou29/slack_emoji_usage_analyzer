"""CSV出力モジュール"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from .logging_cfg import logger


def validate_output_path(output_path: str) -> bool:
    """
    出力パスの妥当性を検証する

    Args:
        output_path: 出力ファイルパス

    Returns:
        パスが有効かどうか
    """
    if not output_path:
        logger.error("Output path is empty")
        return False

    # ディレクトリの存在確認と作成
    output_dir = Path(output_path).parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Cannot create output directory {output_dir}: {e}")
        return False

    # 書き込み権限の確認
    if output_dir.exists() and not os.access(output_dir, os.W_OK):
        logger.error(f"No write permission for directory: {output_dir}")
        return False

    return True


def backup_existing_file(output_path: str) -> None:
    """
    既存ファイルのバックアップを作成する

    Args:
        output_path: 出力ファイルパス
    """
    if not os.path.exists(output_path):
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{output_path}.backup_{timestamp}"

        # ファイルをコピー
        import shutil

        shutil.copy2(output_path, backup_path)
        logger.info(f"Created backup: {backup_path}")

    except Exception as e:
        logger.warning(f"Failed to create backup: {e}")


def write_csv(records: List[List], output_path: str, pivot_format: bool = True) -> None:
    """
    集計結果をCSVファイルに出力する

    Args:
        records: 集計結果のレコードリスト
        output_path: 出力ファイルパス
        pivot_format: ピボット形式で出力するかどうか
    """
    try:
        logger.info(f"Writing {len(records)} records to {output_path}")

        if pivot_format:
            _write_pivot_csv(records, output_path)
        else:
            _write_standard_csv(records, output_path)

        # ファイルサイズの確認
        file_size = os.path.getsize(output_path)
        logger.info(f"Output file size: {file_size:,} bytes")

    except Exception as e:
        logger.error(f"Failed to write CSV file: {e}")
        raise


def _write_standard_csv(records: List[List], output_path: str) -> None:
    """
    標準形式でCSVを出力する

    Args:
        records: 集計結果のレコードリスト
        output_path: 出力ファイルパス
    """
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # ヘッダーの書き込み
        writer.writerow(["emoji", "period", "usage_count"])

        # データの書き込み
        for record in records:
            writer.writerow(record)

    logger.info(f"Standard CSV file written successfully: {output_path}")


def _write_pivot_csv(records: List[List], output_path: str) -> None:
    """
    ピボット形式でCSVを出力する

    Args:
        records: 集計結果のレコードリスト
        output_path: 出力ファイルパス
    """
    # データをピボット形式に変換
    pivot_data = _convert_to_pivot(records)
    
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # ヘッダーの準備
        if not pivot_data["periods"]:
            # データが空の場合
            writer.writerow(["emoji", "total"])
            return

        periods = sorted(pivot_data["periods"])
        header = ["emoji"] + periods + ["total", "average", "max_period"]
        writer.writerow(header)

        # データの書き込み
        for emoji_name, emoji_data in sorted(pivot_data["data"].items()):
            row = [emoji_name]
            
            # 各期間の使用回数
            period_values = []
            for period in periods:
                value = emoji_data.get(period, 0)
                row.append(value)
                period_values.append(value)
            
            # 統計情報
            total = sum(period_values)
            average = total / len(period_values) if period_values else 0
            max_period = max(emoji_data.keys(), key=lambda p: emoji_data[p]) if emoji_data else ""
            
            row.extend([total, f"{average:.1f}", max_period])
            writer.writerow(row)

        # 合計行を追加
        _write_pivot_summary(writer, pivot_data, periods)

    logger.info(f"Pivot CSV file written successfully: {output_path}")


def _convert_to_pivot(records: List[List]) -> Dict[str, Any]:
    """
    レコードをピボット形式のデータ構造に変換する

    Args:
        records: 集計結果のレコードリスト

    Returns:
        ピボット形式のデータ
    """
    data = defaultdict(dict)
    periods = set()

    for record in records:
        if len(record) != 3:
            continue
        
        emoji_name, period, usage_count = record
        try:
            usage_int = int(usage_count)
            data[emoji_name][period] = usage_int
            periods.add(period)
        except (ValueError, TypeError):
            logger.warning(f"Invalid usage count: {usage_count} for {emoji_name}")
            continue

    return {
        "data": dict(data),
        "periods": periods
    }


def _write_pivot_summary(writer, pivot_data: Dict[str, Any], periods: List[str]) -> None:
    """
    ピボット形式のサマリー行を書き込む

    Args:
        writer: CSVライター
        pivot_data: ピボットデータ
        periods: 期間リスト
    """
    # 空行
    writer.writerow([])
    
    # 期間ごとの合計行
    total_row = ["TOTAL"]
    grand_total = 0
    
    for period in periods:
        period_total = sum(
            emoji_data.get(period, 0) 
            for emoji_data in pivot_data["data"].values()
        )
        total_row.append(period_total)
        grand_total += period_total
    
    # 総合計と平均
    total_average = grand_total / len(periods) if periods else 0
    total_row.extend([grand_total, f"{total_average:.1f}", ""])
    writer.writerow(total_row)


def write_pivot_csv(records: List[List], output_path: str) -> None:
    """
    ピボット形式でCSVを出力する（パブリック関数）

    Args:
        records: 集計結果のレコードリスト
        output_path: 出力ファイルパス
    """
    write_csv(records, output_path, pivot_format=True)


def read_csv(input_path: str) -> List[List]:
    """
    CSVファイルを読み込む

    Args:
        input_path: 入力ファイルパス

    Returns:
        読み込まれたレコードのリスト
    """
    records = []

    try:
        with open(input_path, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)

            # ヘッダーをスキップ
            next(reader, None)

            for row in reader:
                records.append(row)

        logger.info(f"Read {len(records)} records from {input_path}")
        return records

    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        raise


def validate_csv_records(records: List[List]) -> List[List]:
    """
    CSVレコードの妥当性を検証し、不正なレコードを除去する

    Args:
        records: レコードのリスト

    Returns:
        検証済みのレコードのリスト
    """
    valid_records = []

    for i, record in enumerate(records):
        try:
            # レコードの基本検証
            if len(record) != 3:
                logger.warning(f"Invalid record length at row {i + 1}: {record}")
                continue

            emoji_name, month, usage_count = record

            # 絵文字名の検証
            if not emoji_name or not isinstance(emoji_name, str):
                logger.warning(f"Invalid emoji name at row {i + 1}: {emoji_name}")
                continue

            # 月の検証（YYYY-MM形式またはYYYY-MM to YYYY-MM形式）
            if not _validate_period_format(month):
                logger.warning(f"Invalid period format at row {i + 1}: {month}")
                continue

            # 使用回数の検証
            try:
                usage_int = int(usage_count)
                if usage_int < 0:
                    logger.warning(
                        f"Negative usage count at row {i + 1}: {usage_count}"
                    )
                    continue
            except ValueError:
                logger.warning(f"Invalid usage count at row {i + 1}: {usage_count}")
                continue

            valid_records.append([emoji_name, month, str(usage_int)])

        except Exception as e:
            logger.warning(f"Error validating record at row {i + 1}: {e}")
            continue

    removed_count = len(records) - len(valid_records)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} invalid records")

    return valid_records


def _validate_period_format(period: str) -> bool:
    """
    期間フォーマットの妥当性を検証する

    Args:
        period: 期間文字列

    Returns:
        フォーマットが有効かどうか
    """
    try:
        # YYYY-MM形式
        if len(period) == 7 and period[4] == '-':
            datetime.strptime(period, "%Y-%m")
            return True
        
        # YYYY-MM to YYYY-MM形式
        if " to " in period:
            parts = period.split(" to ")
            if len(parts) == 2:
                datetime.strptime(parts[0], "%Y-%m")
                datetime.strptime(parts[1], "%Y-%m")
                return True
        
        return False
    except ValueError:
        return False


def append_to_csv(records: List[List], output_path: str) -> None:
    """
    既存のCSVファイルにレコードを追加する

    Args:
        records: 追加するレコードのリスト
        output_path: 出力ファイルパス
    """
    try:
        file_exists = os.path.exists(output_path)

        with open(output_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # ファイルが新規作成の場合はヘッダーを書き込み
            if not file_exists:
                writer.writerow(["emoji", "period", "usage_count"])

            # データの書き込み
            for record in records:
                writer.writerow(record)

        logger.info(f"Appended {len(records)} records to {output_path}")

    except Exception as e:
        logger.error(f"Failed to append to CSV file: {e}")
        raise