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
        self.geometry("600x700")

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

        self.worker_label = ctk.CTkLabel(self, text="Numero di worker (thread):")
        self.worker_label.pack(pady=5)

        self.worker_entry = ctk.CTkEntry(self)
        self.worker_entry.insert(0, "5")  # valore di default
        self.worker_entry.pack(pady=5)

        self.output_label = ctk.CTkLabel(self, text="File di output:")
        self.output_label.pack(pady=5)

        self.output_path = ctk.CTkEntry(self, width=400)
        self.output_path.insert(0, "catalogo_con_prezzi.csv")
        self.output_path.pack(pady=5)

        self.output_button = ctk.CTkButton(self, text="Scegli dove salvare", command=self.select_output_path)
        self.output_button.pack(pady=5)

        self.ibs_checkbox = ctk.CTkCheckBox(self, text="Scrape IBS", command=self.check_scraper)
        self.ibs_checkbox.select()
        self.ibs_checkbox.pack(pady=5)

        self.ebay_checkbox = ctk.CTkCheckBox(self, text="Scrape eBay", command=self.check_scraper)
        self.ebay_checkbox.select()
        self.ebay_checkbox.pack(pady=5)

        self.amz_checkbox = ctk.CTkCheckBox(self, text="Scrape Amazon", command=self.check_scraper)
        self.amz_checkbox.deselect()
        self.amz_checkbox.pack(pady=5)

        self.start_button = ctk.CTkButton(self, text="Avvia Aggiornamento", command=self.start_processing, state="disabled")
        self.start_button.pack(pady=20)

        self.progress_label = ctk.CTkLabel(self, text="")
        self.progress_label.pack()

        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10)

        self.filepath = None

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filepath:
            self.filepath = filepath
            self.file_label.configure(text=f"CSV: {filepath}")
            self.check_scraper()

    def check_scraper(self):
        if self.filepath and (self.ibs_checkbox.get() or self.ebay_checkbox.get() or self.amz_checkbox.get()):
            self.start_button.configure(state="normal")
        else:
            self.start_button.configure(state="disabled")

    def start_processing(self):
        if not self.filepath:
            messagebox.showerror("Errore", "Nessun file selezionato.")
            return

        self.progress_label.configure(text="🔄 Elaborazione in corso...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="🔄 Elaborazione in corso...")
        self.start_button.configure(state="disabled")
        thread = threading.Thread(target=self.run_processing)
        thread.start()

    def run_processing(self):
        try:
            from src.main import start_processing_csv

            row_limit = int(self.row_entry.get()) if self.row_entry.get().isdigit() else 30
            max_workers = int(self.worker_entry.get()) if self.worker_entry.get().isdigit() else 5
            output_file = self.output_path.get() or "catalogo_con_prezzi.csv"

            def update_progress(percentage):
                self.progress_bar.set(percentage)

            output = start_processing_csv(
                self.filepath,
                use_ibs=self.ibs_checkbox.get(),
                use_ebay=self.ebay_checkbox.get(),
                use_amz=self.amz_checkbox.get(),
                row_limit=row_limit,
                max_workers=max_workers,
                output_filename=output_file,
                progress_callback=update_progress
            )
            self.progress_label.configure(text=f"✅ File salvato: {output}")
            self.start_button.configure(state="normal")
        except Exception as e:
            self.progress_label.configure(text="❌ Errore durante l'elaborazione.")
            messagebox.showerror("Errore", str(e))
            self.start_button.configure(state="normal")

    def select_output_path(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            self.output_path.delete(0, ctk.END)
            self.output_path.insert(0, path)



if __name__ == "__main__":
    app = LibrisaggiApp()
    app.mainloop()
