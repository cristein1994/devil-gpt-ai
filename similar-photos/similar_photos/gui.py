"""Minimal tkinter GUI for similar-photos (stdlib on most Linux desktops)."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .gen import generate_similar
from .source import report_json, search_sources


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("similar-photos — 3 parecidas + origem")
        self.geometry("720x560")
        self.image_path: Path | None = None
        self.out_dir = Path.home() / "similar-photos-out"

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Imagem:").grid(row=0, column=0, sticky="w")
        self.path_var = tk.StringVar(value="(nenhuma)")
        ttk.Label(frm, textvariable=self.path_var, wraplength=480).grid(
            row=0, column=1, sticky="w", padx=8
        )
        ttk.Button(frm, text="Escolher…", command=self.pick).grid(row=0, column=2)

        self.local_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frm,
            text="Só local (PIL) — desmarque se tiver OPENAI_API_KEY",
            variable=self.local_var,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=6)

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, columnspan=3, sticky="w", pady=8)
        ttk.Button(btns, text="Gerar 3 parecidas", command=self.do_gen).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Buscar origem/fóruns", command=self.do_source).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btns, text="Fazer os dois", command=self.do_both).pack(side=tk.LEFT, padx=4)

        self.status = tk.StringVar(value="Pronto.")
        ttk.Label(frm, textvariable=self.status).grid(row=3, column=0, columnspan=3, sticky="w")

        self.log = scrolledtext.ScrolledText(frm, height=22, wrap=tk.WORD)
        self.log.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=8)
        frm.rowconfigure(4, weight=1)
        frm.columnconfigure(1, weight=1)

    def pick(self) -> None:
        path = filedialog.askopenfilename(
            title="Escolher foto",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("Todos", "*.*"),
            ],
        )
        if path:
            self.image_path = Path(path)
            self.path_var.set(path)

    def _need_image(self) -> Path | None:
        if not self.image_path or not self.image_path.is_file():
            messagebox.showwarning("Falta imagem", "Escolha uma foto primeiro.")
            return None
        return self.image_path

    def _append(self, text: str) -> None:
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def _run(self, title: str, fn) -> None:
        if self._need_image() is None:
            return

        def worker() -> None:
            self.status.set(title)
            try:
                fn()
                self.status.set("Concluído.")
            except Exception as exc:  # noqa: BLE001
                self.status.set("Erro.")
                self.after(0, lambda: messagebox.showerror("Erro", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def do_gen(self) -> None:
        def job() -> None:
            assert self.image_path
            out = self.out_dir / self.image_path.stem
            paths = generate_similar(
                self.image_path, out, n=3, prefer_api=not self.local_var.get()
            )
            lines = [f"Saída: {out}"] + [f"  • {p}" for p in paths]
            self.after(0, lambda: self._append("\n".join(lines)))

        self._run("Gerando parecidas…", job)

    def do_source(self) -> None:
        def job() -> None:
            assert self.image_path
            report = search_sources(self.image_path, open_browsers=False)
            text = report_json(report)
            self.after(0, lambda: self._append(text))

        self._run("Buscando origem…", job)

    def do_both(self) -> None:
        def job() -> None:
            assert self.image_path
            out = self.out_dir / self.image_path.stem
            paths = generate_similar(
                self.image_path, out, n=3, prefer_api=not self.local_var.get()
            )
            report = search_sources(self.image_path, open_browsers=False)
            block = (
                f"Saída: {out}\n"
                + "\n".join(f"  • {p}" for p in paths)
                + "\n\n"
                + report_json(report)
            )
            self.after(0, lambda: self._append(block))

        self._run("Gerando + buscando…", job)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
