import os
import shutil
import numpy as np
import cv2
import matplotlib.pyplot as plt
from tkinter import Tk, Button, Label, filedialog, messagebox, StringVar, OptionMenu
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Configurações
ESPECIES = ["MALMEANUM", "CHACOENSE", "COMMERSONII"]
SUBCONJUNTOS = ["treino", "validacao"]
IMAGENS_NECESSARIAS = {"treino": 500, "validacao": 220}
TAMANHO_IMAGEM = (720, 720)

# Criação das pastas
def criar_pastas(base_path="dataset"):
    for subset in SUBCONJUNTOS:
        for especie in ESPECIES:
            caminho = os.path.join(base_path, subset, especie)
            os.makedirs(caminho, exist_ok=True)

criar_pastas()

def aplicar_filtros_coloridos(img):
    # Apenas espelhamento horizontal para aumentar o dataset
    filtros = []
    espelhada = cv2.flip(img, 1)
    filtros.append(espelhada)
    return filtros

def aumentar_dataset_para_500(especie, base_dir='dataset', target_size=(720, 720)):
    destino = os.path.join(base_dir, 'treino', especie)
    imagens_existentes = [f for f in os.listdir(destino) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_atual = len(imagens_existentes)

    if total_atual >= 500:
        print(f"{especie}: Já possui {total_atual} imagens (treino).")
        return

    print(f"{especie}: Aumentando treino de {total_atual} para 500 imagens...")

    imagens = []
    for img_name in imagens_existentes:
        img_path = os.path.join(destino, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, target_size)
        imagens.append(img_resized)

    count = total_atual
    idx = 0

    while count < 500 and idx < len(imagens):
        img = imagens[idx]
        filtros = aplicar_filtros_coloridos(img)

        for i, filtrada in enumerate(filtros):
            nome = f'aug_train_{count}_{i}.jpg'
            caminho_saida = os.path.join(destino, nome)
            img_bgr = cv2.cvtColor(filtrada, cv2.COLOR_RGB2BGR)
            cv2.imwrite(caminho_saida, img_bgr)
            count += 1
            if count >= 500:
                break

        idx += 1
        if idx >= len(imagens):
            idx = 0

    print(f"{especie}: Treino aumentado para {count} imagens.")

def aumentar_dataset_validacao_para_220(especie, base_dir='dataset', target_size=(720, 720)):
    destino = os.path.join(base_dir, 'validacao', especie)
    imagens_existentes = [f for f in os.listdir(destino) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    total_atual = len(imagens_existentes)

    if total_atual >= 220:
        print(f"{especie} (validação): Já possui {total_atual} imagens.")
        return

    print(f"{especie} (validação): Aumentando de {total_atual} para 220 imagens...")

    imagens = []
    for img_name in imagens_existentes:
        img_path = os.path.join(destino, img_name)
        img = cv2.imread(img_path)
        if img is None:
            continue
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, target_size)
        imagens.append(img_resized)

    count = total_atual
    idx = 0

    while count < 220 and idx < len(imagens):
        img = imagens[idx]
        filtros = aplicar_filtros_coloridos(img)

        for i, filtrada in enumerate(filtros):
            nome = f'aug_val_{count}_{i}.jpg'
            caminho_saida = os.path.join(destino, nome)
            img_bgr = cv2.cvtColor(filtrada, cv2.COLOR_RGB2BGR)
            cv2.imwrite(caminho_saida, img_bgr)
            count += 1
            if count >= 220:
                break

        idx += 1
        if idx >= len(imagens):
            idx = 0

    print(f"{especie} (validação): Aumentado para {count} imagens.")

def aumentar_todas_as_especies():
    for especie in ESPECIES:
        aumentar_dataset_para_500(especie)
    messagebox.showinfo("Aumento Concluído", "Treino de todas as espécies agora tem pelo menos 500 imagens.")

def aumentar_todas_validacao():
    for especie in ESPECIES:
        aumentar_dataset_validacao_para_220(especie)
    messagebox.showinfo("Aumento Concluído", "Validação de todas as espécies agora tem pelo menos 220 imagens.")

class ClassificadorEspeciesApp:
    def __init__(self, root):
        self.root = root
        root.title("Classificador de Espécies")

        self.especie_var = StringVar(root)
        self.especie_var.set(ESPECIES[0])

        Label(root, text="Espécie:").pack()
        OptionMenu(root, self.especie_var, *ESPECIES).pack()

        Button(root, text="Adicionar imagens - Treino", command=self.selecionar_imagens_treino).pack(pady=5)
        Button(root, text="Adicionar imagens - Validação", command=self.selecionar_imagens_validacao).pack(pady=5)
        Button(root, text="Aumentar Dataset Treino para 500", command=self.aumentar_todas).pack(pady=5)
        Button(root, text="Aumentar Dataset Validação para 220", command=self.aumentar_todas_validacao).pack(pady=5)
        Button(root, text="Treinar Modelo Geral", command=self.treinar_modelo_especies).pack(pady=5)
        Button(root, text="Reconhecer Espécie (Imagem do PC)", command=self.reconhecer_imagem_pc).pack(pady=5)
        Button(root, text="Reconhecer Espécie (Webcam)", command=self.reconhecer_webcam).pack(pady=5)

        self.saida_label = Label(root, text="", fg="blue")
        self.saida_label.pack()

    def atualizar_saida(self, texto):
        self.saida_label.config(text=texto)

    def aumentar_todas(self):
        aumentar_todas_as_especies()

    def aumentar_todas_validacao(self):
        aumentar_todas_validacao()

    def selecionar_imagens_treino(self):
        especie = self.especie_var.get()
        destino = os.path.join("dataset", "treino", especie)
        os.makedirs(destino, exist_ok=True)
        arquivos = filedialog.askopenfilenames(filetypes=[("Imagens", "*.jpg *.jpeg *.png")])

        if arquivos:
            for caminho in arquivos:
                nome_arquivo = os.path.basename(caminho)
                shutil.copy2(caminho, os.path.join(destino, nome_arquivo))
            messagebox.showinfo("Sucesso", f"{len(arquivos)} imagem(ns) adicionada(s) para treino de '{especie}'.")

    def selecionar_imagens_validacao(self):
        especie = self.especie_var.get()
        destino = os.path.join("dataset", "validacao", especie)
        os.makedirs(destino, exist_ok=True)
        arquivos = filedialog.askopenfilenames(filetypes=[("Imagens", "*.jpg *.jpeg *.png")])

        if arquivos:
            for caminho in arquivos:
                nome_arquivo = os.path.basename(caminho)
                shutil.copy2(caminho, os.path.join(destino, nome_arquivo))
            messagebox.showinfo("Sucesso", f"{len(arquivos)} imagem(ns) adicionada(s) para validação de '{especie}'.")

    def treinar_modelo_especies(self):
        datagen_treino = ImageDataGenerator(rescale=1. / 255)
        datagen_validacao = ImageDataGenerator(rescale=1. / 255)

        treino_dir = os.path.join('dataset', 'treino')
        val_dir = os.path.join('dataset', 'validacao')

        treino = datagen_treino.flow_from_directory(
            treino_dir,
            target_size=TAMANHO_IMAGEM,
            batch_size=16,
            class_mode='categorical',
            shuffle=True
        )

        validacao = datagen_validacao.flow_from_directory(
            val_dir,
            target_size=TAMANHO_IMAGEM,
            batch_size=16,
            class_mode='categorical',
            shuffle=False
        )

        modelo = Sequential([
            Conv2D(16, (3, 3), activation='relu', input_shape=(720, 720, 3)),
            MaxPooling2D((2, 2)),
            Conv2D(32, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            Flatten(),
            Dense(720, activation='relu'),
            Dropout(0.5),
            Dense(len(ESPECIES), activation='softmax')
        ])

        modelo.compile(optimizer=Adam(0.0001), loss='categorical_crossentropy', metrics=['accuracy'])

        historico = modelo.fit(
            treino,
            epochs=100,
            validation_data=validacao
        )

        modelo.save("modelonespecies.h5")

        plt.figure()
        plt.plot(historico.history['accuracy'], label='Treino')
        plt.plot(historico.history['val_accuracy'], label='Validação')
        plt.legend()
        plt.title("Acurácia - Classificação de Espécies")
        plt.xlabel("Épocas")
        plt.ylabel("Acurácia")
        plt.show()

        messagebox.showinfo("Treinamento", "Modelo geral de espécies treinado e salvo!")

    def reconhecer_imagem_pc(self):
        modelo_path = "modelonespecies.h5"

        if not os.path.exists(modelo_path):
            messagebox.showerror("Erro", "O modelo de espécies ainda não foi treinado.")
            return

        caminho_imagem = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.jpeg *.png")])
        if not caminho_imagem:
            return

        modelo = load_model(modelo_path)
        class_names = sorted(os.listdir(os.path.join("dataset", "treino")))

        corrigir_labels = {
            "CHACOENSE": "CHACOENSE",
            "COMMERSONII": "COMMERSONII",
            "MALMEANUM": "MALMEANUM"
        }

        imagem = cv2.imread(caminho_imagem)
        imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
        imagem_redimensionada = cv2.resize(imagem_rgb, TAMANHO_IMAGEM)
        imagem_redimensionada = imagem_redimensionada.astype("float32") / 255.0
        imagem_redimensionada = np.expand_dims(imagem_redimensionada, axis=0)

        pred = modelo.predict(imagem_redimensionada, verbose=0)[0]
        indice = np.argmax(pred)
        especie_errada = class_names[indice]
        especie = corrigir_labels.get(especie_errada, especie_errada)
        confianca = pred[indice]

        self.atualizar_saida(f"Espécie detectada: {especie}\nPrecisão: {confianca * 100:.2f}%")

        plt.imshow(imagem_rgb)
        plt.title(f"Espécie: {especie} ({confianca * 100:.1f}%)")
        plt.axis('off')
        plt.show()

    def reconhecer_webcam(self):
        modelo_path = "modelonespecies.h5"

        if not os.path.exists(modelo_path):
            messagebox.showerror("Erro", "O modelo de espécies ainda não foi treinado.")
            return

        modelo = load_model(modelo_path)
        class_names = sorted(os.listdir(os.path.join("dataset", "treino")))

        corrigir_labels = {
            "COMMERSONII": "COMMERSONII",
            "CHACOENSE": "CHACOENSE",
            "MALMEANUM": "MALMEANUM"
        }

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Erro", "Não foi possível acessar a webcam.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            imagem_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imagem_redimensionada = cv2.resize(imagem_rgb, TAMANHO_IMAGEM)
            imagem_redimensionada = imagem_redimensionada.astype("float32") / 255.0
            imagem_redimensionada = np.expand_dims(imagem_redimensionada, axis=0)

            pred = modelo.predict(imagem_redimensionada, verbose=0)[0]
            indice = np.argmax(pred)
            especie_errada = class_names[indice]
            especie = corrigir_labels.get(especie_errada, especie_errada)
            confianca = pred[indice]

            texto = f"{especie}: {confianca * 100:.1f}%"
            cv2.putText(frame, texto, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Reconhecimento de Espécies - Pressione 'q' para sair", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    root = Tk()
    app = ClassificadorEspeciesApp(root)
    root.mainloop()
