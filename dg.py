import streamlit as st
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Raport Deutsche Glasfaser", layout="wide")

# --- DANE Z PLIKU PDF (T DG 3.pdf) ---
# Lista materiałów dokładnie jak w pliku
MATERIALS_LIST = [
    {"name": "FTTP 4 faser kabel", "unit": "m"},
    {"name": "MultiHüp", "unit": "st."},
    {"name": "Hüp", "unit": "st."},
    {"name": "T-stücke", "unit": "st."},
    {"name": "Instalacionsrohr", "unit": "m"},
    {"name": "Muffe M 20", "unit": "st."},
    {"name": "Quick Schellen M 20", "unit": "st."},
    {"name": "Schutzrohr", "unit": "m"},
    {"name": "Metalikanal 30x30", "unit": "m"},
    {"name": "Plastik kanal 15x15", "unit": "m"},
    {"name": "Plombe", "unit": "st."},
    {"name": "Serveschrank", "unit": "st."},
]

# --- KLASA PDF ---
class PDF(FPDF):
    def header(self):
        # Nagłówek: Deutsche Glasfaser
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Deutsche Glasfaser', 0, 1, 'L')
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Tagesarbeitsbericht', 0, 1, 'L')
        self.ln(5)

    def footer(self):
        # Stopka: FIBERGROUND
        self.set_y(-20)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'FIBERGROUND', 0, 0, 'C')

