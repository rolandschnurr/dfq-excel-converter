# app_fallback.py - Fallback ohne aqdefreader
import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(
    page_title="DFQ zu Excel Konverter",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 DFQ zu Excel Konverter (Basic Version)")
st.write("Einfacher DFQ-Parser ohne externe Abhängigkeiten")

# Warnung anzeigen
st.warning("⚠️ Dies ist eine vereinfachte Version. Für vollständige DFQ-Unterstützung verwende die lokale Version mit aqdefreader.")

# File Upload
uploaded_file = st.file_uploader(
    "DFQ-Datei hochladen", 
    type=['dfq', 'txt'],
    help="Q-DAS ASCII transfer format (.dfq) oder Text-Dateien"
)

def simple_dfq_parser(content):
    """
    Einfacher DFQ-Parser für grundlegende Funktionalität
    """
    lines = content.strip().split('\n')
    
    measurements = {}
    current_characteristic = "Merkmal_1"
    
    for line in lines:
        line = line.strip()
        
        # Charakteristik-Namen extrahieren
        if line.startswith('K2002'):
            parts = line.split('\t')
            if len(parts) > 1:
                current_characteristic = parts[1]
                measurements[current_characteristic] = []
        
        # Messwerte extrahieren (vereinfacht)
        elif line and not line.startswith('K'):
            try:
                # Versuche Zahlenwerte zu extrahieren
                parts = line.replace('\x14', ' ').split()
                for part in parts:
                    try:
                        value = float(part)
                        if current_characteristic not in measurements:
                            measurements[current_characteristic] = []
                        measurements[current_characteristic].append(value)
                    except ValueError:
                        continue
            except:
                continue
    
    return measurements

if uploaded_file is not None:
    try:
        # Datei als String lesen
        content = uploaded_file.read().decode('utf-8', errors='ignore')
        
        st.success("✅ Datei erfolgreich geladen!")
        
        # Einfaches Parsing
        measurements = simple_dfq_parser(content)
        
        if measurements:
            st.subheader("📊 Erkannte Merkmale und Messwerte")
            
            # Daten als DataFrame anzeigen
            max_len = max(len(values) for values in measurements.values()) if measurements else 0
            
            # DataFrame erstellen
            df_data = {}
            for char_name, values in measurements.items():
                # Auffüllen mit NaN für unterschiedliche Längen
                padded_values = values + [None] * (max_len - len(values))
                df_data[char_name] = padded_values
            
            df = pd.DataFrame(df_data)
            
            if not df.empty:
                st.dataframe(df)
                
                # Statistiken
                st.subheader("📈 Statistische Auswertung")
                stats_df = df.describe()
                st.dataframe(stats_df)
                
                # Visualisierung
                st.subheader("📊 Visualisierung")
                st.line_chart(df)
                
                # Excel-Export
                st.subheader("💾 Excel-Export")
                
                if st.button("📥 Excel-Datei erstellen"):
                    # Excel erstellen
                    output = io.BytesIO()
                    
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Messwerte', index=True)
                        stats_df.to_excel(writer, sheet_name='Statistiken', index=True)
                    
                    output.seek(0)
                    
                    # Download-Button
                    st.download_button(
                        label="📥 Excel herunterladen",
                        data=output.getvalue(),
                        file_name=f"dfq_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.success("✅ Excel-Datei wurde erstellt!")
            else:
                st.warning("⚠️ Keine gültigen Messdaten gefunden.")
        else:
            st.warning("⚠️ Keine Merkmale in der DFQ-Datei erkannt.")
            
        # Rohdaten anzeigen
        with st.expander("🔍 Datei-Inhalt anzeigen (Debug)"):
            st.text_area("Datei-Inhalt:", content[:2000] + "..." if len(content) > 2000 else content, height=200)
    
    except Exception as e:
        st.error(f"❌ Fehler beim Verarbeiten der Datei: {str(e)}")

# Sidebar mit Info
st.sidebar.markdown("""
## 📖 Basic Version

Diese vereinfachte Version kann:
- ✅ DFQ-Dateien lesen
- ✅ Einfache Messwerte extrahieren  
- ✅ Excel-Export erstellen
- ✅ Grundlegende Visualisierung

## ⚠️ Einschränkungen

- Vereinfachtes DFQ-Parsing
- Keine vollständige AQDEF-Unterstützung
- Begrenzte Metadaten-Extraktion

## 🔧 Vollversion

Für vollständige Funktionalität verwende die lokale Version mit aqdefreader.

---
*Basic DFQ Parser für Streamlit Cloud*
""")
