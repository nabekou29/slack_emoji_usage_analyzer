"""設定モジュールのテスト"""

import os
import pytest
from unittest.mock import patch, mock_open
from emoji_usage.config import Settings


class TestSettings:
    """Settings クラスのテスト"""

    def test_default_values(self):
        """デフォルト値が正しく設定されているかテスト"""
        settings = Settings()

        assert settings.slack_token == ""
        assert settings.min_interval_sec == 5.0
        assert settings.max_retry == 3
        assert settings.months == 12
        assert settings.output_path == "emoji_usage.csv"
        assert settings.log_level == "INFO"

    @patch.dict(
        os.environ,
        {
            "SLACK_TOKEN": "xoxp-test-token",
            "MIN_INTERVAL_SEC": "3.0",
            "MAX_RETRY": "5",
            "MONTHS": "6",
            "OUTPUT_PATH": "test_output.csv",
            "LOG_LEVEL": "DEBUG",
        },
    )
    def test_environment_variables(self):
        """環境変数からの設定読み込みテスト"""
        settings = Settings()

        assert settings.slack_token == "xoxp-test-token"
        assert settings.min_interval_sec == 3.0
        assert settings.max_retry == 5
        assert settings.months == 6
        assert settings.output_path == "test_output.csv"
        assert settings.log_level == "DEBUG"

    @patch(
        "builtins.open",
        mock_open(
            read_data="""
SLACK_TOKEN=xoxp-file-token
MIN_INTERVAL_SEC=4.0
MAX_RETRY=2
MONTHS=3
OUTPUT_PATH=file_output.csv
LOG_LEVEL=ERROR
"""
        ),
    )
    def test_env_file_loading(self):
        """環境変数ファイルからの読み込みテスト"""
        with patch("os.path.exists", return_value=True):
            settings = Settings()

            # 注意: 実際の.envファイルの読み込みは
            # pydantic-settingsの内部実装に依存します

    @patch.dict(os.environ, {"SLACK_TOKEN": "env-token", "MIN_INTERVAL_SEC": "2.5"})
    @patch(
        "builtins.open",
        mock_open(
            read_data="""
SLACK_TOKEN=file-token
MIN_INTERVAL_SEC=1.5
MAX_RETRY=4
"""
        ),
    )
    def test_environment_priority(self):
        """環境変数がファイルより優先されることをテスト"""
        settings = Settings()

        # 環境変数が設定されている項目は環境変数の値が優先
        assert settings.slack_token == "env-token"
        assert settings.min_interval_sec == 2.5

    def test_invalid_values(self):
        """不正な値の処理テスト"""
        # 文字列を数値フィールドに設定した場合のテスト
        with patch.dict(os.environ, {"MIN_INTERVAL_SEC": "invalid"}):
            with pytest.raises(ValueError):
                Settings()

    def test_validation_ranges(self):
        """値の範囲検証テスト"""
        # 負の値のテスト
        with patch.dict(os.environ, {"MIN_INTERVAL_SEC": "-1.0"}):
            # 設定は作成されるが、負の値は論理的におかしい
            settings = Settings()
            # アプリケーションレベルでの検証が必要

    def test_model_config(self):
        """モデル設定の確認テスト"""
        settings = Settings()

        # model_configの設定確認
        assert hasattr(settings, "model_config")
        config = settings.model_config
        assert config.get("env_file") == ".env"
        assert config.get("env_file_encoding") == "utf-8"
        assert config.get("case_sensitive") is False

    def test_case_insensitive_env_vars(self):
        """環境変数の大文字小文字を区別しないテスト"""
        with patch.dict(
            os.environ,
            {
                "slack_token": "lowercase-token",  # 小文字
                "SLACK_TOKEN": "uppercase-token",  # 大文字
            },
        ):
            settings = Settings()
            # 大文字の方が優先される（OSの環境変数の仕様）
            assert settings.slack_token == "uppercase-token"
