"""集計モジュールのテスト"""

from unittest.mock import Mock, patch
import pytest
from emoji_usage.aggregator import (
    aggregate_emoji_usage,
    _perform_monthly_aggregation,
    _perform_period_aggregation,
)


class TestAggregateEmojiUsage:
    """aggregate_emoji_usage関数のテスト"""

    @patch("emoji_usage.aggregator.get_workspace_info")
    @patch("emoji_usage.aggregator.load_emojis")
    @patch("emoji_usage.aggregator.validate_output_path")
    @patch("emoji_usage.aggregator.backup_existing_file")
    @patch("emoji_usage.aggregator.write_csv")
    @patch("emoji_usage.aggregator.generate_month_starts")
    @patch("emoji_usage.aggregator._perform_monthly_aggregation")
    def test_monthly_aggregation_success(
        self,
        mock_perform_monthly,
        mock_generate_months,
        mock_write_csv,
        mock_backup,
        mock_validate_path,
        mock_load_emojis,
        mock_get_workspace,
    ):
        """月次集計の成功テスト"""
        # モックの設定
        mock_validate_path.return_value = True
        mock_load_emojis.return_value = ["smile", "heart"]
        mock_get_workspace.return_value = {"name": "Test Workspace"}
        mock_generate_months.return_value = ["2023-01-01", "2023-02-01"]
        mock_perform_monthly.return_value = [
            ["smile", "2023-01", 10],
            ["heart", "2023-01", 5],
        ]

        # 1ヶ月間隔での実行
        result = aggregate_emoji_usage(months=2, interval_months=1)

        assert result is True
        mock_perform_monthly.assert_called_once()
        mock_write_csv.assert_called_once()

    @patch("emoji_usage.aggregator.get_workspace_info")
    @patch("emoji_usage.aggregator.load_emojis")
    @patch("emoji_usage.aggregator.validate_output_path")
    @patch("emoji_usage.aggregator.backup_existing_file")
    @patch("emoji_usage.aggregator.write_csv")
    @patch("emoji_usage.aggregator.generate_period_starts")
    @patch("emoji_usage.aggregator._perform_period_aggregation")
    def test_period_aggregation_success(
        self,
        mock_perform_period,
        mock_generate_periods,
        mock_write_csv,
        mock_backup,
        mock_validate_path,
        mock_load_emojis,
        mock_get_workspace,
    ):
        """期間集計の成功テスト"""
        # モックの設定
        mock_validate_path.return_value = True
        mock_load_emojis.return_value = ["smile", "heart"]
        mock_get_workspace.return_value = {"name": "Test Workspace"}
        mock_generate_periods.return_value = ["2023-01-01", "2023-04-01"]
        mock_perform_period.return_value = [
            ["smile", "2023-01 to 2023-03", 30],
            ["heart", "2023-01 to 2023-03", 15],
        ]

        # 3ヶ月間隔での実行
        result = aggregate_emoji_usage(months=6, interval_months=3)

        assert result is True
        mock_perform_period.assert_called_once()
        mock_write_csv.assert_called_once()

    @patch("emoji_usage.aggregator.load_emojis")
    @patch("emoji_usage.aggregator.validate_output_path")
    def test_no_emojis_loaded(self, mock_validate_path, mock_load_emojis):
        """絵文字が読み込まれない場合のテスト"""
        mock_validate_path.return_value = True
        mock_load_emojis.return_value = []

        result = aggregate_emoji_usage()

        assert result is False

    @patch("emoji_usage.aggregator.validate_output_path")
    def test_invalid_output_path(self, mock_validate_path):
        """無効な出力パスのテスト"""
        mock_validate_path.return_value = False

        result = aggregate_emoji_usage()

        assert result is False


