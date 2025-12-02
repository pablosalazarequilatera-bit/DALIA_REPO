"""
Plantilla general para procesos de limpieza de datos en Python con pandas.

Uso básico desde terminal:

    python data_cleaning_template.py --input ruta/al/archivo.csv --output salida/archivo_limpio.csv

También puedes importar las funciones desde otro script:

    from data_cleaning_template import (
        load_data, standardize_column_names, basic_info,
        drop_full_null_columns, handle_missing_values,
        handle_duplicates, handle_outliers_iqr
    )
"""

import argparse
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple


# =========================
# 1. Carga y exploración
# =========================

def load_data(
    path: str,
    sep: str = ",",
    encoding: str = "utf-8",
    decimal: str = ".",
) -> pd.DataFrame:
    """Carga un CSV en un DataFrame."""
    df = pd.read_csv(path, sep=sep, encoding=encoding, decimal=decimal)
    return df


def basic_info(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """Imprime información general del DataFrame."""
    print(f"\n=== Info básica: {name} ===")
    print(f"Filas: {df.shape[0]}, Columnas: {df.shape[1]}")
    print("\nTipos de datos:")
    print(df.dtypes)
    print("\nPrimeras filas:")
    print(df.head())
    print("\nEstadísticos descriptivos (numéricos):")
    print(df.describe())


# =========================
# 2. Limpieza de columnas
# =========================

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza nombres de columnas:
    - Minúsculas
    - Quita espacios al inicio/fin
    - Reemplaza espacios y caracteres raros por '_'
    """
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.normalize("NFKD")  # quita tildes
        .str.encode("ascii", errors="ignore")
        .str.decode("utf-8")
        .str.replace(r"[^0-9a-zA-Z]+", "_", regex=True)
    )
    return df


def drop_full_null_columns(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Elimina columnas que son 100% nulas."""
    df = df.copy()
    null_cols = df.columns[df.isna().all()].tolist()
    if verbose and null_cols:
        print(f"Columnas completamente nulas eliminadas: {null_cols}")
    df = df.drop(columns=null_cols)
    return df


# =========================
# 3. Valores faltantes
# =========================

def missing_values_report(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve un resumen de valores faltantes por columna."""
    total = df.isna().sum()
    perc = df.isna().mean() * 100
    report = pd.DataFrame({"n_null": total, "pct_null": perc})
    report = report[report["n_null"] > 0].sort_values("pct_null", ascending=False)
    return report


def handle_missing_values(
    df: pd.DataFrame,
    numeric_strategy: str = "median",
    categorical_strategy: str = "mode",
    max_missing_pct: float = 0.9,
) -> pd.DataFrame:
    """
    Maneja valores faltantes con estrategias simples.

    numeric_strategy: 'mean', 'median' o 'zero'
    categorical_strategy: 'mode' o 'constant'
    max_missing_pct: elimina columnas con % nulos mayor a este valor.
    """
    df = df.copy()

    # 1) Eliminar columnas con demasiados nulos
    missing_pct = df.isna().mean()
    cols_to_drop = missing_pct[missing_pct > max_missing_pct].index.tolist()
    if cols_to_drop:
        print(f"Eliminando columnas con > {max_missing_pct*100:.1f}% nulos: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)

    # 2) Separar numéricas y categóricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns

    # 3) Imputación numérica
    for col in numeric_cols:
        if df[col].isna().any():
            if numeric_strategy == "mean":
                value = df[col].mean()
            elif numeric_strategy == "median":
                value = df[col].median()
            elif numeric_strategy == "zero":
                value = 0
            else:
                raise ValueError("numeric_strategy debe ser 'mean', 'median' o 'zero'")
            df[col].fillna(value, inplace=True)

    # 4) Imputación categórica
    for col in categorical_cols:
        if df[col].isna().any():
            if categorical_strategy == "mode":
                value = df[col].mode(dropna=True)
                value = value.iloc[0] if not value.empty else "missing"
            elif categorical_strategy == "constant":
                value = "missing"
            else:
                raise ValueError("categorical_strategy debe ser 'mode' o 'constant'")
            df[col].fillna(value, inplace=True)

    return df


# =========================
# 4. Duplicados y tipos
# =========================

def handle_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None, keep: str = "first") -> pd.DataFrame:
    """
    Elimina filas duplicadas.

    subset: lista de columnas a considerar para definir duplicado.
    keep: 'first', 'last' o False (elimina todos los duplicados).
    """
    df = df.copy()
    before = df.shape[0]
    df = df.drop_duplicates(subset=subset, keep=keep)
    after = df.shape[0]
    print(f"Duplicados eliminados: {before - after}")
    return df


def convert_types_auto(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte tipos automáticamente usando pandas.convert_dtypes."""
    df = df.copy()
    df = df.convert_dtypes()
    return df


def convert_to_datetime(
    df: pd.DataFrame,
    columns: List[str],
    dayfirst: bool = True,
    errors: str = "coerce",
) -> pd.DataFrame:
    """Convierte columnas especificadas a datetime."""
    df = df.copy()
    for col in columns:
        df[col] = pd.to_datetime(df[col], dayfirst=dayfirst, errors=errors)
    return df


# =========================
# 5. Outliers (básico)
# =========================

def outlier_bounds_iqr(series: pd.Series, factor: float = 1.5) -> Tuple[float, float]:
    """Calcula límites inferior y superior usando IQR."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return lower, upper


def handle_outliers_iqr(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    factor: float = 1.5,
    method: str = "cap",
) -> pd.DataFrame:
    """
    Manejo simple de outliers con IQR.

    method:
        - 'cap': recorta valores por debajo/encima de los límites.
        - 'remove': elimina filas con outliers.
        - 'none': solo imprime conteo.
    """
    df = df.copy()
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in numeric_cols:
        s = df[col]
        lower, upper = outlier_bounds_iqr(s, factor=factor)
        mask_outliers = (s < lower) | (s > upper)
        n_outliers = mask_outliers.sum()
        print(f"Columna '{col}': {n_outliers} outliers")

        if method == "cap" and n_outliers > 0:
            df.loc[s < lower, col] = lower
            df.loc[s > upper, col] = upper
        elif method == "remove" and n_outliers > 0:
            df = df[~mask_outliers]

    return df


# =========================
# 6. Flujo principal (ejemplo)
# =========================

def clean_dataset(
    path_in: str,
    path_out: Optional[str] = None,
    sep: str = ",",
    encoding: str = "utf-8",
) -> pd.DataFrame:
    """
    Pipeline general de limpieza:
    1. Carga
    2. Estandariza nombres de columnas
    3. Info básica
    4. Elimina columnas 100% nulas
    5. Reporta nulos
    6. Maneja nulos (num/cat)
    7. Elimina duplicados
    8. Convierte tipos automáticamente
    9. Manejo sencillo de outliers (cap)
    """
    # 1) Carga
    df = load_data(path_in, sep=sep, encoding=encoding)

    # 2) Nombres de columnas
    df = standardize_column_names(df)

    # 3) Info antes de limpiar
    basic_info(df, name="Antes de limpiar")

    # 4) Eliminar columnas totalmente nulas
    df = drop_full_null_columns(df)

    # 5) Reporte de nulos
    print("\n=== Valores faltantes por columna ===")
    report = missing_values_report(df)
    if report.empty:
        print("No hay valores faltantes.")
    else:
        print(report)

    # 6) Manejo de valores faltantes
    df = handle_missing_values(df)

    # 7) Duplicados
    df = handle_duplicates(df)

    # 8) Tipos de datos
    df = convert_types_auto(df)

    # 9) Outliers (cap)
    df = handle_outliers_iqr(df, method="cap")

    # Info final
    basic_info(df, name="Después de limpiar")

    # 10) Guardar
    if path_out is not None:
        df.to_csv(path_out, index=False)
        print(f"\nArchivo limpio guardado en: {path_out}")

    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline general de limpieza de datos (CSV).")
    parser.add_argument("--input", "-i", required=True, help="Ruta del archivo CSV de entrada")
    parser.add_argument("--output", "-o", required=False, help="Ruta del archivo CSV de salida limpio")
    parser.add_argument("--sep", default=",", help="Separador del CSV (por defecto ',')")
    parser.add_argument("--encoding", default="utf-8", help="Encoding del archivo (por defecto 'utf-8')")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    clean_dataset(
        path_in=args.input,
        path_out=args.output,
        sep=args.sep,
        encoding=args.encoding,
    )
