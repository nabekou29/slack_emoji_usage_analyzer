"""Slack APIクライアントのテスト"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from slack_sdk.errors import SlackApiError

# テスト対象のインポート
from emoji_usage.slack_client import (
    _respect_interval,
    search_messages_safe,
    get_custom_emojis,
    get_workspace_info,
)


class TestRateControl:
    """レート制御のテスト"""

    @patch("emoji_usage.slack_client.settings")
    @patch("emoji_usage.slack_client.time")
    def test_respect_interval_enforces_minimum_wait(self, mock_time, mock_settings):
        """最小待機時間が守られることをテスト"""
        mock_settings.min_interval_sec = 5.0
        mock_time.perf_counter.side_effect = [100.0, 102.0]  # 2秒経過

        _respect_interval()

        # 3秒待機すべき（5.0 - 2.0 = 3.0）
        mock_time.sleep.assert_called_once_with(3.0)

    @patch("emoji_usage.slack_client.settings")
    @patch("emoji_usage.slack_client.time")
    def test_respect_interval_no_wait_when_enough_time_passed(
        self, mock_time, mock_settings
    ):
        """十分な時間が経過している場合は待機しないことをテスト"""
        mock_settings.min_interval_sec = 5.0
        mock_time.perf_counter.side_effect = [100.0, 106.0]  # 6秒経過

        _respect_interval()

        # 待機しない
        mock_time.sleep.assert_not_called()


class TestSearchMessagesSafe:
    """メッセージ検索のテスト"""

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_successful_search(self, mock_client, mock_respect_interval):
        """正常な検索のテスト"""
        mock_response = {"messages": {"total": 42, "matches": []}}
        mock_client.search_messages.return_value = mock_response

        result = search_messages_safe("test query")

        assert result == 42
        mock_client.search_messages.assert_called_once_with(query="test query", count=1)
        mock_respect_interval.assert_called_once()

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_search_with_none_response(self, mock_client, mock_respect_interval):
        """レスポンスがNoneの場合のテスト"""
        mock_client.search_messages.return_value = None

        result = search_messages_safe("test query")

        assert result == 0

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_search_with_empty_messages(self, mock_client, mock_respect_interval):
        """messagesが空の場合のテスト"""
        mock_response = {"messages": None}
        mock_client.search_messages.return_value = mock_response

        result = search_messages_safe("test query")

        assert result == 0

    @patch("emoji_usage.slack_client.settings")
    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    @patch("emoji_usage.slack_client.time.sleep")
    def test_429_retry_success(
        self, mock_sleep, mock_client, mock_respect_interval, mock_settings
    ):
        """429エラーのリトライが成功するテスト"""
        mock_settings.max_retry = 3

        # 1回目: 429エラー、2回目: 成功
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "2"}

        mock_response_success = {"messages": {"total": 10}}

        mock_client.search_messages.side_effect = [
            SlackApiError("Rate limited", mock_response_429),
            mock_response_success,
        ]

        result = search_messages_safe("test query")

        assert result == 10
        mock_sleep.assert_called_once_with(3)  # Retry-After + 1
        assert mock_client.search_messages.call_count == 2

    @patch("emoji_usage.slack_client.settings")
    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    @patch("emoji_usage.slack_client.time.sleep")
    def test_429_retry_failure(
        self, mock_sleep, mock_client, mock_respect_interval, mock_settings
    ):
        """429エラーのリトライが失敗するテスト"""
        mock_settings.max_retry = 2

        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        mock_client.search_messages.side_effect = [
            SlackApiError("Rate limited", mock_response_429),
            SlackApiError("Rate limited", mock_response_429),
        ]

        result = search_messages_safe("test query")

        assert result == 0
        assert mock_client.search_messages.call_count == 2
        assert mock_sleep.call_count == 2

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_non_429_error_propagation(self, mock_client, mock_respect_interval):
        """429以外のエラーが正しく伝播されることをテスト"""
        mock_response_error = Mock()
        mock_response_error.status_code = 403

        mock_client.search_messages.side_effect = SlackApiError(
            "Forbidden", mock_response_error
        )

        with pytest.raises(SlackApiError):
            search_messages_safe("test query")


class TestGetCustomEmojis:
    """カスタム絵文字取得のテスト"""

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_successful_emoji_fetch(self, mock_client, mock_respect_interval):
        """正常な絵文字取得のテスト"""
        mock_response = {
            "ok": True,
            "emoji": {
                "custom1": "https://example.com/custom1.png",
                "custom2": "https://example.com/custom2.gif",
            },
        }
        mock_client.emoji_list.return_value = mock_response

        result = get_custom_emojis()

        assert len(result) == 2
        assert {"name": "custom1", "url": "https://example.com/custom1.png"} in result
        assert {"name": "custom2", "url": "https://example.com/custom2.gif"} in result

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_empty_emoji_list(self, mock_client, mock_respect_interval):
        """空の絵文字リストのテスト"""
        mock_response = {"ok": True, "emoji": {}}
        mock_client.emoji_list.return_value = mock_response

        result = get_custom_emojis()

        assert result == []

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_api_error_response(self, mock_client, mock_respect_interval):
        """APIエラーレスポンスのテスト"""
        mock_response = {"ok": False, "error": "invalid_auth"}
        mock_client.emoji_list.return_value = mock_response

        with pytest.raises(SlackApiError):
            get_custom_emojis()


class TestGetWorkspaceInfo:
    """ワークスペース情報取得のテスト"""

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_successful_workspace_info(self, mock_client, mock_respect_interval):
        """正常なワークスペース情報取得のテスト"""
        mock_response = {
            "ok": True,
            "team": {
                "id": "T123456",
                "name": "Test Workspace",
                "domain": "test-workspace",
            },
        }
        mock_client.team_info.return_value = mock_response

        result = get_workspace_info()

        assert result and result["name"] == "Test Workspace"
        assert result and result["id"] == "T123456"
        assert result and result["domain"] == "test-workspace"

    @patch("emoji_usage.slack_client._respect_interval")
    @patch("emoji_usage.slack_client.client")
    def test_workspace_info_failure_returns_none(
        self, mock_client, mock_respect_interval
    ):
        """エラー時はNoneを返す"""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}

        mock_client.team_info.side_effect = SlackApiError(
            "Rate limited", mock_response_429
        )

        result = get_workspace_info()

        assert result is None
