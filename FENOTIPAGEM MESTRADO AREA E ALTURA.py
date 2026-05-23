import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import math
import openpyxl
from openpyxl import Workbook

class GreenAreaDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Área Vegetal")

        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.frame, bg="black")
        self.h_scroll = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scroll = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.h_scroll.grid(row=1, column=0, sticky='ew')
        self.v_scroll.grid(row=0, column=1, sticky='ns')

        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.info_box = tk.Text(root, height=8, width=70)
        self.info_box.pack()

        buttons_frame = tk.Frame(root)
        buttons_frame.pack(pady=5)

        tk.Button(buttons_frame, text="Abrir Imagem", command=self.select_image).grid(row=0, column=0, padx=5)
        tk.Button(buttons_frame, text="Resetar", command=self.reset_all).grid(row=0, column=1, padx=5)
        tk.Button(buttons_frame, text="Medir Distância", command=self.activate_distance_mode).grid(row=0, column=2, padx=5)
        tk.Button(buttons_frame, text="Salvar Imagem com Área", command=self.save_result_image).grid(row=0, column=3, padx=5)
        tk.Button(buttons_frame, text="Finalizar Trabalho", command=self.save_xlsx).grid(row=0, column=4, padx=5)
        tk.Button(buttons_frame, text="Nova Medição", command=self.start_new_measurement).grid(row=0, column=5, padx=5)

        self.original_img = None
        self.display_img = None
        self.tk_img = None
        self.img_id = None

        self.scale_points = []
        self.rect_start = None
        self.regions = []
        self.region_rect_ids = []

        self.distance_mode = False
        self.distance_points = []

        self.pixels_per_cm = None

        # NOVOS
        self.result_img = None
        self.total_area_cm2 = None
        self.xlsx_data = []
        self.area_list = []

        menu = tk.Menu(root)
        root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Abrir Imagem", command=self.select_image)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def reset_all(self):
        self.scale_points = []
        self.rect_start = None
        self.regions = []
        self.region_rect_ids = []
        self.pixels_per_cm = None
        self.distance_mode = False
        self.distance_points = []
        self.result_img = None
        self.total_area_cm2 = None
        self.info_box.delete("1.0", tk.END)
        self.area_list = []

        if self.original_img is not None:
            self.display_img = self.original_img.copy()
            self.update_image_on_canvas()

        self.info_box.insert(tk.END, "1. Clique em dois pontos para definir a escala\n")

    def select_image(self):
        folder_path = filedialog.askdirectory(title="Escolha a pasta com imagens")
        if not folder_path:
            return

        images = [f for f in os.listdir(folder_path)
                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]

        if not images:
            self.info_box.insert(tk.END, "Nenhuma imagem encontrada na pasta.\n")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Escolher Imagem")

        thumbs_frame = tk.Frame(popup)
        thumbs_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(thumbs_frame)
        scroll_y = tk.Scrollbar(thumbs_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.thumbs = []

        for i, img_file in enumerate(images):
            img_path = os.path.join(folder_path, img_file)
            try:
                pil_img = Image.open(img_path).resize((200, 150))
                tk_thumb = ImageTk.PhotoImage(pil_img)
                self.thumbs.append(tk_thumb)

                frame = tk.Frame(scroll_frame, bd=2, relief="ridge", padx=5, pady=5)
                frame.grid(row=i // 3, column=i % 3, padx=10, pady=10)

                btn = tk.Button(frame, image=tk_thumb,
                                command=lambda p=img_path: self.load_image_from_popup(popup, p))
                btn.pack()

                label = tk.Label(frame, text=img_file, wraplength=180)
                label.pack()
            except:
                pass

    def load_image_from_popup(self, popup, path):
        popup.destroy()
        self.load_image(path)

    def load_image(self, file_path):
        self.original_img = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
        self.display_img = self.original_img.copy()
        self.reset_all()

    def update_image_on_canvas(self):
        self.tk_img = ImageTk.PhotoImage(Image.fromarray(self.display_img))
        self.canvas.delete("all")
        self.img_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def on_click(self, event):
        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))

        if self.distance_mode:
            self.distance_points.append((x, y))
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill='yellow')
            if len(self.distance_points) == 2:
                self.calculate_distance()
            return

        if len(self.scale_points) < 2:
            self.scale_points.append((x, y))
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill='red')
            if len(self.scale_points) == 2:
                self.ask_scale()
        elif len(self.regions) < 2:
            self.rect_start = (x, y)

    def on_drag(self, event):
        if self.rect_start and len(self.regions) < 2:
            x = int(self.canvas.canvasx(event.x))
            y = int(self.canvas.canvasy(event.y))

            if self.region_rect_ids:
                self.canvas.delete(self.region_rect_ids[-1])

            x0, y0 = self.rect_start
            rect_id = self.canvas.create_rectangle(x0, y0, x, y, outline='blue')
            self.region_rect_ids.append(rect_id)

    def on_release(self, event):
        if self.rect_start and len(self.regions) < 2:
            x0, y0 = self.rect_start
            x1 = int(self.canvas.canvasx(event.x))
            y1 = int(self.canvas.canvasy(event.y))

            self.regions.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
            self.rect_start = None

            if len(self.regions) == 1:
                self.info_box.insert(tk.END, "2. Selecione a região do tom máximo\n")
            elif len(self.regions) == 2:
                self.info_box.insert(tk.END, "3. Calculando área ...\n")
                self.root.after(100, self.calculate_green_area)

    def ask_scale(self):
        popup = tk.Toplevel(self.root)
        popup.title("Definir Escala")

        tk.Label(popup, text="Distância real entre os pontos (em cm):").pack()
        entry = tk.Entry(popup)
        entry.pack()

        def confirm():
            real_distance = float(entry.get())
            px = math.dist(*self.scale_points)
            self.pixels_per_cm = px / real_distance
            popup.destroy()
            self.info_box.insert(tk.END, "2. Selecione a região do tom mínimo\n")

        tk.Button(popup, text="OK", command=confirm).pack()

    def activate_distance_mode(self):
        if not self.pixels_per_cm:
            self.info_box.insert(tk.END, "Defina a escala antes de medir distância.\n")
            return
        self.distance_mode = True
        self.distance_points = []
        self.info_box.insert(tk.END, "Modo de medição ativado.\n")

    def calculate_distance(self):
        (x1, y1), (x2, y2) = self.distance_points
        pixel_dist = math.dist((x1, y1), (x2, y2))
        real_dist = pixel_dist / self.pixels_per_cm
        self.info_box.insert(tk.END, f"Distância real medida: {real_dist:.2f} cm\n")
        self.distance_mode = False

    def calculate_green_area(self):
        hsv = cv2.cvtColor(self.original_img, cv2.COLOR_RGB2HSV)

        def extract(rect):
            x0, y0, x1, y1 = rect
            roi = hsv[y0:y1, x0:x1]
            return np.min(roi.reshape(-1, 3), 0), np.max(roi.reshape(-1, 3), 0)

        hsv_min, _ = extract(self.regions[0])
        _, hsv_max = extract(self.regions[1])

        mask = cv2.inRange(hsv, hsv_min, hsv_max)
        green_pixels = cv2.countNonZero(mask)

        result_img = self.original_img.copy()
        result_img[mask > 0] = [128, 128, 128]

        self.display_img = result_img
        self.result_img = result_img.copy()
        self.update_image_on_canvas()

        self.total_area_cm2 = green_pixels * (1 / self.pixels_per_cm) ** 2

        # Adiciona na lista de áreas
        self.area_list.append(self.total_area_cm2)
        avg_area = sum(self.area_list) / len(self.area_list)

        # Atualiza info box
        self.info_box.insert(tk.END, f"Pixels verdes: {green_pixels}\n")
        self.info_box.insert(tk.END, f"Área estimada: {self.total_area_cm2:.2f} cm²\n")
        self.info_box.insert(tk.END, f"Média das áreas até agora: {avg_area:.2f} cm²\n")

        # Armazena dados para XLSX
        self.xlsx_data.append({
            "Imagem": "Imagem atual",
            "Área (cm²)": round(self.total_area_cm2, 2),
            "Média (cm²)": round(avg_area, 2)
        })

    def start_new_measurement(self):
        """Permite iniciar uma nova medição mantendo áreas anteriores para média"""
        self.rect_start = None
        self.regions = []
        self.region_rect_ids = []
        self.distance_mode = False
        self.distance_points = []
        self.info_box.insert(tk.END, "\nNova medição iniciada. Selecione a região mínima novamente.\n")

    def save_result_image(self):
        if self.result_img is None or self.total_area_cm2 is None:
            self.info_box.insert(tk.END, "Nenhum resultado para salvar.\n")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")]
        )
        if not path:
            return

        img = self.result_img.copy()
        h, w = img.shape[:2]

        footer = 50
        output = np.ones((h + footer, w, 3), dtype=np.uint8) * 255
        output[:h] = img

        texto = f"Area calculada: {self.total_area_cm2:.2f} cm2"

        cv2.putText(
            output,
            texto,
            (20, h + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2,
            cv2.LINE_AA
        )

        cv2.imwrite(path, cv2.cvtColor(output, cv2.COLOR_RGB2BGR))
        self.info_box.insert(tk.END, "Imagem salva com sucesso.\n")

    def save_xlsx(self):
        if not self.xlsx_data:
            self.info_box.insert(tk.END, "Nenhum dado para salvar.\n")
            return

        folder = filedialog.askdirectory(title="Escolha a pasta para salvar o XLSX")
        if not folder:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Área Vegetal"

        ws.append(["Imagem", "Área (cm²)", "Média (cm²)"])
        for entry in self.xlsx_data:
            ws.append([entry["Imagem"], entry["Área (cm²)"], entry.get("Média (cm²)", "")])

        save_path = os.path.join(folder, "resultado_area.xlsx")
        wb.save(save_path)
        self.info_box.insert(tk.END, f"Arquivo XLSX salvo em: {save_path}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = GreenAreaDetector(root)
    root.mainloop()