# --- FUNKCJA GENERUJĄCA ---
def generate_dg_pdf(date_str, address, object_num, work_df, materials_counts, staff_data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # 1. GÓRNE DANE (Datum, Adresse, Obiekt Nummer)
    pdf.cell(30, 8, "Datum:", 0, 0)
    pdf.cell(60, 8, date_str, "B", 0) # "B" to podkreślenie
    
    pdf.cell(35, 8, "Obiekt Nummer:", 0, 0)
    pdf.cell(60, 8, object_num, "B", 1)
    
    pdf.ln(2)
    pdf.cell(30, 8, "Adresse:", 0, 0)
    pdf.cell(155, 8, address, "B", 1)
    pdf.ln(10)

    # 2. TABELA GŁÓWNA (Wohnung, Gfta, Ont gpon...)
    # Nagłówki
    pdf.set_font('Arial', 'B', 9)
    cols = ["Nr", "Wohnung", "Gfta", "Ont gpon", "Ont xgs", "Patch Ont"]
    widths = [10, 40, 25, 35, 35, 35]
    
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 8, col, 1, 0, 'C')
    pdf.ln()

    # Wiersze (1-12)
    pdf.set_font('Arial', '', 9)
    for index, row in work_df.iterrows():
        pdf.cell(widths[0], 7, str(index + 1), 1, 0, 'C') # Numer wiersza
        
        # Nazwa mieszkania
        wohnung = row["Wohnung"] if row["Wohnung"] else ""
        pdf.cell(widths[1], 7, wohnung, 1, 0, 'C')
        
        # Checkboxy - jeśli True to wstawiamy "X"
        for col_name, width in zip(["Gfta", "Ont gpon", "Ont xgs", "Patch Ont"], widths[2:]):
            val = "X" if row[col_name] else ""
            pdf.cell(width, 7, val, 1, 0, 'C')
        pdf.ln()
    
    pdf.ln(10)

    # 3. MATERIAŁY
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, "Material", 0, 1, 'L')
    
    # Nagłówki tabeli materiałów
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(10, 7, "Nr", 1, 0, 'C', 1)
    pdf.cell(100, 7, "Material", 1, 0, 'L', 1)
    pdf.cell(30, 7, "Masse", 1, 0, 'C', 1)
    pdf.cell(30, 7, "Anzahl", 1, 1, 'C', 1)

    # Wiersze materiałów
    pdf.set_font('Arial', '', 10)
    for i, item in enumerate(MATERIALS_LIST):
        qty = materials_counts.get(item['name'], 0)
        
        # Wypisujemy wszystkie wiersze (1-12) jak w oryginale, nawet jak puste
        display_qty = str(qty) if qty > 0 else ""
        
        pdf.cell(10, 7, str(i + 1), 1, 0, 'C')
        pdf.cell(100, 7, item['name'], 1, 0)
        pdf.cell(30, 7, item['unit'], 1, 0, 'C') # Jednostka (Masse)
        pdf.cell(30, 7, display_qty, 1, 1, 'C')
    
    pdf.ln(10)

    # 4. PRACOWNIK (Mietarbeiter, czasy)
    pdf.set_font('Arial', 'B', 10)
    
    # Nagłówki
    pdf.cell(60, 7, "Mietarbeiter", 1, 0, 'C', 1)
    pdf.cell(30, 7, "Beginn", 1, 0, 'C', 1)
    pdf.cell(30, 7, "Pause", 1, 0, 'C', 1)
    pdf.cell(30, 7, "Ende", 1, 1, 'C', 1)
    
    # Dane
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 8, staff_data['name'], 1, 0, 'C')
    pdf.cell(30, 8, staff_data['start'], 1, 0, 'C')
    pdf.cell(30, 8, staff_data['break'], 1, 0, 'C')
    pdf.cell(30, 8, staff_data['end'], 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFEJS UŻYTKOWNIKA ---

st.title("📝 Raport Deutsche Glasfaser")
st.markdown("Generator PDF na podstawie wzoru `T DG 3`.")

# --- DANE WEJŚCIOWE (NA GŁÓWNYM EKRANIE) ---

# Używamy st.expander, żeby można było zwinąć te dane jak już je wpiszesz
with st.expander("🏗️ Dane Projektu i Pracownika", expanded=True):
    
    st.write("--- DANE PROJEKTU ---")
    col_proj_1, col_proj_2 = st.columns(2)
    with col_proj_1:
        report_date = st.date_input("Data (Datum)", datetime.now())
        obj_num = st.text_input("Numer Obiektu", "12345")
    with col_proj_2:
        address = st.text_input("Adres (Adresse)", "Musterstraße 1")

    st.write("--- PRACOWNIK ---")
    staff_name = st.text_input("Imię i Nazwisko", "Jan Nowak")
    
    col_time_1, col_time_2, col_time_3 = st.columns(3)
    with col_time_1:
        start = st.time_input("Start", value=None)
    with col_time_2:
        brk = st.text_input("Pauza", "0")
    with col_time_3:
        end = st.time_input("Koniec", value=None)

# --- GŁÓWNA CZĘŚĆ ---

# 1. TABELA PRAC (12 wierszy)
st.subheader("1. Wykaz Prac (Wohnungen)")
st.caption("Wpisz numer mieszkania i zaznacz wykonane czynności.")

# Przygotowanie pustej tabeli na 12 wierszy
default_data = {
    "Wohnung": [""] * 12,
    "Gfta": [False] * 12,
    "Ont gpon": [False] * 12,
    "Ont xgs": [False] * 12,
    "Patch Ont": [False] * 12,
}
df_work = pd.DataFrame(default_data)

# Edytor tabeli
edited_work = st.data_editor(
    df_work,
    column_config={
        "Wohnung": st.column_config.TextColumn("Wohnung (Nr Mieszkania)"),
        "Gfta": st.column_config.CheckboxColumn("Gfta", default=False),
        "Ont gpon": st.column_config.CheckboxColumn("Ont gpon", default=False),
        "Ont xgs": st.column_config.CheckboxColumn("Ont xgs", default=False),
        "Patch Ont": st.column_config.CheckboxColumn("Patch Ont", default=False),
    },
    hide_index=False, # Pokazuje numery 0-11 (technicznie), w PDF zrobimy 1-12
    use_container_width=True
)

st.divider()

# 2. MATERIAŁY
st.subheader("2. Zużyte Materiały")
st.caption("Wpisz ilości (Anzahl). Jednostki są przypisane automatycznie.")

col1, col2 = st.columns(2)
collected_materials = {}

for i, item in enumerate(MATERIALS_LIST):
    # Dzielimy na dwie kolumny dla estetyki w aplikacji
    target_col = col1 if i < 6 else col2
    
    with target_col:
        val = st.number_input(
            f"{i+1}. {item['name']} [{item['unit']}]",
            min_value=0,
            step=1,
            key=f"mat_{i}"
        )
        collected_materials[item['name']] = val

# --- GENEROWANIE ---
st.divider()

if st.button("🖨️ Generuj Plik PDF", type="primary"):
    # Formatowanie czasów do stringa
    staff_info = {
        "name": staff_name,
        "start": start.strftime("%H:%M") if start else "",
        "end": end.strftime("%H:%M") if end else "",
        "break": brk
    }
    
    try:
        pdf_bytes = generate_dg_pdf(
            report_date.strftime("%d.%m.%Y"),
            address,
            obj_num,
            edited_work,
            collected_materials,
            staff_info
        )
        
        st.success("Gotowe! Kliknij poniżej, aby pobrać.")
        st.download_button(
            label="📥 Pobierz Raport PDF",
            data=pdf_bytes,
            file_name=f"Raport_DG_{obj_num}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Błąd: {e}")