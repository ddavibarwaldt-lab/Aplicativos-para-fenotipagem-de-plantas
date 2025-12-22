import cv2
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import os
import datetime

class DualCamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dual Webcam App")

        # Pasta de salvamento padrão
        self.save_folder = os.getcwd()

        # Detectar câmeras disponíveis
        self.available_cameras = self.detect_cameras()
        if not self.available_cameras:
            tk.messagebox.showerror("Erro", "Nenhuma câmera detectada")
            root.destroy()
            return

        # Dropdown para seleção de câmeras
        self.cam1_var = tk.IntVar(value=self.available_cameras[0])
        self.cam2_var = tk.IntVar(value=self.available_cameras[1] if len(self.available_cameras) > 1 else self.available_cameras[0])

        tk.Label(root, text="Câmera 1:").grid(row=0, column=0)
        self.cam1_menu = ttk.Combobox(root, values=self.available_cameras, textvariable=self.cam1_var, width=5)
        self.cam1_menu.grid(row=0, column=1)
        tk.Label(root, text="Câmera 2:").grid(row=0, column=2)
        self.cam2_menu = ttk.Combobox(root, values=self.available_cameras, textvariable=self.cam2_var, width=5)
        self.cam2_menu.grid(row=0, column=3)

        # Botão para iniciar câmeras
        self.btn_start = tk.Button(root, text="Iniciar Câmeras", command=self.start_cameras)
        self.btn_start.grid(row=0, column=4, padx=10)

        # Frames para os vídeos
        self.cam1_frame = tk.Label(root)
        self.cam1_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        self.cam2_frame = tk.Label(root)
        self.cam2_frame.grid(row=1, column=2, columnspan=2, padx=10, pady=10)

        # Botões de ação
        self.btn_frame = tk.Frame(root)
        self.btn_frame.grid(row=2, column=0, columnspan=5)
        self.btn_save = tk.Button(self.btn_frame, text="Tirar Foto", command=self.take_photo, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=5)
        self.btn_select_folder = tk.Button(self.btn_frame, text="Selecionar Pasta", command=self.select_folder)
        self.btn_select_folder.pack(side=tk.LEFT, padx=5)

        # Inicialização
        self.cap1 = None
        self.cap2 = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def detect_cameras(self, max_tested=10):
        cams = []
        for i in range(max_tested):
            cap = cv2.VideoCapture(i)
            if cap.read()[0]:
                cams.append(i)
            cap.release()
        return cams

    def start_cameras(self):
        # Fechar câmeras anteriores se existirem
        if self.cap1: self.cap1.release()
        if self.cap2: self.cap2.release()

        self.cap1 = cv2.VideoCapture(self.cam1_var.get())
        self.cap2 = cv2.VideoCapture(self.cam2_var.get())

        self.btn_save.config(state=tk.NORMAL)
        self.update_frames()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_folder = folder

    def take_photo(self):
        if not self.cap1 or not self.cap2:
            return
        ret1, frame1 = self.cap1.read()
        ret2, frame2 = self.cap2.read()
        if ret1 and ret2:
            frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
            frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            img1 = Image.fromarray(frame1)
            img2 = Image.fromarray(frame2)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = os.path.join(self.save_folder, f"fotos_{timestamp}.pdf")
            img1.save(pdf_path, save_all=True, append_images=[img2])
            print(f"PDF salvo em {pdf_path}")

    def update_frames(self):
        if self.cap1 and self.cap2:
            ret1, frame1 = self.cap1.read()
            ret2, frame2 = self.cap2.read()
            if ret1:
                img1 = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)))
                self.cam1_frame.imgtk = img1
                self.cam1_frame.configure(image=img1)
            if ret2:
                img2 = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)))
                self.cam2_frame.imgtk = img2
                self.cam2_frame.configure(image=img2)
            self.root.after(10, self.update_frames)

    def on_closing(self):
        if self.cap1: self.cap1.release()
        if self.cap2: self.cap2.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DualCamApp(root)
    root.mainloop()
