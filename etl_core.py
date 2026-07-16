import re

import pandas as pd

SIIGO_HEADER_MARKERS = [
    "Código cuentas contables",
    "Comprobante",
    "Fecha elaboración",
    "Identificación tercero",
]

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

COMPROBANTE_EGRESOS = "2"
CUENTA_PROVEEDORES = "220515"


def parsear_comprobante(valor: str) -> tuple[str, str, str]:
    parts = str(valor).split("-")
    if len(parts) != 3:
        raise ValueError(
            f"Formato inesperado: '{valor}' (se esperan 3 partes separadas por '-')"
        )
    return parts[0].strip(), parts[1].strip(), parts[2].strip()


def _extraer_ref_de_detalle(detalle: str) -> str:
    detalle = str(detalle).strip()
    if " Cuota:" in detalle:
        return detalle.split(" Cuota:")[0].strip()
    match = re.match(r"^([A-Za-z]+-?\d[\w-]*)", detalle)
    if match:
        return match.group(1)
    return ""


def _detectar_header(df_raw: pd.DataFrame) -> int:
    for i, row in df_raw.iterrows():
        valores = [str(v).strip() for v in row.values]
        coincidencias = sum(1 for m in SIIGO_HEADER_MARKERS if m in valores)
        if coincidencias >= 3:
            return i
    raise ValueError(
        "No se encontró la fila de encabezados. "
        f"Se buscaron al menos 3 de: {SIIGO_HEADER_MARKERS}"
    )


def _leer_siigo(ruta: str) -> pd.DataFrame:
    df_raw = pd.read_excel(ruta, header=None)
    header_row = _detectar_header(df_raw)
    df = pd.read_excel(ruta, header=header_row)
    df = df.dropna(how="all")
    df = df[df["Código cuentas contables"].notna()]
    return df.reset_index(drop=True)


def transformar_siigo_contai(
    ruta_entrada: str, ruta_salida: str
) -> tuple[bool, str]:
    try:
        df = _leer_siigo(ruta_entrada)
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error al abrir el archivo: {e}"

    filas_ok = []
    advertencias = []

    for i, row in df.iterrows():
        try:
            prefix, comprobante, docnum = parsear_comprobante(row["Comprobante"])
        except ValueError as e:
            advertencias.append(f"Fila {i + 1}: {e}")
            continue

        debito = pd.to_numeric(row.get("Débito", 0), errors="coerce")
        credito = pd.to_numeric(row.get("Crédito", 0), errors="coerce")
        debito = 0.0 if pd.isna(debito) else float(debito)
        credito = 0.0 if pd.isna(credito) else float(credito)

        if debito == 0 and credito == 0:
            advertencias.append(f"Fila {i + 1}: Débito y Crédito ambos vacíos o cero")
            continue
        if debito != 0 and credito != 0:
            advertencias.append(f"Fila {i + 1}: Débito y Crédito ambos con valor")
            continue

        tipo = 1 if debito != 0 else 2
        valor = debito if debito != 0 else credito
        cuenta = str(row["Código cuentas contables"]).strip()
        es_egreso = comprobante == COMPROBANTE_EGRESOS

        if es_egreso:
            docum = docnum
            if cuenta == CUENTA_PROVEEDORES:
                doc_ref = _extraer_ref_de_detalle(row.get("Descripción", ""))
                if not doc_ref:
                    advertencias.append(
                        f"Fila {i + 1}: No se pudo extraer referencia de factura "
                        f"del Detalle para cuenta {CUENTA_PROVEEDORES}"
                    )
                    doc_ref = docnum
            else:
                doc_ref = docnum
        else:
            docum = f"{prefix}-{docnum}"
            doc_ref = docum

        filas_ok.append({
            "Cuenta": cuenta,
            "Comprobante": comprobante,
            "Fecha(mm/dd/yyyy)": pd.to_datetime(
                row["Fecha elaboración"]
            ).strftime("%m/%d/%Y"),
            "Docum": docum,
            "Documento Ref.": doc_ref,
            "NIT": str(int(float(row["Identificación tercero"]))),
            "Detalle": row.get("Descripción", ""),
            "Tipo": tipo,
            "Valor": valor,
            "Base": 0,
            "Plazo": 0,
        })

    if not filas_ok:
        msg = "No se procesaron filas válidas."
        if advertencias:
            msg += "\n" + "\n".join(advertencias)
        return False, msg

    result = pd.DataFrame(filas_ok)[CONTAI_COLUMNS]
    result.to_excel(ruta_salida, index=False)

    msg = f"{len(filas_ok)} registros exportados."
    if advertencias:
        msg += f" {len(advertencias)} filas con advertencias:\n" + "\n".join(advertencias)

    return True, msg
