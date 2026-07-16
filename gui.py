import os
from tkinter import filedialog

import customtkinter as ctk

from etl_core import transformar_siigo_contai

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Siigo → ContaI ETL")
        self.geometry("620x480")
        self.resizable(False, False)

        self._ruta_entrada = ctk.StringVar()
        self._ruta_salida = ctk.StringVar()

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": (8, 0)}

        ctk.CTkLabel(self, text="Archivo Excel de Siigo (.xlsx)").grid(
            row=0, column=0, columnspan=2, sticky="w", **pad
        )
        ctk.CTkEntry(self, textvariable=self._ruta_entrada, width=440).grid(
            row=1, column=0, padx=(16, 4), pady=4, sticky="w"
        )
        ctk.CTkButton(self, text="Buscar", width=100, command=self._select_file).grid(
            row=1, column=1, padx=(4, 16), pady=4
        )

        ctk.CTkLabel(self, text="Carpeta de salida").grid(
            row=2, column=0, columnspan=2, sticky="w", **pad
        )
        ctk.CTkEntry(self, textvariable=self._ruta_salida, width=440).grid(
            row=3, column=0, padx=(16, 4), pady=4, sticky="w"
        )
        ctk.CTkButton(self, text="Buscar", width=100, command=self._select_folder).grid(
            row=3, column=1, padx=(4, 16), pady=4
        )

        ctk.CTkButton(
            self, text="Procesar", height=40, command=self._process
        ).grid(row=4, column=0, columnspan=2, pady=16)

        self._log = ctk.CTkTextbox(self, width=588, height=220, state="disabled")
        self._log.grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 16))

    def _select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if path:
            self._ruta_entrada.set(path)
            if not self._ruta_salida.get():
                self._ruta_salida.set(os.path.dirname(path))

    def _select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self._ruta_salida.set(path)

    def _append_log(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _process(self):
        entrada = self._ruta_entrada.get().strip()
        salida_dir = self._ruta_salida.get().strip()

        if not entrada or not salida_dir:
            self._append_log("[ERROR] Seleccioná el archivo de entrada y la carpeta de salida.")
            return

        nombre = os.path.splitext(os.path.basename(entrada))[0]
        salida = os.path.join(salida_dir, f"{nombre}_contai.xlsx")

        self._append_log(f"Procesando: {entrada}")
        ok, msg = transformar_siigo_contai(entrada, salida)
        prefix = "[OK]" if ok else "[ERROR]"
        self._append_log(f"{prefix} {msg}")


if __name__ == "__main__":
    App().mainloop()
