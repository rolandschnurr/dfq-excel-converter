# app.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from aqdefreader import read_dfq_file, create_column_dataframe, create_characteristic_dataframe

st.title("🔧 AQDEF Reader - DFQ zu Excel Konverter")
st.write("Konvertiere Q-DAS DFQ-Dateien zu Excel mit detaillierten Analysen")

# File Upload
uploaded_file = st.file_uploader(
    "DFQ-Datei hochladen", 
    type=['dfq'],
    help="Q-DAS ASCII transfer format (.dfq)"
)

if uploaded_file is not None:
    try:
        # Temporäre Datei erstellen
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dfq"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Mit deiner Bibliothek parsen
        st.info("📖 Lade DFQ-Datei...")
        parsed_file = read_dfq_file(temp_filename)
        
        st.success(f"✅ DFQ-Datei erfolgreich geladen!")
        
        # File-Info anzeigen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Anzahl Teile", parsed_file.part_count())
        with col2:
            characteristics_count = len(parsed_file.get_part(0).get_characteristics()) if parsed_file.part_count() > 0 else 0
            st.metric("Anzahl Merkmale", characteristics_count)
        with col3:
            total_measurements = sum(
                len(char.get_measurements()) 
                for char in parsed_file.get_part(0).get_characteristics()
            ) if parsed_file.part_count() > 0 else 0
            st.metric("Gesamt Messwerte", total_measurements)
        
        # Teil-Auswahl (falls mehrere Teile)
        part_index = 0
        if parsed_file.part_count() > 1:
            part_options = []
            for i in range(parsed_file.part_count()):
                part_name = parsed_file.get_part(i).get_data("K1001") or f"Teil {i+1}"
                part_options.append(f"Teil {i+1}: {part_name}")
            
            selected_part = st.selectbox("Teil auswählen:", part_options)
            part_index = int(selected_part.split(":")[0].replace("Teil ", "")) - 1

        # Daten konvertieren
        st.subheader("📊 Konvertierte Daten")
        
        # Hauptdatenframe erstellen
        main_df = create_column_dataframe(parsed_file, part_index, group_by_date=True)
        
        if not main_df.empty:
            st.dataframe(main_df)
            
            # Statistiken anzeigen
            st.subheader("📈 Statistische Auswertung")
            stats_df = main_df.describe()
            st.dataframe(stats_df)
            
            # Visualisierungen
            st.subheader("📊 Visualisierungen")
            
            viz_cols = st.columns(2)
            with viz_cols[0]:
                st.write("**Zeitreihe aller Merkmale:**")
                st.line_chart(main_df)
            
            with viz_cols[1]:
                st.write("**Verteilungen:**")
                for col in main_df.columns:
                    if main_df[col].notna().any():
                        st.write(f"*{col}:*")
                        st.bar_chart(main_df[col].dropna().value_counts().head(10))
            
            # Excel-Export Optionen
            st.subheader("💾 Excel-Export")
            
            export_option = st.radio(
                "Export-Format:",
                ["Einfach (nur Messwerte)", "Detailliert (mit Metadaten)", "Getrennte Blätter pro Merkmal"]
            )
            
            if st.button("📥 Excel-Datei erstellen"):
                excel_buffer = create_excel_export(parsed_file, part_index, export_option)
                
                # Download-Button
                st.download_button(
                    label="📥 Excel herunterladen",
                    data=excel_buffer,
                    file_name=f"aqdef_export_{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.success("✅ Excel-Datei wurde erstellt!")
        
        else:
            st.warning("⚠️ Keine Messdaten in der DFQ-Datei gefunden.")
        
        # Detail-Info zu Merkmalen
        if characteristics_count > 0:
            st.subheader("🔍 Merkmal-Details")
            
            characteristic_names = []
            for i, char in enumerate(parsed_file.get_part(part_index).get_characteristics()):
                name = char.get_data("K2002") or f"Merkmal {i+1}"
                characteristic_names.append(name)
            
            selected_char = st.selectbox("Merkmal für Details auswählen:", characteristic_names)
            char_index = characteristic_names.index(selected_char)
            
            selected_characteristic = parsed_file.get_part(part_index).get_characteristics()[char_index]
            
            # Merkmal-Metadaten anzeigen
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Merkmal-Informationen:**")
                for key in selected_characteristic.get_data_keys():
                    value = selected_characteristic.get_data(key)
                    st.write(f"• {key}: {value}")
            
            with col2:
                st.write("**Messwerte-Details:**")
                char_df = create_characteristic_dataframe(selected_characteristic)
                if not char_df.empty:
                    st.dataframe(char_df)
                    st.line_chart(char_df.set_index('datetime')['value'])
    
    except Exception as e:
        st.error(f"❌ Fehler beim Verarbeiten der DFQ-Datei: {str(e)}")
        st.write("Mögliche Ursachen:")
        st.write("• Datei ist beschädigt oder kein gültiges DFQ-Format")
        st.write("• Encoding-Probleme")
        st.write("• Unvollständige Daten in der Datei")

def create_excel_export(parsed_file, part_index, export_option):
    """
    Erstellt Excel-Export mit verschiedenen Optionen
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        if export_option == "Einfach (nur Messwerte)":
            # Einfacher Export - nur Messwerte
            main_df = create_column_dataframe(parsed_file, part_index, group_by_date=True)
            main_df.to_excel(writer, sheet_name='Messwerte', index=True)
        
        elif export_option == "Detailliert (mit Metadaten)":
            # Detaillierter Export
            main_df = create_column_dataframe(parsed_file, part_index, group_by_date=True)
            main_df.to_excel(writer, sheet_name='Messwerte', index=True)
            
            # Statistiken hinzufügen
            stats_df = main_df.describe()
            stats_df.to_excel(writer, sheet_name='Statistiken', index=True)
            
            # Teil-Metadaten
            part = parsed_file.get_part(part_index)
            part_metadata = []
            for key in ["K1001", "K1002", "K1003", "K1004"]:  # Häufige Teil-Keys
                try:
                    value = part.get_data(key)
                    if value:
                        part_metadata.append({"Schlüssel": key, "Wert": value})
                except:
                    pass
            
            if part_metadata:
                metadata_df = pd.DataFrame(part_metadata)
                metadata_df.to_excel(writer, sheet_name='Teil_Metadaten', index=False)
            
            # Merkmal-Metadaten
            char_metadata = []
            for i, char in enumerate(part.get_characteristics()):
                char_name = char.get_data("K2002") or f"Merkmal_{i+1}"
                for key in char.get_data_keys():
                    value = char.get_data(key)
                    char_metadata.append({
                        "Merkmal": char_name,
                        "Schlüssel": key,
                        "Wert": value
                    })
            
            if char_metadata:
                char_meta_df = pd.DataFrame(char_metadata)
                char_meta_df.to_excel(writer, sheet_name='Merkmal_Metadaten', index=False)
        
        elif export_option == "Getrennte Blätter pro Merkmal":
            # Jedes Merkmal auf eigenem Blatt
            part = parsed_file.get_part(part_index)
            
            for i, char in enumerate(part.get_characteristics()):
                char_name = char.get_data("K2002") or f"Merkmal_{i+1}"
                char_df = create_characteristic_dataframe(char, unique=False)
                
                if not char_df.empty:
                    # Blattname bereinigen (Excel-konforme Namen)
                    sheet_name = char_name.replace("/", "_").replace("\\", "_")[:31]
                    char_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Übersicht auf erstem Blatt
            main_df = create_column_dataframe(parsed_file, part_index, group_by_date=True)
            main_df.to_excel(writer, sheet_name='Übersicht', index=True)
    
    output.seek(0)
    return output.getvalue()

# Sidebar mit Info
st.sidebar.markdown("""
## 📖 Verwendung

1. **DFQ-Datei hochladen**
2. **Daten automatisch konvertieren**
3. **Export-Format wählen**
4. **Excel herunterladen**

## 🔧 Features

- ✅ Vollständige DFQ-Unterstützung
- ✅ Mehrere Excel-Export-Optionen
- ✅ Datenvisualisierung
- ✅ Statistische Auswertung
- ✅ Metadaten-Export

## 📊 Export-Formate

**Einfach:** Nur Messwerte  
**Detailliert:** Mit Metadaten & Statistiken  
**Getrennt:** Jedes Merkmal einzeln
""")