from pathlib import Path
import re

ESTENSIONI_VIDEO = {".mkv", ".mp4", ".avi", ".mov", ".webm", ".m4v"}

TAG_LINGUA = [
    r'\bita-eng\b', r'\beng-ita\b', r'\bsub-ita\b', r'\bsub-eng\b',
    r'\bita\b', r'\beng\b', r'\bmulti\b', r'\bdual\b', r'\bsub\b'
]

TAG_RUMORE = [
    r'1080p', r'720p', r'2160p', r'4k', r'576p',
    r'web-rip', r'webrip', r'hdtv', r'bluray', r'bdrip', r'dvdrip',
    r'x264', r'x265', r'h264', r'h265', r'hevc', r'aac', r'ac3'
]

PATTERNS_EPISODIO = [
    re.compile(r'^(?P<titolo>.+?)[._\s-]+S(?P<stagione>\d{1,2})[._\s-]*E(?P<episodio>\d{1,2})(?P<resto>.*)$', re.IGNORECASE),
    re.compile(r'^(?P<titolo>.+?)[._\s-]+(?P<stagione>\d{1,2})x(?P<episodio>\d{1,2})(?P<resto>.*)$', re.IGNORECASE),
    re.compile(r'^(?P<titolo>.+?)[._\s-]+Ep[._\s-]*(?P<episodio>\d{1,2})(?P<resto>.*)$', re.IGNORECASE),
]

def normalizza_trattini(testo):
    if not testo:
        return ""
    s = re.sub(r'[._\s]+', '-', testo)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

def estrai_info_filename(filename_senza_estensione):
    nome_raw = filename_senza_estensione

    for pattern in PATTERNS_EPISODIO:
        match = pattern.match(nome_raw)
        if match:
            data = match.groupdict()
            
            serie = normalizza_trattini(data['titolo'])
            stagione = int(data.get('stagione', 1))
            episodio = int(data['episodio'])
            
            resto = data.get('resto', '')
            
            # Lingua
            lingua_trovata = ""
            for l_pattern in TAG_LINGUA:
                l_match = re.search(l_pattern, resto, re.IGNORECASE)
                if l_match:
                    lingua_trovata = l_match.group(0).upper().replace(".", "-")
                    break
                    
            # Qualità
            qualita_trovata = []
            resto_lower = resto.lower()
            if '1080p' in resto_lower: qualita_trovata.append('1080p')
            elif '720p' in resto_lower: qualita_trovata.append('720p')
            elif '2160p' in resto_lower or '4k' in resto_lower: qualita_trovata.append('4K')
            
            if 'webrip' in resto_lower or 'web-rip' in resto_lower: qualita_trovata.append('WEBRIP')
            elif 'bluray' in resto_lower or 'bdrip' in resto_lower: qualita_trovata.append('Bluray')
            
            if 'x264' in resto_lower: qualita_trovata.append('x264')
            elif 'x265' in resto_lower or 'hevc' in resto_lower: qualita_trovata.append('x265')

            # Titolo Episodio
            tag_indici = []
            if lingua_trovata:
                idx_l = re.search(re.escape(lingua_trovata), resto, re.IGNORECASE)
                if idx_l: tag_indici.append(idx_l.start())
            
            for q_tag in TAG_RUMORE:
                idx_q = re.search(r'\b' + q_tag + r'\b', resto, re.IGNORECASE)
                if idx_q: tag_indici.append(idx_q.start())
            
            idx_rel = re.search(r'-[a-zA-Z0-9]+$', resto)
            if idx_rel: tag_indici.append(idx_rel.start())
            
            if tag_indici:
                cut_idx = min(tag_indici)
                titolo_ep_raw = resto[:cut_idx]
            else:
                titolo_ep_raw = resto
            
            titolo_episodio = normalizza_trattini(titolo_ep_raw)
            
            return {
                "serie": serie,
                "stagione": stagione,
                "episodio": episodio,
                "titolo_episodio": titolo_episodio,
                "lingua": lingua_trovata,
                "qualita": "-".join(qualita_trovata),
                "successo": True
            }
            
    return {"successo": False}

def verifica_stagioni_multiple(cartella_path):
    """Restituisce True se trova file appartenenti a più di una stagione diversa."""
    cartella = Path(cartella_path)
    stagioni_rilevate = set()
    for f in cartella.iterdir():
        if f.is_file() and f.suffix.lower() in ESTENSIONI_VIDEO:
            info = estrai_info_filename(f.stem)
            if info.get("successo"):
                stagioni_rilevate.add(info["stagione"])
    return len(stagioni_rilevate) > 1

def genera_lista_rinomina(cartella_path, nome_serie, stagione, lingua="", qualita="",
                          inc_serie=True, inc_stagione=True, inc_titolo_ep=True,
                          inc_lingua=True, inc_qualita=True, dividi_stagioni=False):
    
    cartella = Path(cartella_path)
    file_video = sorted([
        f for f in cartella.iterdir() 
        if f.is_file() and f.suffix.lower() in ESTENSIONI_VIDEO
    ], key=lambda x: x.name)

    nome_serie_formatted = normalizza_trattini(nome_serie)
    risultato = []

    for idx, file_orig in enumerate(file_video, start=1):
        info = estrai_info_filename(file_orig.stem)
        parti = []

        # Determina episodio e stagione effettivi (leggendoli dal file se possibile, altrimenti manuali)
        if info.get("successo"):
            ep_effettivo = info["episodio"]
            stagione_effettiva = info["stagione"]
        else:
            ep_effettivo = idx
            stagione_effettiva = int(stagione) if stagione else 1

        if inc_serie and nome_serie_formatted:
            parti.append(nome_serie_formatted)

        if inc_stagione:
            parti.append(f"S{stagione_effettiva:02d}E{ep_effettivo:02d}")

        if inc_titolo_ep and info.get("successo") and info.get("titolo_episodio"):
            parti.append(info["titolo_episodio"])

        if inc_lingua:
            lingua_eff = lingua if lingua else info.get("lingua", "")
            if lingua_eff:
                parti.append(normalizza_trattini(lingua_eff))

        if inc_qualita:
            qualita_eff = qualita if qualita else info.get("qualita", "")
            if qualita_eff:
                parti.append(normalizza_trattini(qualita_eff))

        nuovo_nome = "_".join(parti) + file_orig.suffix.lower() if parti else file_orig.name

        # Gestione sottocartelle
        if dividi_stagioni:
            subfolder = f"Season-{stagione_effettiva:02d}"
            nuovo_percorso = Path(subfolder) / nuovo_nome
        else:
            nuovo_percorso = Path(nuovo_nome)

        risultato.append((file_orig, nuovo_percorso))
        
    return risultato

def applica_rinomina(lista_modifiche):
    """Rinomina i file e restituisce lo storico delle modifiche effettuate (per eventuale Undo)."""
    storico_effettivo = []
    for file_orig, nuovo_percorso in lista_modifiche:
        destinazione = file_orig.parent / nuovo_percorso
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        file_orig.rename(destinazione)
        # Salviamo la coppia (nuovo_percorso_effettivo, vecchio_percorso)
        storico_effettivo.append((destinazione, file_orig))
    return storico_effettivo

def annulla_rinomina(storico_modifiche):
    """Inverte lo storico delle modifiche riportando i file ai nomi originali."""
    count = 0
    # Scorriamo lo storico al contrario per sicurezza
    for corrente, originale in reversed(storico_modifiche):
        if corrente.exists():
            corrente.parent.mkdir(parents=True, exist_ok=True)
            corrente.rename(originale)
            count += 1
    return count