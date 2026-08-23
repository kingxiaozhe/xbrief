from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from xbrief import __version__
from xbrief.config import load_settings, save_settings
from xbrief.doctor import run_doctor
from xbrief.errors import XBriefError, exit_code_for
from xbrief.models import Outcome
from xbrief.service import prepare as prepare_service

app = typer.Typer(
    name="xbrief",
    help="抓取 X 帖子与可见评论，保存到 Obsidian，并交给当前 Codex 分析。",
    no_args_is_help=True,
    invoke_without_command=True,
)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="显示版本。", is_eager=True),
) -> None:
    if version:
        typer.echo(f"xbrief {__version__}")
        raise typer.Exit()


@app.command()
def configure(
    vault: Annotated[Path, typer.Option("--vault", help="Obsidian Vault 绝对路径。")],
    folder: str = typer.Option("XBrief", "--folder", help="Vault 内输出目录。"),
) -> None:
    resolved = vault.expanduser().resolve()
    if not resolved.is_dir():
        raise typer.BadParameter(f"Vault 不存在：{resolved}")
    settings = load_settings().model_copy(update={"vault_path": resolved, "vault_folder": folder})
    path = save_settings(settings)
    typer.echo(
        json.dumps(
            {"ok": True, "config_path": str(path), "vault": str(resolved)}, ensure_ascii=False
        )
    )


@app.command()
def doctor(json_output: bool = typer.Option(False, "--json", help="输出 JSON。")) -> None:
    result = run_doctor(load_settings())
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for check in result["checks"]:  # type: ignore[index]
            marker = "✓" if check["ok"] else "✗"
            typer.echo(f"{marker} {check['name']}: {check['detail']}")
    if not result["ok"]:
        raise typer.Exit(2)


@app.command()
def prepare(
    url: str = typer.Argument(..., help="完整 X 帖子链接。"),
    json_output: bool = typer.Option(False, "--json", help="stdout 仅输出结果 JSON。"),
    nested: bool | None = typer.Option(
        None, "--nested/--top-level-only", help="是否继续抓取嵌套回复。"
    ),
) -> None:
    try:
        result = prepare_service(url, settings=load_settings(), include_nested=nested)
    except XBriefError as exc:
        payload = {"ok": False, "error_code": exc.code, "message": exc.message}
        typer.echo(json.dumps(payload, ensure_ascii=False) if json_output else exc.message)
        raise typer.Exit(exit_code_for(exc)) from exc
    except Exception as exc:
        payload = {
            "ok": False,
            "error_code": "storage_error",
            "message": "本地存储或产物生成失败。",
        }
        typer.echo(json.dumps(payload, ensure_ascii=False) if json_output else payload["message"])
        raise typer.Exit(6) from exc

    if json_output:
        typer.echo(result.model_dump_json())
    else:
        typer.echo(f"已保存 {result.comments_fetched} 条评论。")
        typer.echo(f"Obsidian：{result.report_path}")
        typer.echo(f"分析任务：{result.analysis_prompt_path}")
    if result.outcome is Outcome.FAILURE:
        raise typer.Exit(5)


if __name__ == "__main__":
    app()
