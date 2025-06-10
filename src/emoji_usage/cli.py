"""CLIエントリポイント"""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress

from .config import Settings
from .logging_cfg import logger
from .aggregator import aggregate_emoji_usage, quick_test_aggregation

# Typerアプリケーションの作成
app = typer.Typer(
    name="emoji-usage",
    help="Slack絵文字利用集計ツール (Rate-Limit Friendly版)",
    add_completion=False,
)

# Rich コンソール
console = Console()

# グローバル設定
settings = Settings()


@app.command()
def main(
    months: Optional[int] = typer.Option(
        None, "--months", "-m", help=f"集計対象月数 (デフォルト: {settings.months})"
    ),
    interval: Optional[int] = typer.Option(
        None,
        "--interval",
        "-i",
        help=f"集計間隔（月数） (デフォルト: {settings.interval_months})",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help=f"出力ファイルパス (デフォルト: {settings.output_path})",
    ),
    # 絵文字タイプ選択オプション
    no_standard: bool = typer.Option(
        False, "--no-standard", help="標準絵文字を除外する（:smile:等）"
    ),
    only_standard: bool = typer.Option(
        False, "--only-standard", help="標準絵文字のみを対象とする（:smile:等）"
    ),
    no_custom: bool = typer.Option(
        False,
        "--no-custom",
        help="カスタム絵文字を除外する（ワークスペース固有の絵文字）",
    ),
    only_custom: bool = typer.Option(
        False,
        "--only-custom",
        help="カスタム絵文字のみを対象とする（ワークスペース固有の絵文字）",
    ),
    max_emojis: Optional[int] = typer.Option(
        None, "--max-emojis", help="処理する絵文字の最大数（テスト用）"
    ),
    log_level: Optional[str] = typer.Option(
        None, "--log-level", help=f"ログレベル (デフォルト: {settings.log_level})"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="詳細ログを表示"),
) -> None:
    """
    Slack絵文字利用状況を集計してCSVに出力する
    """
    try:
        # ログレベルの設定
        if verbose:
            import logging
            from .logging_cfg import logger

            logger.setLevel(logging.DEBUG)
        elif log_level:
            import logging
            from .logging_cfg import logger

            log_level_value = getattr(logging, log_level.upper(), logging.INFO)
            logger.setLevel(log_level_value)

        # パラメータの検証
        if only_standard and only_custom:
            console.print(
                "[red]Error: --only-standard と --only-custom は同時に指定できません[/red]"
            )
            raise typer.Exit(1)

        if only_standard and (no_standard or no_custom):
            console.print(
                "[red]Error: --only-standard は他の除外オプションと同時に指定できません[/red]"
            )
            raise typer.Exit(1)

        if only_custom and (no_standard or no_custom):
            console.print(
                "[red]Error: --only-custom は他の除外オプションと同時に指定できません[/red]"
            )
            raise typer.Exit(1)

        # 絵文字タイプの決定
        if only_standard:
            include_standard = True
            include_custom = False
        elif only_custom:
            include_standard = False
            include_custom = True
        else:
            include_standard = not no_standard
            include_custom = not no_custom

        # 最終検証
        if not include_standard and not include_custom:
            console.print(
                "[red]Error: 標準絵文字とカスタム絵文字の両方を除外することはできません[/red]"
            )
            raise typer.Exit(1)

        # 設定の表示
        target_months = months or settings.months
        target_interval = interval or settings.interval_months
        target_output = output or settings.output_path

        # 間隔の検証
        if target_interval <= 0:
            console.print("[red]Error: 集計間隔は1以上である必要があります[/red]")
            raise typer.Exit(1)

        console.print("[bold blue]Slack絵文字利用集計ツール[/bold blue]")
        console.print(f"集計期間: {target_months}ヶ月")
        console.print(f"集計間隔: {target_interval}ヶ月")
        console.print(f"出力ファイル: {target_output}")
        console.print(f"標準絵文字: {'✓' if include_standard else '✗'}")
        console.print(f"カスタム絵文字: {'✓' if include_custom else '✗'}")
        if max_emojis:
            console.print(f"最大絵文字数: {max_emojis}")
        console.print()

        # 実行確認
        if not typer.confirm("集計を開始しますか？"):
            console.print("集計がキャンセルされました。")
            raise typer.Exit(0)

        # 集計の実行
        console.print("[yellow]集計を開始しています...[/yellow]")

        success = aggregate_emoji_usage(
            months=target_months,
            interval_months=target_interval,
            output_path=target_output,
            include_standard=include_standard,
            include_custom=include_custom,
            max_emojis=max_emojis,
        )

        if success:
            console.print(f"[green]✓ 集計が完了しました: {target_output}[/green]")
            raise typer.Exit(0)
        else:
            console.print("[red]✗ 集計に失敗しました[/red]")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]集計が中断されました[/yellow]")
        raise typer.Exit(1)
    except typer.Exit:
        # typer.Exitは再raiseして、他の例外処理をスキップ
        raise
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        from .logging_cfg import logger

        logger.error(f"CLI error: {e}")
        raise typer.Exit(1)


@app.command("test")
def test_command(
    emoji_count: int = typer.Option(
        5, "--emoji-count", "-e", help="テストする絵文字数"
    ),
    months: int = typer.Option(2, "--months", "-m", help="テストする月数"),
) -> None:
    """
    テスト用の簡易集計を実行する
    """
    try:
        console.print("[bold blue]テスト集計を実行しています...[/bold blue]")
        console.print(f"絵文字数: {emoji_count}")
        console.print(f"月数: {months}")
        console.print()

        success = quick_test_aggregation(emoji_count=emoji_count, months=months)

        if success:
            console.print(
                "[green]✓ テスト集計が完了しました: test_emoji_usage.csv[/green]"
            )
            raise typer.Exit(0)
        else:
            console.print("[red]✗ テスト集計に失敗しました[/red]")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]テスト集計が中断されました[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]エラー: {e}[/red]")
        logger.error(f"Test CLI error: {e}")
        raise typer.Exit(1)


@app.command("config")
def config_command() -> None:
    """
    現在の設定を表示する
    """
    try:
        console.print("[bold blue]現在の設定[/bold blue]")
        console.print(
            f"SLACK_TOKEN: {'設定済み' if settings.slack_token else '未設定'}"
        )
        console.print(f"集計期間: {settings.months}ヶ月")
        console.print(f"出力ファイル: {settings.output_path}")
        console.print(f"API呼び出し間隔: {settings.min_interval_sec}秒")
        console.print(f"最大リトライ回数: {settings.max_retry}回")
        console.print(f"ログレベル: {settings.log_level}")

    except Exception as e:
        console.print(f"[red]設定の表示に失敗しました: {e}[/red]")
        raise typer.Exit(1)


@app.command("version")
def version_command() -> None:
    """
    バージョン情報を表示する
    """
    from . import __version__

    console.print(f"emoji-usage version {__version__}")


def cli() -> None:
    """
    CLI実行用のエントリポイント
    """
    try:
        app()
    except Exception as e:
        console.print(f"[red]予期しないエラーが発生しました: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
