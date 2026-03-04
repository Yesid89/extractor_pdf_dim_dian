import streamlit as st
import fitz
import re
import pandas as pd
from io import BytesIO


# =========================
# FUNCION REUTILIZABLE
# =========================
def extraer_casilla_por_texto(page, etiqueta):
    texto = page.get_text("text")
    patron = rf"{re.escape(etiqueta)}\s*\n(.+)"
    match = re.search(patron, texto)

    if match:
        #return match.group(1).strip()
        valor = match.group(1).strip()

        # 🔹 Limpiar prefijos tipo No., N°, No:
        valor = re.sub(r"^(No\.?|N°)\s*", "", valor)

        return valor.strip()

    return None

def extraer_casilla_por_texto2(page, etiqueta):
    texto = page.get_text("text")

    # 1️⃣ Intentar cuando está en la misma línea
    patron_misma = rf"{re.escape(etiqueta)}\s*(.*?)\s+\d{{1,3}}\s*\."
    match = re.search(patron_misma, texto)

    if not match:
        # 2️⃣ Intentar cuando está en la línea siguiente
        patron_siguiente = rf"{re.escape(etiqueta)}\s*\n(.*)"
        match = re.search(patron_siguiente, texto)

    if match:
        valor = match.group(1).strip()

        # 🔹 Limpiar prefijos tipo No., N°, etc.
        valor = re.sub(r"^(No\.?|N°)\s*", "", valor)

        # 🔹 Si hay números dentro, extraer solo números
        numero = re.search(r"[\d-]+", valor)
        if numero:
            return numero.group()

        return valor.strip()

    return None

# =========================
# INTERFAZ STREAMLIT
# =========================
st.title("Extractor DIM - (Multi PDF)")

uploaded_files = st.file_uploader(
    "Subir uno o varios PDFs Declaración de Importación",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    datos = []

    for uploaded_file in uploaded_files:

        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

        for i, page in enumerate(doc):

            casilla_4 = extraer_casilla_por_texto2(
                page,
                "4. Número de formulario"
            )

            casilla_42 = extraer_casilla_por_texto(
                page,
                "42 . Manifiesto de carga"
            )

            casilla_59 = extraer_casilla_por_texto(
                page,
                "59 . Subpartida arancelaria"
            )

            casilla_134 = extraer_casilla_por_texto2(
                page,
                "134"
            )

            if casilla_4 is not None or casilla_59 is not None:

                datos.append({
                    "Archivo": uploaded_file.name,
                    "Pagina": i + 1,
                    "Numero Formulario": casilla_4,
                    "Manifiesto de carga": casilla_42,
                    "Subpartida arancelaria": casilla_59,
                    "Levante No.": casilla_134

                })

    if datos:

        df = pd.DataFrame(datos)

        st.success(f"Se procesaron {len(uploaded_files)} archivos")
        st.dataframe(df)

        # Excel consolidado
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.download_button(
            label="Descargar Excel Consolidado",
            data=output,
            file_name="resultado_DIM_consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("No se encontraron datos en los documentos.")