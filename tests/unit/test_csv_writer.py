"""CSV出力モジュールのテスト"""

import os
import tempfile
from pathlib import Path
import pytest
from emoji_usage.csv_writer import (
    write_csv,
    _write_pivot_csv,
    _convert_to_pivot,
    validate_output_path,
    validate_csv_records,
    read_csv,
)


class TestWriteCSV:
    """write_csv関数のテスト"""

    def test_pivot_format_output(self):
        """ピボット形式での出力テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_pivot.csv")

            # テストデータ
            records = [
                ["smile", "2023-01", 10],
                ["smile", "2023-02", 15],
                ["heart", "2023-01", 5],
                ["heart", "2023-02", 8],
            ]

            # ピボット形式で出力
            write_csv(records, output_path)

            # ファイルが作成されていることを確認
            assert os.path.exists(output_path)

            # 内容の確認
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # ヘッダーに絵文字、期間、統計が含まれているか確認
            assert "emoji" in content
            assert "2023-01" in content
            assert "2023-02" in content
            assert "total" in content
            assert "average" in content

    def test_empty_records(self):
        """空のレコードのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_empty.csv")

            records = []
            write_csv(records, output_path)

            assert os.path.exists(output_path)

    def test_period_format_records(self):
        """期間形式のレコードのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_period.csv")

            records = [
                ["thumbsup", "2023-01 to 2023-03", 25],
                ["thumbsup", "2023-04 to 2023-06", 30],
                ["wave", "2023-01 to 2023-03", 15],
                ["wave", "2023-04 to 2023-06", 20],
            ]

            write_csv(records, output_path)

            assert os.path.exists(output_path)

            # 内容の確認
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "2023-01 to 2023-03" in content
            assert "2023-04 to 2023-06" in content


class TestConvertToPivot:
    """_convert_to_pivot関数のテスト"""

    def test_monthly_records_conversion(self):
        """月次レコードの変換テスト"""
        records = [
            ["smile", "2023-01", 10],
            ["smile", "2023-02", 15],
            ["heart", "2023-01", 5],
        ]

        result = _convert_to_pivot(records)

        assert "data" in result
        assert "periods" in result
        assert "smile" in result["data"]
        assert "heart" in result["data"]
        assert "2023-01" in result["periods"]
        assert "2023-02" in result["periods"]

        # データの内容確認
        assert result["data"]["smile"]["2023-01"] == 10
        assert result["data"]["smile"]["2023-02"] == 15
        assert result["data"]["heart"]["2023-01"] == 5

    def test_period_records_conversion(self):
        """期間レコードの変換テスト"""
        records = [
            ["thumbsup", "2023-01 to 2023-03", 25],
            ["wave", "2023-01 to 2023-03", 15],
        ]

        result = _convert_to_pivot(records)

        assert result["data"]["thumbsup"]["2023-01 to 2023-03"] == 25
        assert result["data"]["wave"]["2023-01 to 2023-03"] == 15
        assert "2023-01 to 2023-03" in result["periods"]

    def test_invalid_records_handling(self):
        """無効なレコードの処理テスト"""
        records = [
            ["smile", "2023-01", 10],
            ["incomplete"],  # 不完全なレコード
            ["heart", "2023-01", "invalid"],  # 無効な使用回数
        ]

        result = _convert_to_pivot(records)

        # 有効なレコードのみが処理されること
        assert "smile" in result["data"]
        assert "incomplete" not in result["data"]
        assert "heart" not in result["data"]

    def test_empty_records(self):
        """空のレコードのテスト"""
        records = []

        result = _convert_to_pivot(records)

        assert result["data"] == {}
        assert result["periods"] == set()


class TestValidateOutputPath:
    """validate_output_path関数のテスト"""

    def test_valid_path(self):
        """有効なパスのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.csv")
            assert validate_output_path(output_path) is True

    def test_empty_path(self):
        """空のパスのテスト"""
        assert validate_output_path("") is False
        assert validate_output_path(None) is False

    def test_create_directory(self):
        """ディレクトリ作成のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "new_subdir")
            output_path = os.path.join(new_dir, "test.csv")

            # ディレクトリが存在しないが、作成されるはず
            assert not os.path.exists(new_dir)
            assert validate_output_path(output_path) is True
            assert os.path.exists(new_dir)


class TestValidateCSVRecords:
    """validate_csv_records関数のテスト"""

    def test_valid_records(self):
        """有効なレコードのテスト"""
        records = [
            ["smile", "2023-01", "10"],
            ["heart", "2023-02", "5"],
        ]

        result = validate_csv_records(records)

        assert len(result) == 2
        assert result[0] == ["smile", "2023-01", "10"]
        assert result[1] == ["heart", "2023-02", "5"]

    def test_invalid_length_records(self):
        """不正な長さのレコードのテスト"""
        records = [
            ["smile", "2023-01", "10"],  # 有効
            ["incomplete"],  # 不正な長さ
            ["too", "many", "fields", "here"],  # 不正な長さ
        ]

        result = validate_csv_records(records)

        assert len(result) == 1
        assert result[0] == ["smile", "2023-01", "10"]

    def test_invalid_usage_count(self):
        """不正な使用回数のテスト"""
        records = [
            ["smile", "2023-01", "10"],  # 有効
            ["heart", "2023-01", "invalid"],  # 不正な使用回数
            ["wave", "2023-01", "-5"],  # 負の値
        ]

        result = validate_csv_records(records)

        assert len(result) == 1
        assert result[0] == ["smile", "2023-01", "10"]

    def test_invalid_period_format(self):
        """不正な期間フォーマットのテスト"""
        records = [
            ["smile", "2023-01", "10"],  # 有効
            ["heart", "invalid-period", "5"],  # 不正な期間
        ]

        result = validate_csv_records(records)

        assert len(result) == 1
        assert result[0] == ["smile", "2023-01", "10"]

    def test_period_range_format(self):
        """期間範囲フォーマットのテスト"""
        records = [
            ["thumbsup", "2023-01 to 2023-03", "25"],  # 有効な期間範囲
            ["wave", "2023-04 to 2023-06", "20"],  # 有効な期間範囲
        ]

        result = validate_csv_records(records)

        assert len(result) == 2
        assert result[0] == ["thumbsup", "2023-01 to 2023-03", "25"]
        assert result[1] == ["wave", "2023-04 to 2023-06", "20"]


class TestReadCSV:
    """read_csv関数のテスト"""

    def test_read_existing_file(self):
        """既存ファイルの読み込みテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, "test.csv")

            # テストファイルを作成
            test_data = [
                ["smile", "2023-01", 10],
                ["heart", "2023-02", 5],
            ]
            write_csv(test_data, csv_path)

            # ファイルを読み込み
            result = read_csv(csv_path)

            # ヘッダーはスキップされるので、データ行のみが返される
            assert len(result) >= 2

    def test_read_nonexistent_file(self):
        """存在しないファイルの読み込みテスト"""
        with pytest.raises(Exception):
            read_csv("/nonexistent/path/file.csv")

