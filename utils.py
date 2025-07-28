# utils.py (optional - für erweiterte Features)
import pandas as pd
from datetime import datetime

def create_detailed_report(parsed_file, part_index=0):
    """
    Erstellt einen detaillierten Bericht über die DFQ-Datei
    """
    part = parsed_file.get_part(part_index)
    
    report = {
        "Datei-Info": {
            "Anzahl Teile": parsed_file.part_count(),
            "Anzahl Merkmale": len(part.get_characteristics()),
            "Verarbeitet am": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        },
        "Teil-Info": {},
        "Merkmale": []
    }
    
    # Teil-Informationen sammeln
    for key in ["K1001", "K1002", "K1003", "K1004"]:
        try:
            value = part.get_data(key)
            if value:
                report["Teil-Info"][key] = value
        except:
            pass
    
    # Merkmal-Informationen sammeln
    for i, char in enumerate(part.get_characteristics()):
        char_info = {
            "Index": i + 1,
            "Name": char.get_data("K2002") or f"Merkmal {i+1}",
            "Anzahl Messwerte": len(char.get_measurements()),
            "Metadaten": {}
        }
        
        # Wichtige Merkmal-Keys sammeln
        for key in char.get_data_keys():
            char_info["Metadaten"][key] = char.get_data(key)
        
        report["Merkmale"].append(char_info)
    
    return report

def validate_dfq_file(parsed_file):
    """
    Validiert die DFQ-Datei und gibt Warnungen zurück
    """
    warnings = []
    
    if parsed_file.part_count() == 0:
        warnings.append("⚠️ Keine Teile in der DFQ-Datei gefunden")
        return warnings
    
    part = parsed_file.get_part(0)
    characteristics = part.get_characteristics()
    
    if len(characteristics) == 0:
        warnings.append("⚠️ Keine Merkmale gefunden")
        return warnings
    
    # Prüfe auf Merkmale ohne Messwerte
    empty_chars = [
        char.get_data("K2002") or f"Merkmal {i+1}"
        for i, char in enumerate(characteristics)
        if len(char.get_measurements()) == 0
    ]
    
    if empty_chars:
        warnings.append(f"⚠️ Merkmale ohne Messwerte: {', '.join(empty_chars)}")
    
    # Prüfe auf fehlende Namen
    unnamed_chars = [
        f"Merkmal {i+1}"
        for i, char in enumerate(characteristics)
        if not char.get_data("K2002")
    ]
    
    if unnamed_chars:
        warnings.append(f"ℹ️ Merkmale ohne Namen: {', '.join(unnamed_chars)}")
    
    return warnings
