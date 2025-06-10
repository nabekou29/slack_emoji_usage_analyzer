"""メイン集計ロジック"""

from typing import List, Optional
from datetime import date

from .config import Settings
from .logging_cfg import logger
from .emoji_loader import load_emojis, filter_emojis
from .query_builder import generate_month_starts, build_monthly_queries
from .slack_client import search_messages_safe, get_workspace_info
from .csv_writer import write_csv, validate_output_path, backup_existing_file

# グローバル設定
settings = Settings()


def aggregate_emoji_usage(
    months: Optional[int] = None,
    output_path: Optional[str] = None,
    include_standard: bool = True,
    include_custom: bool = True,
    max_emojis: Optional[int] = None,
) -> bool:
    """
    絵文字利用状況を集計してCSVに出力する

    Args:
        months: 集計対象月数（Noneの場合は設定値を使用）
        output_path: 出力ファイルパス（Noneの場合は設定値を使用）
        include_standard: 標準絵文字を含むかどうか
        include_custom: カスタム絵文字を含むかどうか
        max_emojis: 処理する絵文字の最大数（テスト用）

    Returns:
        集計成功（True/False）
    """
    try:
        # パラメータの設定
        target_months = months or settings.months
        target_output = output_path or settings.output_path

        logger.info("Starting emoji usage aggregation")
        logger.info(f"Target months: {target_months}")
        logger.info(f"Output path: {target_output}")

        # 出力パスの検証
        if not validate_output_path(target_output):
            logger.error("Invalid output path")
            return False

        # 既存ファイルのバックアップ
        backup_existing_file(target_output)

        # ワークスペース情報の取得
        workspace_info = get_workspace_info()
        if workspace_info:
            logger.info(f"Workspace: {workspace_info.get('name', 'Unknown')}")

        # 絵文字リストの読み込み
        logger.info("Loading emoji list...")
        emoji_list = load_emojis(
            include_standard=include_standard, include_custom=include_custom
        )

        if not emoji_list:
            logger.error("No emojis loaded")
            return False

        # 絵文字数の制限（テスト用）
        if max_emojis:
            emoji_list = filter_emojis(emoji_list, max_emojis)

        logger.info(f"Processing {len(emoji_list)} emojis")

        # 月次期間の生成
        month_periods = generate_month_starts(target_months)
        logger.info(f"Processing {len(month_periods)} month periods")

        # 集計処理の実行
        records = _perform_aggregation(emoji_list, month_periods)

        if not records:
            logger.warning("No records generated")
            return False

        # CSV出力
        logger.info("Writing results to CSV...")
        write_csv(records, target_output)

        # 統計情報のログ出力
        _log_statistics(records, emoji_list, month_periods)

        logger.info("Emoji usage aggregation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        return False


def _perform_aggregation(
    emoji_list: List[str], month_periods: List[date]
) -> List[List]:
    """
    実際の集計処理を実行する

    Args:
        emoji_list: 絵文字リスト
        month_periods: 月次期間リスト

    Returns:
        集計結果のレコードリスト
    """
    records = []
    total_queries = len(emoji_list) * len(month_periods) * 2  # テキスト+リアクション
    processed_queries = 0

    logger.info(f"Total queries to process: {total_queries}")

    for emoji_idx, emoji_name in enumerate(emoji_list):
        logger.info(f"Processing emoji {emoji_idx + 1}/{len(emoji_list)}: {emoji_name}")

        for month_idx, month_start in enumerate(month_periods):
            try:
                # クエリの構築
                text_query, reaction_query = build_monthly_queries(
                    emoji_name, month_start
                )

                # テキスト検索の実行
                text_count = search_messages_safe(text_query)
                processed_queries += 1

                # リアクション検索の実行
                reaction_count = search_messages_safe(reaction_query)
                processed_queries += 1

                # 合計カウント
                total_count = text_count + reaction_count

                # レコードの追加
                month_str = month_start.strftime("%Y-%m")
                records.append([emoji_name, month_str, total_count])

                # 進捗ログ
                if total_count > 0:
                    logger.info(f"  {month_str}: {total_count} usages")
                else:
                    logger.debug(f"  {month_str}: 0 usages")

                # 進捗状況の表示
                progress = (processed_queries / total_queries) * 100
                if processed_queries % 10 == 0:  # 10クエリごとに進捗表示
                    logger.info(
                        f"Progress: {processed_queries}/{total_queries} queries "
                        f"({progress:.1f}%)"
                    )

            except Exception as e:
                logger.error(f"Error processing {emoji_name} for {month_start}: {e}")
                # エラーが発生した場合は0でレコードを追加
                month_str = month_start.strftime("%Y-%m")
                records.append([emoji_name, month_str, 0])
                processed_queries += 2  # 2つのクエリをスキップしたとしてカウント

    logger.info(f"Aggregation completed: {len(records)} records generated")
    return records


def _log_statistics(
    records: List[List], emoji_list: List[str], month_periods: List[date]
) -> None:
    """
    統計情報をログに出力する

    Args:
        records: 集計結果のレコード
        emoji_list: 処理した絵文字リスト
        month_periods: 処理した月次期間
    """
    try:
        total_usage = sum(int(record[2]) for record in records)
        non_zero_records = [r for r in records if int(r[2]) > 0]
        usage_by_emoji = {}

        for record in records:
            emoji_name = record[0]
            usage_count = int(record[2])
            if emoji_name not in usage_by_emoji:
                usage_by_emoji[emoji_name] = 0
            usage_by_emoji[emoji_name] += usage_count

        # 使用回数の多い絵文字トップ10
        top_emojis = sorted(usage_by_emoji.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        logger.info("=== Aggregation Statistics ===")
        logger.info(f"Total records: {len(records)}")
        logger.info(f"Total usage count: {total_usage}")
        logger.info(f"Records with usage > 0: {len(non_zero_records)}")
        logger.info(f"Emojis processed: {len(emoji_list)}")
        logger.info(f"Months processed: {len(month_periods)}")

        if top_emojis:
            logger.info("Top 10 most used emojis:")
            for i, (emoji_name, count) in enumerate(top_emojis):
                logger.info(f"  {i + 1}. {emoji_name}: {count} usages")

        logger.info("===============================")

    except Exception as e:
        logger.error(f"Failed to log statistics: {e}")


def quick_test_aggregation(emoji_count: int = 5, months: int = 2) -> bool:
    """
    テスト用の簡易集計

    Args:
        emoji_count: テストする絵文字数
        months: テストする月数

    Returns:
        テスト成功（True/False）
    """
    logger.info(
        f"Running quick test aggregation ({emoji_count} emojis, {months} months)"
    )

    return aggregate_emoji_usage(
        months=months,
        output_path="test_emoji_usage.csv",
        include_standard=True,
        include_custom=False,  # テストでは標準絵文字のみ
        max_emojis=emoji_count,
    )
