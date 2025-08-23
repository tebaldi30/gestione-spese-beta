# utils/helpers.py

def format_currency(value):
    """
    Formatta un numero in stile italiano: 1.200,00 €
    """
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def clean_importo(series):
    """
    Converte una serie di importi (stringhe) in numeri float
    rimuovendo simboli €, punti e virgole.
    """
    import pandas as pd
    return pd.to_numeric(
        series.astype(str)
        .str.replace("€", "")
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip(),
        errors="coerce"
    )
