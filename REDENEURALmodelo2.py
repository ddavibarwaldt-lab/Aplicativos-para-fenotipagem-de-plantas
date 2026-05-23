import os
import shutil
import numpy as np
import cv2
import matplotlib.pyplot as plt
import tensorflow as tf
import seaborn as sns

from tkinter import Tk, Button, Label, filedialog, messagebox, StringVar, OptionMenu
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.metrics import classification_report, confusion_matrix

# ================= CONFIGURAÇÕES =================
ESPECIES = ["MALMEANUM", "CHACOENSE", "COMMERSONII"]
SUBCONJUNTOS = ["treino", "validacao"]
TAMANHO_IMAGEM = (128, 128)
BASE_DATASET = "dataset"

# ================= CRIAÇÃO AUTOMÁTICA DAS PASTAS =================
def criar_pastas():
    for subset in SUBCONJUNTOS:
        for especie in ESPECIES:
            caminho = os.path.join(BASE_DATASET, subset, especie)
            os.makedirs(caminho, exist_ok=True)

criar_pastas()

# ================= VALIDAÇÃO DO DATASET =================
def dataset_valido():
    for subset in SUBCONJUNTOS:
        for especie in ESPECIES:
            caminho = os.path.join(BASE_DATASET, subset, especie)
            if not os.path.exists(caminho) or len(os.listdir(caminho)) == 0:
                return False
    return True

# ================= APP =================
class ClassificadorEspeciesApp:

    def __init__(self, root):
        self.root = root
        root.title("Classificador de Espécies")

        self.especie_var = StringVar(root)
        self.especie_var.set(ESPECIES[0])

        Label(root, text="Selecione a Espécie").pack()
        OptionMenu(root, self.especie_var, *ESPECIES).pack()

        Button(root, text="Adicionar Imagens - Treino",
               command=self.selecionar_imagens_treino).pack(pady=5)

        Button(root, text="Adicionar Imagens - Validação",
               command=self.selecionar_imagens_validacao).pack(pady=5)

        Button(root, text="Treinar Modelo",
               command=self.treinar_modelo).pack(pady=5)

        Button(root, text="Reconhecer Imagem",
               command=self.reconhecer_imagem).pack(pady=5)

        self.saida_label = Label(root, text="", fg="blue")
        self.saida_label.pack()

    # ================= SELEÇÃO DE IMAGENS =================
    def selecionar_imagens_treino(self):
        especie = self.especie_var.get()
        destino = os.path.join(BASE_DATASET, "treino", especie)

        arquivos = filedialog.askopenfilenames(
            filetypes=[("Imagens", "*.jpg *.jpeg *.png")]
        )

        for caminho in arquivos:
            nome = os.path.basename(caminho)
            shutil.copy2(caminho, os.path.join(destino, nome))

        messagebox.showinfo("Sucesso",
                            f"{len(arquivos)} imagem(ns) adicionada(s) ao treino.")

    def selecionar_imagens_validacao(self):
        especie = self.especie_var.get()
        destino = os.path.join(BASE_DATASET, "validacao", especie)

        arquivos = filedialog.askopenfilenames(
            filetypes=[("Imagens", "*.jpg *.jpeg *.png")]
        )

        for caminho in arquivos:
            nome = os.path.basename(caminho)
            shutil.copy2(caminho, os.path.join(destino, nome))

        messagebox.showinfo("Sucesso",
                            f"{len(arquivos)} imagem(ns) adicionada(s) à validação.")

    # ================= TREINAMENTO =================
    def treinar_modelo(self):

        if not dataset_valido():
            messagebox.showerror(
                "Erro",
                "Dataset incompleto! Verifique se todas as classes possuem imagens em treino e validação."
            )
            return

        treino_path = os.path.join(BASE_DATASET, "treino")
        validacao_path = os.path.join(BASE_DATASET, "validacao")

        datagen_treino = ImageDataGenerator(rescale=1./255)
        datagen_validacao = ImageDataGenerator(rescale=1./255)

        treino = datagen_treino.flow_from_directory(
            treino_path,
            target_size=TAMANHO_IMAGEM,
            batch_size=16,
            class_mode='categorical',
            shuffle=True
        )

        validacao = datagen_validacao.flow_from_directory(
            validacao_path,
            target_size=TAMANHO_IMAGEM,
            batch_size=16,
            class_mode='categorical',
            shuffle=False
        )

        modelo = Sequential([
            Conv2D(16, (3,3), activation='relu', input_shape=(128,128,3)),
            MaxPooling2D((2,2)),
            Conv2D(32, (3,3), activation='relu'),
            MaxPooling2D((2,2)),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(len(ESPECIES), activation='softmax')
        ])

        modelo.compile(
            optimizer=Adam(0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )

        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.3,
            patience=3,
            min_lr=1e-6
        )

        modelo.fit(
            treino,
            epochs=20,
            validation_data=validacao,
            callbacks=[early_stop, reduce_lr]
        )

        modelo.save("papafull.h5")

        # ===== MÉTRICAS =====
        validacao.reset()
        predicoes = modelo.predict(validacao)
        y_pred = np.argmax(predicoes, axis=1)
        y_true = validacao.classes

        print("\n===== RELATÓRIO DE CLASSIFICAÇÃO =====\n")
        print(classification_report(
            y_true,
            y_pred,
            target_names=validacao.class_indices.keys()
        ))

        cm = confusion_matrix(y_true, y_pred)

        plt.figure(figsize=(6,5))
        sns.heatmap(cm, annot=True, fmt="d",
                    xticklabels=validacao.class_indices.keys(),
                    yticklabels=validacao.class_indices.keys())
        plt.xlabel("Predito")
        plt.ylabel("Real")
        plt.title("Matriz de Confusão")
        plt.show()

        messagebox.showinfo("Treinamento",
                            "Modelo treinado com métricas completas!")

    # ================= RECONHECIMENTO =================
    def reconhecer_imagem(self):
        if not os.path.exists("papafull.h5"):
            messagebox.showerror("Erro", "Treine o modelo primeiro.")
            return

        caminho = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.jpg *.jpeg *.png")]
        )

        if not caminho:
            return

        modelo = load_model("papafull.h5")
        class_names = sorted(os.listdir(os.path.join(BASE_DATASET, "treino")))

        img = cv2.imread(caminho)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img_resized = cv2.resize(img_rgb, TAMANHO_IMAGEM)
        img_resized = img_resized.astype("float32") / 255.0
        img_resized = np.expand_dims(img_resized, axis=0)

        pred = modelo.predict(img_resized)[0]
        indice = np.argmax(pred)
        especie = class_names[indice]
        confianca = pred[indice]

        self.saida_label.config(
            text=f"{especie} ({confianca*100:.2f}%)"
        )

        plt.figure(figsize=(6,6))
        plt.imshow(img_rgb)
        plt.title(f"{especie} ({confianca*100:.1f}%)")
        plt.axis("off")
        plt.show()


# ================= MAIN =================
if __name__ == "__main__":
    root = Tk()
    app = ClassificadorEspeciesApp(root)
    root.mainloop()