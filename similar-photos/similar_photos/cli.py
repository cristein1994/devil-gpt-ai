"""CLI entry: similar-photos gen|source|run|gui"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .gen import generate_similar
from .source import report_json, search_sources


def _cmd_gen(args: argparse.Namespace) -> int:
    out = Path(args.out or Path.cwd() / "outputs" / Path(args.image).stem)
    paths = generate_similar(Path(args.image), out, n=args.n, prefer_api=not args.local)
    print(f"Geradas {len(paths)} parecidas em {out}:")
    for p in paths:
        print(f"  {p}")
    return 0


def _cmd_source(args: argparse.Namespace) -> int:
    report = search_sources(Path(args.image), open_browsers=args.open)
    print(report_json(report))
    if not report.hits:
        print("\nNenhum hit automático. Use os browser_helpers do JSON acima.", file=sys.stderr)
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    code = _cmd_gen(args)
    if code != 0:
        return code
    return _cmd_source(args)


def _cmd_gui(_: argparse.Namespace) -> int:
    from .gui import main as gui_main

    gui_main()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="similar-photos",
        description="Gera 3 imagens parecidas e busca páginas/fóruns que hospedam a foto (origem).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="Gera N variações parecidas")
    g.add_argument("image", help="Caminho da imagem de entrada")
    g.add_argument("-o", "--out", help="Pasta de saída")
    g.add_argument("-n", type=int, default=3, help="Quantidade (padrão 3)")
    g.add_argument("--local", action="store_true", help="Força transforms locais (sem OpenAI)")
    g.set_defaults(func=_cmd_gen)

    s = sub.add_parser("source", help="Busca origem/fóruns do arquivo")
    s.add_argument("image", help="Caminho da imagem")
    s.add_argument("--open", action="store_true", help="Abre helpers no navegador")
    s.set_defaults(func=_cmd_source)

    r = sub.add_parser("run", help="gen + source")
    r.add_argument("image")
    r.add_argument("-o", "--out")
    r.add_argument("-n", type=int, default=3)
    r.add_argument("--local", action="store_true")
    r.add_argument("--open", action="store_true")
    r.set_defaults(func=_cmd_run)

    ui = sub.add_parser("gui", help="Abre o app gráfico Linux")
    ui.set_defaults(func=_cmd_gui)
    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
