import pandas as pd


CONTAI_COLUMNS = [
    "Cuenta",
    "Comprobante",
    "Fecha(mm/dd/yyyy)",
    "Docum",
    "Documento Ref.",
    "NIT",
    "Detalle",
    "Tipo",
    "Valor",
    "Base",
    "Plazo",
]


def _split_documento(serie: pd.Series) -> pd.DataFrame:
    parts = serie.astype(str).str.split("-", expand=True)
    return pd.DataFrame({
        "Comprobante": parts[1] if 1 in parts.columns else "",
        "Docum": parts[2] if 2 in parts.columns else "",
    })


def _format_fecha(serie: pd.Series) -> pd.Series:
    return pd.to_datetime(serie, dayfirst=True).dt.strftime("%m/%d/%Y")


def _clean_nit(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.replace(r"\s+", "", regex=True)


def transformar_siigo_contai(
    ruta_entrada: str, ruta_salida: str
) -> tuple[bool, str]:
    try:
        df = pd.read_excel(ruta_entrada)

        doc_parts = _split_documento(df["Documento"])

        result = pd.DataFrame({
            "Cuenta": df["Cuenta"],
            "Comprobante": doc_parts["Comprobante"],
            "Fecha(mm/dd/yyyy)": _format_fecha(df["Fecha"]),
            "Docum": doc_parts["Docum"],
            "Documento Ref.": df.get("Documento Ref.", ""),
            "NIT": _clean_nit(df["Nit"]),
            "Detalle": df["Detalle"],
            "Tipo": df["Tipo"],
            "Valor": df["Valor"],
            "Base": df.get("Base", 0),
            "Plazo": df.get("Plazo", 0),
        })

        result = result[CONTAI_COLUMNS]
        result.to_csv(ruta_salida, sep="\t", index=False)

        return True, f"{len(result)} registros exportados a {ruta_salida}"

    except KeyError as e:
        return False, f"Columna requerida no encontrada en el archivo: {e}"
    except ValueError as e:
        return False, f"Error en formato de datos: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"
