
import streamlit as st
import pandas as pd
import re
import dateparser
from docx import Document
from fpdf import FPDF
import fitz  # PyMuPDF

# === Cargar bases de datos ===
cie_df = pd.read_csv("cie10_base.csv")
ium_df = pd.read_json("ium_base.json")

def extract_dates(text):
    patrones = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}', text)
    fechas = []
    for fecha_raw in patrones:
        fecha = dateparser.parse(fecha_raw)
        if fecha:
            fechas.append(fecha.strftime("%Y-%m-%d"))
    return sorted(set(fechas))

def buscar_cie10(text):
    enfermedades = []
    texto_lower = text.lower()
    for _, row in cie_df.iterrows():
        nombre = row['nombre'].lower()
        if nombre in texto_lower:
            enfermedades.append({"nombre": row['nombre'], "codigo_cie": row['codigo']})
    return enfermedades

def buscar_ium(text):
    medicamentos = []
    texto_lower = text.lower()
    for _, row in ium_df.iterrows():
        principio = row['principio_activo'].lower()
        if principio in texto_lower:
            medicamentos.append({
                "principio_activo": row['principio_activo'],
                "codigo_ium": row['codigo_ium'],
                "forma": row['forma'],
                "via": row['via']
            })
    return medicamentos

def procesar_historia_clinica(texto):
    return {
        "linea_de_tiempo": extract_dates(texto),
        "enfermedades": buscar_cie10(texto),
        "medicamentos": buscar_ium(texto)
    }

def generar_texto_tutela(nombre, cedula, direccion, telefono, datos):
    texto = f"""ACCIÓN DE TUTELA

Señor(a)
Juez de la República
(EPS correspondiente)
Ciudad

1. IDENTIFICACIÓN DEL ACCIONANTE
Nombre: {nombre}
Cédula: {cedula}
Dirección: {direccion}
Teléfono: {telefono}

2. HECHOS
El accionante padece de las siguientes patologías identificadas en su historia clínica:
""" + ''.join(f"- {e['nombre']} (CIE-10: {e['codigo_cie']})\n" for e in datos["enfermedades"])
    texto += "\nSe encuentra en tratamiento con los siguientes medicamentos:\n"
    texto += ''.join(f"- {m['principio_activo']} (IUM: {m['codigo_ium']}, vía: {m['via']})\n" for m in datos["medicamentos"])
    texto += f"\nSegún la historia clínica, los eventos clínicos relevantes ocurrieron en las fechas: {', '.join(datos['linea_de_tiempo'])}."

    texto += """
3. FUNDAMENTOS DE DERECHO
Se fundamenta esta acción en los artículos 11 (derecho a la vida) y 49 (derecho a la salud) de la Constitución Política de Colombia,
y en la Ley Estatutaria 1751 de 2015. Así mismo, en la Sentencia T-760 de 2008 y otras providencias de la Corte Constitucional
que garantizan el acceso efectivo a tratamientos médicos, incluso si no están incluidos en el plan de beneficios.

4. PRETENSIONES
Se solicita al juez de tutela ordenar a la EPS correspondiente la entrega inmediata y continua de los medicamentos prescritos,
así como el acceso a los tratamientos requeridos por el estado de salud del accionante.

5. PRUEBAS
Se adjunta historia clínica y fórmula médica.

6. JURAMENTO
Bajo la gravedad del juramento, manifiesto que no he presentado otra tutela con el mismo objeto y finalidad.

Atentamente,

[Firma]
{nombre}
C.C. {cedula}
"""
    return texto

def guardar_word(texto, nombre_archivo):
    doc = Document()
    for linea in texto.split("\n"):
        doc.add_paragraph(linea)
    doc.save(nombre_archivo)

def guardar_pdf(texto, nombre_archivo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for linea in texto.split("\n"):
        pdf.multi_cell(0, 10, linea)
    pdf.output(nombre_archivo)

def leer_pdf(uploaded_file):
    text = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# === INTERFAZ STREAMLIT ===
st.title("🧾 Generador de Acción de Tutela en Salud (con PDF)")
st.write("Llena los datos del paciente y pega o sube el texto de la historia clínica.")

with st.form("form_tutela"):
    nombre = st.text_input("Nombre completo", "Juan Pérez")
    cedula = st.text_input("Cédula", "12345678")
    direccion = st.text_input("Dirección", "Calle Ficticia 123")
    telefono = st.text_input("Teléfono", "3110000000")

    opcion = st.radio("¿Cómo quieres ingresar la historia clínica?", ["Pegar texto", "Subir archivo PDF"])

    if opcion == "Pegar texto":
        historia = st.text_area("Historia clínica", height=250)
    else:
        archivo_pdf = st.file_uploader("Subir archivo PDF", type="pdf")
        historia = ""
        if archivo_pdf is not None:
            historia = leer_pdf(archivo_pdf)

    submit = st.form_submit_button("Generar Documento")

if submit:
    if not historia.strip():
        st.error("❗ Debes ingresar o subir la historia clínica.")
    else:
        datos = procesar_historia_clinica(historia)
        texto = generar_texto_tutela(nombre, cedula, direccion, telefono, datos)
        guardar_word(texto, "tutela.docx")
        guardar_pdf(texto, "tutela.pdf")
        st.success("✅ Documentos generados correctamente.")

        with open("tutela.docx", "rb") as f:
            st.download_button("📥 Descargar Word", f, file_name="tutela.docx")

        with open("tutela.pdf", "rb") as f:
            st.download_button("📥 Descargar PDF", f, file_name="tutela.pdf")
