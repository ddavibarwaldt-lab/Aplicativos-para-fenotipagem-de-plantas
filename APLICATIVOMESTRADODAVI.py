import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import cv2
import os
from PIL import Image, ImageTk
import math
import datetime
import numpy as np

class ImageDistanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Medidor de Plantas")

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.scroll_x = tk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.pack(fill=tk.X)

        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.bind("<Configure>", self.update_scroll_region)

        self.text_frame = tk.Frame(self.canvas_frame)
        self.text_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_box = tk.Text(self.text_frame, width=30, height=40)
        self.text_box.pack(fill=tk.BOTH, expand=True)

        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack()

        self.btn_load_folder = tk.Button(self.btn_frame, text="Abrir Pasta e Imagem", command=self.load_image)
        self.btn_load_folder.grid(row=0, column=0)

        self.btn_set_scale = tk.Button(self.btn_frame, text="Definir Escala", command=self.set_scale, state=tk.DISABLED)
        self.btn_set_scale.grid(row=0, column=1)

        self.btn_measure = tk.Button(self.btn_frame, text="Medir Distância", command=self.measure_distance, state=tk.DISABLED)
        self.btn_measure.grid(row=0, column=2)

        self.btn_new_measure = tk.Button(self.btn_frame, text="Nova Medida", command=self.new_measure, state=tk.DISABLED)
        self.btn_new_measure.grid(row=0, column=3)

        self.btn_save_txt = tk.Button(self.btn_frame, text="Salvar Distâncias (.txt)", command=self.save_all_to_txt, state=tk.DISABLED)
        self.btn_save_txt.grid(row=0, column=4)

        self.btn_save_image = tk.Button(self.btn_frame, text="Salvar Imagem", command=self.save_image, state=tk.DISABLED)
        self.btn_save_image.grid(row=0, column=5)

        self.btn_filter_negative = tk.Button(self.btn_frame, text="Filtro Negativo", command=self.apply_negative)
        self.btn_filter_negative.grid(row=1, column=1)

        self.btn_filter_infra = tk.Button(self.btn_frame, text="Filtro Infravermelho", command=self.apply_infrared)
        self.btn_filter_infra.grid(row=1, column=2)

        self.btn_perimeter = tk.Button(self.btn_frame, text="Perímetro", command=self.start_perimeter, state=tk.DISABLED)
        self.btn_perimeter.grid(row=1, column=3)

        self.btn_filter_normal = tk.Button(self.btn_frame, text="Filtro Normal", command=self.apply_normal)
        self.btn_filter_normal.grid(row=1, column=4)

        self.btn_area = tk.Button(self.btn_frame, text="Calcular Área", command=self.calculate_area, state=tk.DISABLED)
        self.btn_area.grid(row=1, column=5)

        self.btn_angle = tk.Button(self.btn_frame, text="Medir Ângulo", command=self.measure_angle, state=tk.DISABLED)
        self.btn_angle.grid(row=1, column=6)

        self.btn_detect_contours = tk.Button(self.btn_frame, text="Detectar Contornos", command=self.detectar_contornos)
        self.btn_detect_contours.grid(row=1, column=0)

        self.btn_filter_canny = tk.Button(self.btn_frame, text="Filtro Canny", command=self.apply_canny_filter)
        self.btn_filter_canny.grid(row=1, column=7)

        self.image_path = None
        self.img_original = None
        self.img = None
        self.tk_img = None
        self.scale_pts = []
        self.measure_pts = []
        self.perimeter_pts = []
        self.angle_pts = []
        self.angles = []
        self.px_per_cm = None
        self.distances = []
        self.measuring_perimeter = False
        self.measuring_angle = False

        self.canvas.bind("<Button-1>", self.on_click)

    def resize_proportional(self, img, max_width, max_height):
        return img

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def load_image(self):
        folder = filedialog.askdirectory(title="Selecione a Pasta")
        if not folder: return

        file_path = filedialog.askopenfilename(initialdir=folder, title="Selecione uma Imagem",
                                               filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if not file_path: return

        self.image_path = file_path
        self.img_original = cv2.imread(file_path)
        self.img = self.img_original.copy()
        self.display_image()
        self.reset_state()

    def display_image(self):
        img_rgb = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.displayed_img = img_rgb.copy()
        self.refresh_canvas()

    def refresh_canvas(self):
        img_pil = Image.fromarray(self.displayed_img)
        self.tk_img = ImageTk.PhotoImage(image=img_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.btn_set_scale['state'] == tk.NORMAL:
            if len(self.scale_pts) < 2:
                self.scale_pts.append((int(x), int(y)))
                cv2.circle(self.displayed_img, (int(x), int(y)), 5, (0,255,0), -1)
                if len(self.scale_pts) == 2:
                    cv2.line(self.displayed_img, self.scale_pts[0], self.scale_pts[1], (0,255,0), 2)
                    self.ask_scale()
                self.refresh_canvas()
        elif self.measuring_perimeter:
            self.perimeter_pts.append((int(x), int(y)))
            cv2.circle(self.displayed_img, (int(x), int(y)), 4, (255, 100, 0), -1)
            if len(self.perimeter_pts) > 1:
                cv2.line(self.displayed_img, self.perimeter_pts[-2], self.perimeter_pts[-1], (255, 100, 0), 2)
            self.refresh_canvas()
        elif self.measuring_angle:
            self.angle_pts.append((int(x), int(y)))
            cv2.circle(self.displayed_img, (int(x), int(y)), 5, (0, 200, 255), -1)
            if len(self.angle_pts) == 3:
                self.calc_angle()
            self.refresh_canvas()
        else:
            if len(self.measure_pts) < 2:
                self.measure_pts.append((int(x), int(y)))
                cv2.circle(self.displayed_img, (int(x), int(y)), 5, (255, 0, 0), -1)
                if len(self.measure_pts) == 2:
                    self.calc_distance()
                self.refresh_canvas()

    def detectar_contornos(self):
        if self.img_original is None:
            return

        cinza = cv2.cvtColor(self.img_original, cv2.COLOR_BGR2GRAY)
        bordas = cv2.Canny(cinza, 50, 150)

        bordas_invertida = cv2.bitwise_not(bordas)
        self.img = cv2.cvtColor(bordas_invertida, cv2.COLOR_GRAY2BGR)
        self.display_image()

    def apply_canny_filter(self):
        if self.img_original is None:
            return

        gray = cv2.cvtColor(self.img_original, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        self.img = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        self.display_image()

    def measure_angle(self):
        self.angle_pts.clear()
        self.measuring_angle = True
        self.display_image()

    def calc_angle(self):
        a, b, c = self.angle_pts
        ba = np.array([a[0] - b[0], a[1] - b[1]])
        bc = np.array([c[0] - b[0], c[1] - b[1]])

        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle_rad = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        angle_deg = np.degrees(angle_rad)
        self.angles.append(angle_deg)

        label = f"Ângulo {len(self.angles)}: {angle_deg:.2f}°"
        cv2.putText(self.displayed_img, label, (b[0] + 10, b[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

        cv2.line(self.displayed_img, a, b, (0, 200, 255), 2)
        cv2.line(self.displayed_img, c, b, (0, 200, 255), 2)

        self.text_box.insert(tk.END, label + "\n")
        self.text_box.see(tk.END)
        self.angle_pts.clear()
        self.measuring_angle = False
        self.refresh_canvas()

    def set_scale(self):
        self.scale_pts.clear()
        self.display_image()

    def ask_scale(self):
        dist_cm = simpledialog.askfloat("Escala", "Digite a distância real entre os dois pontos (em cm):")
        if dist_cm:
            px = self.euclidean_distance(*self.scale_pts)
            self.px_per_cm = px / dist_cm
            messagebox.showinfo("Escala Definida", f"Escala: {self.px_per_cm:.2f} px/cm")
            self.btn_measure.config(state=tk.NORMAL)
            self.btn_set_scale.config(state=tk.DISABLED)
            self.btn_new_measure.config(state=tk.NORMAL)
            self.btn_save_txt.config(state=tk.NORMAL)
            self.btn_save_image.config(state=tk.NORMAL)
            self.btn_perimeter.config(state=tk.NORMAL)
            self.btn_area.config(state=tk.NORMAL)
            self.btn_angle.config(state=tk.NORMAL)

    def measure_distance(self):
        self.measure_pts.clear()
        self.display_image()

    def new_measure(self):
        self.measure_pts.clear()
        self.refresh_canvas()

    def calc_distance(self):
        pt1, pt2 = self.measure_pts
        px = self.euclidean_distance(pt1, pt2)
        dist_cm = px / self.px_per_cm
        self.distances.append(dist_cm)

        cv2.line(self.displayed_img, pt1, pt2, (70, 50, 210), 2)
        mid_x = int((pt1[0] + pt2[0]) / 2)
        mid_y = int((pt1[1] + pt2[1]) / 2)
        label = f"{len(self.distances)}) {dist_cm:.2f} cm"
        cv2.putText(self.displayed_img, label, (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 30, 27), 2)

        self.text_box.insert(tk.END, f"Medida {len(self.distances)}: {dist_cm:.2f} cm\n")
        self.text_box.see(tk.END)
        self.refresh_canvas()
        self.measure_pts.clear()

    def save_all_to_txt(self):
        if not self.distances and not self.angles:
            messagebox.showwarning("Nenhuma Medida", "Nenhuma distância ou ângulo para salvar.")
            return

        filename = os.path.splitext(os.path.basename(self.image_path))[0]
        folder = os.path.dirname(self.image_path)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        full_path = os.path.join(folder, f"{filename}_medidas_{now}.txt")

        with open(full_path, "w") as f:
            f.write(f"Medidas em {datetime.datetime.now()}:\n")
            for i, dist in enumerate(self.distances, 1):
                f.write(f"{i}) {dist:.2f} cm\n")
            for i, ang in enumerate(self.angles, 1):
                f.write(f"Ângulo {i}: {ang:.2f}°\n")

        messagebox.showinfo("Salvo", f"Medidas salvas em:\n{full_path}")

    def save_image(self):
        filename = os.path.splitext(os.path.basename(self.image_path))[0]
        folder = os.path.dirname(self.image_path)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(folder, f"{filename}_marcado_{now}.png")
        bgr_img = cv2.cvtColor(self.displayed_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(out_path, bgr_img)
        messagebox.showinfo("Imagem Salva", f"Imagem com marcações salva em:\n{out_path}")

    def reset(self):
        self.reset_state()
        self.display_image()
        self.text_box.delete('1.0', tk.END)

    def reset_state(self):
        self.scale_pts.clear()
        self.measure_pts.clear()
        self.perimeter_pts.clear()
        self.angle_pts.clear()
        self.distances.clear()
        self.angles.clear()
        self.px_per_cm = None
        self.measuring_perimeter = False
        self.measuring_angle = False
        self.btn_set_scale.config(state=tk.NORMAL)
        self.btn_measure.config(state=tk.DISABLED)
        self.btn_new_measure.config(state=tk.DISABLED)
        self.btn_save_txt.config(state=tk.DISABLED)
        self.btn_save_image.config(state=tk.DISABLED)
        self.btn_perimeter.config(state=tk.DISABLED)
        self.btn_area.config(state=tk.DISABLED)
        self.btn_angle.config(state=tk.DISABLED)

    def euclidean_distance(self, pt1, pt2):
        return math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])

    def apply_negative(self):
        self.img = 255 - self.img_original.copy()
        self.display_image()

    def apply_infrared(self):
        infrared = self.img_original[:, :, 2]
        infrared = cv2.merge([infrared, infrared, infrared])
        self.img = infrared
        self.display_image()

    def apply_normal(self):
        self.img = self.img_original.copy()
        self.display_image()

    def start_perimeter(self):
        if not self.measuring_perimeter and self.px_per_cm:
            self.perimeter_pts.clear()
            self.display_image()
            self.measuring_perimeter = True
            self.btn_perimeter.config(text="Finalizar Perímetro")
        else:
            if len(self.perimeter_pts) > 2:
                self.perimeter_pts.append(self.perimeter_pts[0])
                cv2.line(self.displayed_img, self.perimeter_pts[-2], self.perimeter_pts[-1], (255, 100, 0), 2)
                self.refresh_canvas()

            total = sum(self.euclidean_distance(self.perimeter_pts[i], self.perimeter_pts[i + 1])
                        for i in range(len(self.perimeter_pts) - 1)) / self.px_per_cm

            label = f"Perímetro: {total:.2f} cm\n"
            self.text_box.insert(tk.END, label)
            self.text_box.see(tk.END)
            messagebox.showinfo("Perímetro", label)

            self.measuring_perimeter = False
            self.btn_perimeter.config(text="Perímetro")
            self.btn_area.config(state=tk.NORMAL)

    def calculate_area(self):
        if len(self.perimeter_pts) < 3:
            messagebox.showwarning("Área Insuficiente", "Selecione ao menos 3 pontos para formar um polígono.")
            return

        contour = np.array(self.perimeter_pts[:-1], dtype=np.int32).reshape((-1, 1, 2))
        area_px = cv2.contourArea(contour)
        area_cm2 = area_px / (self.px_per_cm ** 2)

        label = f"Área: {area_cm2:.2f} cm²\n"
        self.text_box.insert(tk.END, label)
        self.text_box.see(tk.END)
        messagebox.showinfo("Área Calculada", label)

        cv2.drawContours(self.displayed_img, [contour], -1, (0, 255, 255), 2)
        self.refresh_canvas()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDistanceApp(root)
    root.mainloop()
