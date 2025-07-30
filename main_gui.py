import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class LibrisaggiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Librisaggi - Aggiorna Prezzi Catalogo")
        self.geometry("600x800")

        self.label = ctk.CTkLabel(self, text="Seleziona un file CSV da aggiornare")
        self.label.pack(pady=10)

        self.browse_button = ctk.CTkButton(self, text="Sfoglia", command=self.select_file)
        self.browse_button.pack(pady=5)

        self.file_label = ctk.CTkLabel(self, text="")
        self.file_label.pack()

        self.row_label = ctk.CTkLabel(self, text="Numero di righe da processare:")
        self.row_label.pack(pady=5)

        self.row_entry = ctk.CTkEntry(self)
        self.row_entry.insert(0, "30")
        self.row_entry.pack(pady=5)

        self.analyze_all_checkbox = ctk.CTkCheckBox(self, text="Analizza l'intero file", command=self.toggle_row_entry)
        self.analyze_all_checkbox.pack(pady=5)

        self.worker_label = ctk.CTkLabel(self, text="Numero di worker (thread): (consigliato 90)")
        self.worker_label.pack(pady=5)

        self.worker_entry = ctk.CTkEntry(self)
        self.worker_entry.insert(0, "90")
        self.worker_entry.pack(pady=5)

        self.api_key_label = ctk.CTkLabel(self, text="Chiave API ScraperAPI:")
        self.api_key_label.pack(pady=5)

        self.api_key_entry = ctk.CTkEntry(self, width=400)
        self.api_key_entry.insert(0, "e4b967afdaf014ef917eaa9773019cbe")  # eventualmente un valore di default
        self.api_key_entry.pack(pady=5)

        self.cache_checkbox = ctk.CTkCheckBox(self, text="Usa cache locale (price_cache.json)")
        self.cache_checkbox.select()
        self.cache_checkbox.pack(pady=5)

        self.start_button = ctk.CTkButton(self, text="Avvia Aggiornamento", command=self.start_processing, state="disabled")
        self.start_button.pack(pady=20)

        self.stop_button = ctk.CTkButton(self, text="🛑 Interrompi", command=self.request_stop, state="disabled")
        self.stop_button.pack(pady=5)

        self.progress_label = ctk.CTkLabel(self, text="")
        self.progress_label.pack()

        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)

        self.filepath = None
        self.stop_requested = False

    def toggle_row_entry(self):
        if self.analyze_all_checkbox.get():
            self.row_entry.configure(state="disabled")
        else:
            self.row_entry.configure(state="normal")

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.filepath = filepath
            self.file_label.configure(text=f"CSV: {filepath}")
            self.start_button.configure(state="normal")

    def request_stop(self):
        self.stop_requested = True
        self.progress_label.configure(text="⛔ Interruzione richiesta...")

    def start_processing(self):
        if not self.filepath:
            messagebox.showerror("Errore", "Nessun file selezionato.")
            return

        self.progress_label.configure(text="🔄 Elaborazione in corso...")
        self.progress_bar.set(0)
        self.stop_requested = False
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        thread = threading.Thread(target=self.run_processing)
        thread.start()

    def run_processing(self):
        try:
            from src.main import start_processing_csv

            if self.analyze_all_checkbox.get():
                row_limit = None
            else:
                row_limit = int(self.row_entry.get()) if self.row_entry.get().isdigit() else 30

            max_workers = int(self.worker_entry.get()) if self.worker_entry.get().isdigit() else 5
            use_cache = self.cache_checkbox.get()

            def update_progress(p):
                self.progress_bar.set(p)

            def stop_check():
                return self.stop_requested

            api_key = self.api_key_entry.get().strip()

            output = start_processing_csv(
                filename=self.filepath,
                row_limit=row_limit,
                max_workers=max_workers,
                progress_callback=update_progress,
                stop_requested_callback=stop_check,
                use_cache=use_cache,
                api_key=api_key
            )
            self.progress_label.configure(text=f"✅ File salvato: {output}")
        except Exception as e:
            self.progress_label.configure(text="❌ Errore durante l'elaborazione.")
            messagebox.showerror("Errore", str(e))
        finally:
            self.stop_button.configure(state="disabled")
        

if __name__ == "__main__":
    app = LibrisaggiApp()
    app.mainloop()