class TestPerformMonthlyAggregation:
    """_perform_monthly_aggregation関数のテスト"""

    @patch("emoji_usage.aggregator.search_messages_safe")
    @patch("emoji_usage.aggregator.build_monthly_queries")
    def test_successful_monthly_aggregation(
        self, mock_build_queries, mock_search_messages
    ):
        """正常な月次集計のテスト"""
        from datetime import date

        # モックの設定
        mock_build_queries.return_value = ("text_query", "reaction_query")
        mock_search_messages.side_effect = [5, 3]  # テキスト: 5, リアクション: 3

        emoji_list = ["smile"]
        month_periods = [date(2023, 1, 1)]

        result = _perform_monthly_aggregation(emoji_list, month_periods)

        assert len(result) == 1
        assert result[0] == ["smile", "2023-01", 8]  # 5 + 3 = 8

    @patch("emoji_usage.aggregator.search_messages_safe")
    @patch("emoji_usage.aggregator.build_monthly_queries")
    def test_multiple_emojis_and_months(self, mock_build_queries, mock_search_messages):
        """複数絵文字・複数月のテスト"""
        from datetime import date

        mock_build_queries.return_value = ("text_query", "reaction_query")
        mock_search_messages.side_effect = [1, 2, 3, 4]  # 各クエリの結果

        emoji_list = ["smile", "heart"]
        month_periods = [date(2023, 1, 1)]

        result = _perform_monthly_aggregation(emoji_list, month_periods)

        assert len(result) == 2
        assert result[0] == ["smile", "2023-01", 3]  # 1 + 2 = 3
        assert result[1] == ["heart", "2023-01", 7]  # 3 + 4 = 7


class TestPerformPeriodAggregation:
    """_perform_period_aggregation関数のテスト"""

    @patch("emoji_usage.aggregator.search_messages_safe")
    @patch("emoji_usage.aggregator.build_period_queries")
    def test_successful_period_aggregation(
        self, mock_build_queries, mock_search_messages
    ):
        """正常な期間集計のテスト"""
        from datetime import date

        # モックの設定
        mock_build_queries.return_value = ("text_query", "reaction_query")
        mock_search_messages.side_effect = [10, 5]  # テキスト: 10, リアクション: 5

        emoji_list = ["thumbsup"]
        period_starts = [date(2023, 1, 1)]
        interval_months = 3

        result = _perform_period_aggregation(emoji_list, period_starts, interval_months)

        assert len(result) == 1
        assert result[0] == ["thumbsup", "2023-01 to 2023-03", 15]  # 10 + 5 = 15

    @patch("emoji_usage.aggregator.search_messages_safe")
    @patch("emoji_usage.aggregator.build_period_queries")
    def test_six_month_interval(self, mock_build_queries, mock_search_messages):
        """6ヶ月間隔のテスト"""
        from datetime import date

        mock_build_queries.return_value = ("text_query", "reaction_query")
        mock_search_messages.side_effect = [20, 10]

        emoji_list = ["star"]
        period_starts = [date(2023, 1, 1)]
        interval_months = 6

        result = _perform_period_aggregation(emoji_list, period_starts, interval_months)

        assert len(result) == 1
        assert result[0] == ["star", "2023-01 to 2023-06", 30]  # 20 + 10 = 30

    @patch("emoji_usage.aggregator.search_messages_safe")
    @patch("emoji_usage.aggregator.build_period_queries")
    def test_error_handling(self, mock_build_queries, mock_search_messages):
        """エラーハンドリングのテスト"""
        from datetime import date

        mock_build_queries.return_value = ("text_query", "reaction_query")
        mock_search_messages.side_effect = Exception("API Error")

        emoji_list = ["error_emoji"]
        period_starts = [date(2023, 1, 1)]
        interval_months = 3

        result = _perform_period_aggregation(emoji_list, period_starts, interval_months)

        assert len(result) == 1
        assert result[0] == ["error_emoji", "2023-01 to 2023-03", 0]  # エラー時は0

    @patch("emoji_usage.aggregator.search_messages_safe")
    @patch("emoji_usage.aggregator.build_period_queries")
    def test_multiple_periods(self, mock_build_queries, mock_search_messages):
        """複数期間のテスト"""
        from datetime import date

        mock_build_queries.return_value = ("text_query", "reaction_query")
        mock_search_messages.side_effect = [5, 5, 3, 2]  # 2期間分の結果

        emoji_list = ["wave"]
        period_starts = [date(2023, 1, 1), date(2023, 4, 1)]
        interval_months = 3

        result = _perform_period_aggregation(emoji_list, period_starts, interval_months)

        assert len(result) == 2
        assert result[0] == ["wave", "2023-01 to 2023-03", 10]  # 5 + 5 = 10
        assert result[1] == ["wave", "2023-04 to 2023-06", 5]  # 3 + 2 = 5
