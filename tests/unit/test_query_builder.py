"""クエリビルダーモジュールのテスト"""

from datetime import date
import pytest
from emoji_usage.query_builder import (
    generate_month_starts,
    generate_period_starts,
    build_monthly_queries,
    build_period_queries,
    validate_query,
    escape_emoji_name,
)


class TestGenerateMonthStarts:
    """generate_month_starts関数のテスト"""

    def test_single_month(self):
        """1ヶ月分の生成テスト"""
        result = generate_month_starts(1)
        assert len(result) == 1
        # 現在月の月初が生成される
        assert result[0].day == 1

    def test_multiple_months(self):
        """複数月の生成テスト"""
        result = generate_month_starts(3)
        assert len(result) == 3
        # すべて月初
        for month_start in result:
            assert month_start.day == 1
        # 新しい月から古い月の順
        assert result[0] > result[1] > result[2]


class TestGeneratePeriodStarts:
    """generate_period_starts関数のテスト"""

    def test_monthly_interval(self):
        """1ヶ月間隔のテスト"""
        result = generate_period_starts(12, 1)
        assert len(result) == 12

    def test_quarterly_interval(self):
        """3ヶ月間隔のテスト"""
        result = generate_period_starts(12, 3)
        assert len(result) == 4  # 12 / 3 = 4期間

    def test_half_yearly_interval(self):
        """6ヶ月間隔のテスト"""
        result = generate_period_starts(12, 6)
        assert len(result) == 2  # 12 / 6 = 2期間

    def test_uneven_division(self):
        """割り切れない場合のテスト"""
        result = generate_period_starts(13, 3)
        assert len(result) == 5  # ceil(13 / 3) = 5期間

    def test_period_order(self):
        """期間の順序テスト"""
        result = generate_period_starts(6, 2)
        assert len(result) == 3
        # 新しい期間から古い期間の順
        assert result[0] > result[1] > result[2]


class TestBuildMonthlyQueries:
    """build_monthly_queries関数のテスト"""

    def test_basic_query_construction(self):
        """基本的なクエリ構築テスト"""
        emoji_name = "smile"
        month_start = date(2023, 1, 1)

        text_query, reaction_query = build_monthly_queries(emoji_name, month_start)

        assert ":smile:" in text_query
        assert "after:2023-01-01" in text_query
        assert "before:2023-01-31" in text_query

        assert "has::smile:" in reaction_query
        assert "after:2023-01-01" in reaction_query
        assert "before:2023-01-31" in reaction_query

    def test_february_leap_year(self):
        """2月（うるう年）のテスト"""
        emoji_name = "heart"
        month_start = date(2024, 2, 1)  # 2024年はうるう年

        text_query, reaction_query = build_monthly_queries(emoji_name, month_start)

        assert "before:2024-02-29" in text_query  # うるう年の2月29日
        assert "before:2024-02-29" in reaction_query

    def test_february_non_leap_year(self):
        """2月（平年）のテスト"""
        emoji_name = "heart"
        month_start = date(2023, 2, 1)  # 2023年は平年

        text_query, reaction_query = build_monthly_queries(emoji_name, month_start)

        assert "before:2023-02-28" in text_query  # 平年の2月28日
        assert "before:2023-02-28" in reaction_query


class TestBuildPeriodQueries:
    """build_period_queries関数のテスト"""

    def test_three_month_period(self):
        """3ヶ月期間のテスト"""
        emoji_name = "thumbsup"
        period_start = date(2023, 1, 1)
        interval_months = 3

        text_query, reaction_query = build_period_queries(
            emoji_name, period_start, interval_months
        )

        assert ":thumbsup:" in text_query
        assert "after:2023-01-01" in text_query
        assert "before:2023-03-31" in text_query  # 3ヶ月後の最終日

        assert "has::thumbsup:" in reaction_query
        assert "after:2023-01-01" in reaction_query
        assert "before:2023-03-31" in reaction_query

    def test_six_month_period(self):
        """6ヶ月期間のテスト"""
        emoji_name = "star"
        period_start = date(2023, 7, 1)
        interval_months = 6

        text_query, reaction_query = build_period_queries(
            emoji_name, period_start, interval_months
        )

        assert "after:2023-07-01" in text_query
        assert "before:2023-12-31" in text_query  # 6ヶ月後の最終日

    def test_year_crossing_period(self):
        """年をまたぐ期間のテスト"""
        emoji_name = "party"
        period_start = date(2023, 11, 1)
        interval_months = 3

        text_query, reaction_query = build_period_queries(
            emoji_name, period_start, interval_months
        )

        assert "after:2023-11-01" in text_query
        assert "before:2024-01-31" in text_query  # 翌年の1月末


class TestValidateQuery:
    """validate_query関数のテスト"""

    def test_valid_query(self):
        """有効なクエリのテスト"""
        query = ":smile: after:2023-01-01 before:2023-01-31"
        assert validate_query(query) is True

    def test_empty_query(self):
        """空のクエリのテスト"""
        assert validate_query("") is False
        assert validate_query(None) is False

    def test_too_long_query(self):
        """長すぎるクエリのテスト"""
        long_query = "a" * 1001
        assert validate_query(long_query) is False

    def test_missing_emoji_pattern(self):
        """絵文字パターンが不足しているクエリのテスト"""
        query = "after:2023-01-01 before:2023-01-31"
        assert validate_query(query) is False

    def test_non_string_query(self):
        """文字列以外のクエリのテスト"""
        assert validate_query(123) is False
        assert validate_query([]) is False


class TestEscapeEmojiName:
    """escape_emoji_name関数のテスト"""

    def test_normal_emoji_name(self):
        """通常の絵文字名のテスト"""
        result = escape_emoji_name("smile")
        assert result == "smile"

    def test_emoji_name_with_quotes(self):
        """引用符を含む絵文字名のテスト"""
        result = escape_emoji_name('test"emoji')
        assert result == 'test\\"emoji'

    def test_emoji_name_with_multiple_quotes(self):
        """複数の引用符を含む絵文字名のテスト"""
        result = escape_emoji_name('test"emoji"name')
        assert result == 'test\\"emoji\\"name'

    def test_empty_emoji_name(self):
        """空の絵文字名のテスト"""
        result = escape_emoji_name("")
        assert result == ""
