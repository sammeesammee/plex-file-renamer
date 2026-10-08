import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import random
import string
import subprocess
import platform
import time

# Import dal backend
from backend import (
    genera_lista_rinomina,
    applica_rinomina,
    annulla_rinomina, # <--- Aggiunto qui
    estrai_info_filename,
    verifica_stagioni_multiple,
    ESTENSIONI_VIDEO
)

# =========================================================
# IMPOSTAZIONI VERSIONE E TESTI
# =========================================================
PATCH_VERSION = "3" 
APP_TITLE_FOOTER = f"Plex Media organizer and renamer - Version 1.0.{PATCH_VERSION} - By SR Engineering - Petaluma (CA)"
BOOT_SUBTITLE = f"Ver 1.1.{PATCH_VERSION} - By SR Engineering - Powered by Gemini"

ASCII_ART = """
██████╗ ██╗     ███████╗██╗  ██╗
██╔══██╗██║     ██╔════╝╚██╗██╔╝
██████╔╝██║     █████╗   ╚███╔╝ 
██╔═══╝ ██║     ██╔══╝   ██╔██╗ 
██║     ███████╗███████╗██╔╝ ██╗
╚═╝     ╚══════╝╚══════╝╚═╝  ╚═╝
   MEDIA ORGANIZER & RENAMER
"""

class RetroToggle:
    """Checkbutton customizzato in puro stile terminale testo per stile Matrix."""
    def __init__(self, parent, text, var, bg_color="#000000", fg_color="#00FF41", font=("Courier New", 9)):
        self.var = var
        self.text = text
        self.label = tk.Label(parent, bg=bg_color, fg=fg_color, font=font, cursor="hand2")
        self.label.pack(side="left", padx=(0, 10))
        self.label.bind("<Button-1>", self.toggle)
        self.update_view()

    def toggle(self, event=None):
        self.var.set(not self.var.get())
        self.update_view()

    def update_view(self):
        mark = "■" if self.var.get() else " "
        self.label.config(text=f"[{mark}] {self.text}")

class PlexHackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Plex Media Organizer - SR Engineering")
        self.root.geometry("900x750")
        self.root.configure(bg="black")
        self.root.minsize(850, 700)

        # Variabili di stato e configurazione
        self.cartella_selezionata = Path(__file__).resolve().parent
        self.selected_folder_var = tk.StringVar(value=str(self.cartella_selezionata))
        self.lista_modifiche_corrente = []
        self.dividi_stagioni = False

        self.var_inc_serie = tk.BooleanVar(value=True)
        self.var_inc_stagione = tk.BooleanVar(value=True)
        self.var_inc_titolo_ep = tk.BooleanVar(value=True)
        self.var_inc_lingua = tk.BooleanVar(value=True)
        self.var_inc_qualita = tk.BooleanVar(value=True)

        # Palette Colori Matrix
        self.bg_color = "black"
        self.fg_bright = "#00FF41" 
        self.fg_dim = "#008F11"    
        self.fg_dark = "#003B00"   
        self.font_hacker = ("Courier New", 9)
        self.font_ascii = ("Courier New", 12, "bold")

        # Variabili di stato per l'animazione di avvio
        self.ascii_lines = ASCII_ART.strip("\n").split("\n")
        self.current_line = 0
        self.displayed_ascii = ""
        
        self.current_char = 0
        self.displayed_sub = ""

        # Avvia la sequenza di boot
        self.start_boot_sequence()

    # --- FASE 1: SPLASH SCREEN (INTRO) ---

    def start_boot_sequence(self):
        self.intro_frame = tk.Frame(self.root, bg=self.bg_color)
        self.intro_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.ascii_label = tk.Label(
            self.intro_frame, text="", fg=self.fg_bright, bg=self.bg_color, 
            font=self.font_ascii, justify="left"
        )
        self.ascii_label.pack(pady=10)

        self.subtitle_label = tk.Label(
            self.intro_frame, text="", fg=self.fg_dim, bg=self.bg_color, 
            font=("Courier New", 11)
        )
        self.subtitle_label.pack(pady=20)

        self.root.after(400, self.animate_ascii)

    def animate_ascii(self):
        if self.current_line < len(self.ascii_lines):
            self.displayed_ascii += self.ascii_lines[self.current_line] + "\n"
            self.ascii_label.config(text=self.displayed_ascii)
            self.current_line += 1
            self.root.after(70, self.animate_ascii)
        else:
            self.root.after(250, self.animate_subtitle)

    def animate_subtitle(self):
        if self.current_char < len(BOOT_SUBTITLE):
            self.displayed_sub += BOOT_SUBTITLE[self.current_char]
            self.subtitle_label.config(text=self.displayed_sub + " █")
            self.current_char += 1
            self.root.after(25, self.animate_subtitle)
        else:
            self.subtitle_label.config(text=self.displayed_sub)
            self.root.after(1200, self.transition_to_main)

    def transition_to_main(self):
        self.intro_frame.destroy()
        self.build_main_interface()

    # --- FASE 2: INTERFACCIA PRINCIPALE ---

    def build_main_interface(self):
        # 1. SFONDO ANIMATO (MATRIX RAIN)
        self.canvas = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        self.canvas.place(relwidth=1, relheight=1)

        self.chars = list(string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?")
        self.font_size = 14
        self.cols = 150 
        self.drops = [random.randint(-20, 20) for _ in range(self.cols)] 
        self.active_items = []

        # 2. PANNELLO CENTRALE
        self.main_frame = tk.Frame(
            self.root, bg=self.bg_color, 
            highlightbackground=self.fg_bright, highlightthickness=1
        )
        self.main_frame.place(relx=0.5, rely=0.45, anchor="center", width=760)

        tk.Label(
            self.main_frame, text=">_ PLEX_CORE_RENAMER_SYS...", 
            fg=self.fg_bright, bg=self.bg_color, font=("Courier New", 13, "bold")
        ).pack(pady=(12, 5))

        # --- SEZIONE CARTELLA ---
        folder_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        folder_frame.pack(fill="x", padx=20, pady=5)

        tk.Button(
            folder_frame, text="[ BROWSE ]", command=self.select_folder,
            fg=self.fg_bright, bg=self.bg_color, activebackground=self.fg_dark, 
            activeforeground=self.fg_bright, font=("Courier New", 9, "bold"), bd=1, relief="solid", cursor="hand2"
        ).pack(side="left", padx=(0, 10))

        self.folder_entry = tk.Entry(
            folder_frame, textvariable=self.selected_folder_var, 
            fg=self.fg_bright, bg="#020A02", insertbackground=self.fg_bright,
            font=self.font_hacker, bd=1, relief="solid"
        )
        self.folder_entry.pack(side="left", fill="x", expand=True)

        # --- CAMPI DI INPUT E TOGGLES ---
        self.entry_serie = self.crea_campo_con_toggle("NOME SERIE", self.var_inc_serie)
        self.entry_stagione = self.crea_campo_con_toggle("NUM. STAGIONE", self.var_inc_stagione)
        self.entry_lingua = self.crea_campo_con_toggle("LINGUA AUDIO", self.var_inc_lingua)
        self.entry_qualita = self.crea_campo_con_toggle("QUALITA/CODEC", self.var_inc_qualita)

        # Toggle Titolo Episodio
        frame_titolo = tk.Frame(self.main_frame, bg=self.bg_color)
        frame_titolo.pack(fill="x", padx=20, pady=(4, 6))
        RetroToggle(frame_titolo, "INCLUDI TITOLO EPISODIO", self.var_inc_titolo_ep, bg_color=self.bg_color, fg_color=self.fg_bright)

        # --- PULSANTI AZIONE ---
        btn_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        btn_frame.pack(fill="x", padx=20, pady=6)

        tk.Button(
            btn_frame, text="[ ANALIZZA ANTEPRIMA ]", command=self.azione_anteprima,
            fg=self.fg_bright, bg=self.bg_color, activebackground=self.fg_dark, activeforeground=self.fg_bright,
            font=("Courier New", 9, "bold"), bd=1, relief="solid", cursor="hand2"
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        tk.Button(
            btn_frame, text="[ >>> ESEGUI RINOMINA PLEX <<< ]", command=self.run_renamer_logic,
            fg=self.bg_color, bg=self.fg_bright, activebackground=self.fg_dim, activeforeground=self.bg_color,
            font=("Courier New", 9, "bold"), bd=0, cursor="hand2"
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

        # --- CONSOLE TERMINALE LOGS ---
        log_header = tk.Frame(self.main_frame, bg=self.bg_color)
        log_header.pack(fill="x", padx=20, pady=(4, 0))

        tk.Label(
            log_header, text="SYSTEM CONSOLE LOGS:", 
            fg=self.fg_dim, bg=self.bg_color, font=("Courier New", 8, "bold")
        ).pack(side="left")

        self.log_console = tk.Text(
            self.main_frame, bg="#020A02", fg=self.fg_bright, 
            insertbackground=self.fg_bright, font=("Courier New", 8),
            height=6, highlightbackground=self.fg_dim, highlightthickness=1, bd=0
        )
        self.log_console.pack(fill="both", expand=True, padx=20, pady=(2, 10))

        # --- FRAME SCELTA STAGIONI MULTIPLE (Inline) ---
        self.frame_scelta_stagioni = tk.Frame(self.main_frame, bg=self.bg_color)
        # Non facciamo .pack() qui, comparirà solo se necessario

        # --- FRAME POST-AZIONE (Link cartella + Tasto Abort) ---
        self.frame_post_azione = tk.Frame(self.main_frame, bg=self.bg_color)
        # Nota: Non facciamo .pack() qui, lo mostreremo solo a fine rinomina.

        # 3. FOOTER
        self.footer_frame = tk.Frame(self.root, bg=self.bg_color)
        self.footer_frame.place(relx=0.5, rely=0.94, anchor="center", relwidth=1)

        tk.Label(
            self.footer_frame, text=APP_TITLE_FOOTER, 
            fg=self.fg_bright, bg=self.bg_color, font=("Courier New", 10, "bold")
        ).pack()

        tk.Label(
            self.footer_frame, text="Powered by Gemini", 
            fg=self.fg_dim, bg=self.bg_color, font=("Courier New", 8, "italic")
        ).pack()

        # Inizializzazioni
        self.log("> Terminale di controllo inizializzato.")
        self.esegui_auto_rilevamento(self.cartella_selezionata)
        self.update_matrix()

    # --- METODI DI COSTRUZIONE UI E FOCUS ---

    def crea_campo_con_toggle(self, testo, var):
        frame = tk.Frame(self.main_frame, bg=self.bg_color)
        frame.pack(fill="x", padx=20, pady=(2, 0))
        
        RetroToggle(frame, testo, var, bg_color=self.bg_color, fg_color=self.fg_bright)
        
        entry = tk.Entry(
            self.main_frame, bg="#020A02", fg=self.fg_bright, insertbackground=self.fg_bright, 
            font=self.font_hacker, relief="solid", bd=1, highlightbackground=self.fg_dark, highlightcolor=self.fg_bright
        )
        entry.is_autofilled = False
        entry.pack(fill="x", padx=20, pady=1)
        entry.bind("<FocusIn>", lambda e: self.gestisci_focus_in(entry))
        return entry

    def imposta_testo_corsivo(self, entry, testo):
        entry.delete(0, tk.END)
        if testo:
            entry.insert(0, testo)
            entry.config(font=("Courier New", 9, "italic"), fg=self.fg_dim)
            entry.is_autofilled = True
        else:
            entry.config(font=self.font_hacker, fg=self.fg_bright)
            entry.is_autofilled = False

    def gestisci_focus_in(self, entry):
        if getattr(entry, "is_autofilled", False):
            entry.config(font=self.font_hacker, fg=self.fg_bright)
            entry.is_autofilled = False
            self.root.after(10, lambda: entry.select_range(0, tk.END))

    # --- LOGICA MATRIX ANIMATION ---

    def update_matrix(self):
        canvas_height = self.canvas.winfo_height() or 750

        for i in range(self.cols):
            if random.random() > 0.3:
                char = random.choice(self.chars)
                x = i * self.font_size
                y = self.drops[i] * self.font_size

                item = self.canvas.create_text(x, y, text=char, fill=self.fg_bright, font=("Courier New", 12, "bold"))
                self.active_items.append((item, 0)) 
                self.drops[i] += 1 

                if y > canvas_height and random.random() > 0.8:
                    self.drops[i] = 0

        new_items = []
        for item, age in self.active_items:
            age += 1
            if age == 6:
                self.canvas.itemconfig(item, fill=self.fg_dim) 
            elif age == 14:
                self.canvas.itemconfig(item, fill=self.fg_dark) 
            
            if age > 20:
                self.canvas.delete(item) 
            else:
                new_items.append((item, age))

        self.active_items = new_items
        self.root.after(50, self.update_matrix)

    # --- LOGICA OPERATIVA E BACKEND INTEGRATO ---

    def chiedi_conferma_stagioni_inline(self, messaggio):
        """Mostra una richiesta interattiva nel pannello con bottoni Sì (Verde) e No (Rosso)"""
        for widget in self.frame_scelta_stagioni.winfo_children():
            widget.destroy()
            
        self.frame_scelta_stagioni.pack(fill="x", padx=20, pady=(5, 10))
        
        # Testo della domanda in stile terminale (colore Arancione/Giallo avviso)
        lbl = tk.Label(
            self.frame_scelta_stagioni, 
            text=messaggio, 
            fg="#FFA500", bg=self.bg_color, 
            font=("Courier New", 9, "bold")
        )
        lbl.pack(side="top", anchor="w", pady=(0, 5))
        
        risultato_var = tk.BooleanVar()
        
        # Tasto SI (Verde scuro)
        btn_si = tk.Button(
            self.frame_scelta_stagioni, 
            text="[ ✔ SI ]", 
            command=lambda: [risultato_var.set(True), self.frame_scelta_stagioni.pack_forget()],
            fg="white", bg="#006400", 
            activebackground="green", activeforeground="white",
            font=("Courier New", 9, "bold"), bd=1, relief="solid", cursor="hand2"
        )
        btn_si.pack(side="left", padx=(0, 10))
        
        # Tasto NO (Rosso scuro)
        btn_no = tk.Button(
            self.frame_scelta_stagioni, 
            text="[ ✖ NO ]", 
            command=lambda: [risultato_var.set(False), self.frame_scelta_stagioni.pack_forget()],
            fg="white", bg="#8B0000", 
            activebackground="red", activeforeground="white",
            font=("Courier New", 9, "bold"), bd=1, relief="solid", cursor="hand2"
        )
        btn_no.pack(side="left")
        
        # Mette in attesa la funzione finché l'utente non clicca uno dei due bottoni
        self.root.wait_variable(risultato_var)
        return risultato_var.get()

    def log(self, message):
        if hasattr(self, 'log_console'):
            self.log_console.insert(tk.END, message + "\n")
            self.log_console.see(tk.END)

    def select_folder(self):
        percorso = filedialog.askdirectory(initialdir=str(self.cartella_selezionata))
        if percorso:
            self.cartella_selezionata = Path(percorso)
            self.selected_folder_var.set(str(self.cartella_selezionata))
            self.log(f"> Target impostato: {self.cartella_selezionata}")
            self.esegui_auto_rilevamento(self.cartella_selezionata)

    def esegui_auto_rilevamento(self, cartella_path):
        cartella = Path(cartella_path)
        if not cartella.exists() or not cartella.is_dir():
            return

        file_video = [f for f in cartella.iterdir() if f.is_file() and f.suffix.lower() in ESTENSIONI_VIDEO]
        if not file_video:
            for e in [self.entry_serie, self.entry_stagione, self.entry_lingua, self.entry_qualita]:
                self.imposta_testo_corsivo(e, "")
            self.log("> Nessun file video rilevato nella cartella corrente.")
            return

        file_video.sort(key=lambda x: x.name)
        info = estrai_info_filename(file_video[0].stem)

        if info.get("successo"):
            self.imposta_testo_corsivo(self.entry_serie, info.get("serie", ""))
            self.imposta_testo_corsivo(self.entry_stagione, str(info.get("stagione", "")))
            self.imposta_testo_corsivo(self.entry_lingua, info.get("lingua", ""))
            self.imposta_testo_corsivo(self.entry_qualita, info.get("qualita", ""))
            self.log(f"> Auto-rilevamento completato per: {file_video[0].name}")

    def prepara_dati(self):
        if hasattr(self, 'frame_post_azione'):
            self.frame_post_azione.pack_forget()
        
        cartella_target = Path(self.selected_folder_var.get().strip())
        if not cartella_target.exists():
            messagebox.showerror("SYS.ERR", "DIRECTORY NON TROVATA.")
            self.log("[ERRORE] Directory specificata non trovata.")
            return False

        self.dividi_stagioni = False
        # Sostituisci il vecchio controllo delle stagioni multiple così:
        cartella_corrente = self.selected_folder_var.get()

        if verifica_stagioni_multiple(cartella_corrente):
            risposta = self.chiedi_conferma_stagioni_inline(
                "[?] Rilevate più stagioni. Vuoi suddividerle in cartelle separate?"
            )
            self.dividi_stagioni = risposta
            # ... gestisci la variabile 'risposta' (True/False) come facevi prima ...

        nome = self.entry_serie.get().strip()
        stagione = self.entry_stagione.get().strip()

        self.lista_modifiche_corrente = genera_lista_rinomina(
            cartella_target, nome, stagione,
            self.entry_lingua.get().strip(),
            self.entry_qualita.get().strip(),
            inc_serie=self.var_inc_serie.get(),
            inc_stagione=self.var_inc_stagione.get(),
            inc_titolo_ep=self.var_inc_titolo_ep.get(),
            inc_lingua=self.var_inc_lingua.get(),
            inc_qualita=self.var_inc_qualita.get(),
            dividi_stagioni=self.dividi_stagioni
        )
        return len(self.lista_modifiche_corrente) > 0

    def apri_cartella(self, percorso):
        p = str(percorso)
        if platform.system() == "Windows":
            import os
            os.startfile(p)
        elif platform.system() == "Darwin":
            subprocess.run(["open", p])
        else:
            subprocess.run(["xdg-open", p])

    def azione_anteprima(self):
        self.log("=" * 45)
        self.log("> Avvio analisi anteprima...")
        if self.prepara_dati():
            self.log(f"> File video rilevati: {len(self.lista_modifiche_corrente)}")
            for orig, nuovo in self.lista_modifiche_corrente[:5]: # Mostra i primi 5 file nei log
                self.log(f"  [ORIG]: {orig.name}")
                self.log(f"  [NEW] : {nuovo}")
            if len(self.lista_modifiche_corrente) > 5:
                self.log(f"  ... e altri {len(self.lista_modifiche_corrente) - 5} file.")
            self.log("=" * 45)
        else:
            self.log("[ATTENZIONE] Nessun file video valido trovato.")

    def run_renamer_logic(self):
        self.log("=" * 45)
        self.log("> Inizializzazione sequenza di rinomina...")
        if not self.lista_modifiche_corrente:
            if not self.prepara_dati():
                self.log("[ERRORE] Impossibile procedere senza file da elaborare.")
                return

        try:
            cartella_target = Path(self.selected_folder_var.get().strip())
            totale_file = len(self.lista_modifiche_corrente)
            self.ultimo_storico_modifiche = []
            
            # Ciclo di rinomina con barra di progresso dinamica nel terminale
            for index, (file_orig, nuovo_percorso) in enumerate(self.lista_modifiche_corrente, 1):
                destinazione = file_orig.parent / nuovo_percorso
                destinazione.parent.mkdir(parents=True, exist_ok=True)
                file_orig.rename(destinazione)
                self.ultimo_storico_modifiche.append((destinazione, file_orig))
                
                # Calcolo percentuale e generazione blocchi ASCII (20 blocchi totali)
                percentuale = int((index / totale_file) * 100)
                blocchi = "█" * (percentuale // 5) + "░" * (20 - (percentuale // 5))
                testo_barra = f"[ 🔄 ELABORAZIONE ] [{blocchi}] {percentuale}% ({index}/{totale_file})"
                
                # Aggiorna la riga della barra nel terminale e forza il refresh grafico
                is_first = (index == 1)
                self.aggiorna_progresso_terminale(testo_barra, is_first)
                self.root.update()

                time.sleep(0.08)
            
            num = len(self.ultimo_storico_modifiche)
            self.log(f"> [SUCCESS] Rinomina completata con successo su {num} elementi!")
            self.lista_modifiche_corrente = []
            
            # Mostra il link alla cartella e il tasto rosso di abort in basso
            self.mostra_comandi_post_azione(cartella_target)
            
        except Exception as e:
            self.log(f"[ECCEZIONE]: {str(e)}")
            messagebox.showerror("SYS.ERR", f"Errore durante la rinomina: {str(e)}")
        self.log("=" * 45)

    def aggiorna_progresso_terminale(self, testo, is_first):
        """Aggiorna dinamicamente l'ultima riga del log simulando una barra di progresso in tempo reale"""
        self.log_console.config(state="normal")
        # Se non è il primo ciclo, cancella la barra precedente per sovrascriverla sulla stessa riga
        if not is_first:
            try:
                self.log_console.delete("end-2c linestart", "end-1c")
            except Exception:
                pass
        self.log_console.insert(tk.END, testo + "\n")
        self.log_console.config(state="disabled")
        self.log_console.see(tk.END)
    def mostra_comandi_post_azione(self, cartella):
        """Mostra il link alla cartella e il pulsante rosso di annullamento nel pannello"""
        for widget in self.frame_post_azione.winfo_children():
            widget.destroy()
            
        self.frame_post_azione.pack(fill="x", padx=20, pady=(4, 4))
        
        # Testo cliccabile "Vai alla Cartella" (colore Cyan in stile terminale)
        lbl_cartella = tk.Label(
            self.frame_post_azione, 
            text="[ VAI ALLA CARTELLA]", 
            fg="#00FFFF", bg=self.bg_color, 
            font=("Courier New", 9, "bold"), 
            cursor="hand2"
        )
        lbl_cartella.pack(side="left", padx=(0, 10))
        lbl_cartella.bind("<Button-1>", lambda e: self.apri_cartella(cartella))
        
        # Tasto Annulla modifiche (Rosso scuro/vivo con testo bianco)
        btn_annulla = tk.Button(
            self.frame_post_azione, 
            text="[ ANNULLA MODIFICHE ]", 
            command=self.esegui_annulla,
            fg="white", bg="#8B0000", 
            activebackground="red", activeforeground="white",
            font=("Courier New", 9, "bold"), bd=1, relief="solid", cursor="hand2"
        )
        btn_annulla.pack(side="right")

    def esegui_annulla(self):
        """Esegue il ripristino dei file allo stato precedente"""
        if not getattr(self, 'ultimo_storico_modifiche', None):
            self.log("[ATTENZIONE] Nessuna operazione recente da annullare.")
            return
            
        try:
            num = annulla_rinomina(self.ultimo_storico_modifiche)
            self.log(f"> [ABORT/UNDO] Ripristinati {num} file allo stato originale.")
            messagebox.showinfo("SYS.ABORT", f"Operazione annullata. Ripristinati {num} file.")
            
            # Svuota lo storico e nasconde il frame post-azione
            self.ultimo_storico_modifiche = []
            self.frame_post_azione.pack_forget()
        except Exception as e:
            self.log(f"[ERRORE UNDO]: {str(e)}")
            messagebox.showerror("SYS.ERR", f"Impossibile annullare: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PlexHackerGUI(root)
    root.mainloop()