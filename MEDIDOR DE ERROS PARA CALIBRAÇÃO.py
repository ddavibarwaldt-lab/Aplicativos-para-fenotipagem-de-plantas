import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

class ErroApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Calculadora de Erros")
        self.master.geometry("900x600")

        self.df = None
        self.tree = None
        self.filepath = ""

        # Botões
        self.select_button = tk.Button(master, text="Selecionar Arquivo", command=self.processar_arquivo, font=("Arial", 12), bg="#3F8742", fg="white")
        self.select_button.pack(pady=10)

        self.exemplo_button = tk.Button(master, text="Exemplo de Tabela", command=self.exibir_exemplo, font=("Arial", 11), bg="#B66F04", fg="white")
        self.exemplo_button.pack(pady=5)

        self.formulas_button = tk.Button(master, text="Fórmulas Usadas", command=self.mostrar_formulas, font=("Arial", 11), bg="#63346B", fg="white")
        self.formulas_button.pack(pady=5)

        self.gerar_excel_button = tk.Button(master, text="Gerar Planilha de Exemplo", command=self.gerar_planilha_exemplo, font=("Arial", 11), bg="#795548", fg="white")
        self.gerar_excel_button.pack(pady=5)

        self.tree_frame = tk.Frame(master)
        self.tree_frame.pack(expand=True, fill=tk.BOTH)

        self.save_button = tk.Button(master, text="Salvar como XLSX", command=self.salvar_arquivo, font=("Arial", 12), bg="#0F1D28", fg="white")
        self.save_button.pack(pady=10)
        self.save_button["state"] = tk.DISABLED

    def calcular_erros(self, df):
        for i in range(1, len(df)):
            try:
                valor_real = float(df.iloc[i, 2])
                valor_obtido = float(df.iloc[i, 3])

                erro_absoluto = abs(valor_obtido - valor_real)
                erro_relativo = erro_absoluto / valor_real if valor_real != 0 else None
                erro_percentual = erro_relativo * 100 if erro_relativo is not None else None

                df.iat[i, 4] = round(erro_relativo, 5) if erro_relativo is not None else "Div/0"
                df.iat[i, 5] = f"{round(erro_percentual, 2)}%" if erro_percentual is not None else "Div/0"
                df.iat[i, 6] = round(erro_absoluto, 4)
            except Exception:
                df.iat[i, 4] = df.iat[i, 5] = df.iat[i, 6] = "Erro"
        return df

    def exibir_dataframe(self, df):
        for widget in self.tree_frame.winfo_children():
            widget.destroy()

        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree.configure(yscroll=scrollbar.set)

        self.tree["columns"] = [str(i) for i in range(df.shape[1])]
        self.tree["show"] = "headings"

        for i in range(df.shape[1]):
            header = str(df.iloc[0, i]) if pd.notna(df.iloc[0, i]) else f"Coluna {i+1}"
            self.tree.heading(str(i), text=header)
            self.tree.column(str(i), width=120)

        for row in df.iloc[1:].values.tolist():
            self.tree.insert("", tk.END, values=row)

    def processar_arquivo(self):
        filepath = filedialog.askopenfilename(
            title="Selecione um arquivo Excel ou ODS",
            filetypes=[("Planilhas", "*.xlsx *.xls *.ods")]
        )

        if not filepath:
            return

        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath, engine='openpyxl' if ext == '.xlsx' else None, header=None)
            elif ext == '.ods':
                df = pd.read_excel(filepath, engine='odf', header=None)
            else:
                messagebox.showerror("Erro", "Formato de arquivo não suportado.")
                return

            while df.shape[1] < 7:
                df[df.shape[1]] = ""

            df.iloc[0, 4] = "Erro Relativo"
            df.iloc[0, 5] = "Erro Percentual"
            df.iloc[0, 6] = "Erro Absoluto"

            self.df = self.calcular_erros(df)
            self.exibir_dataframe(self.df)
            self.filepath = filepath
            self.save_button["state"] = tk.NORMAL

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao processar o arquivo:\n{str(e)}")

    def salvar_arquivo(self):
        if self.df is not None:
            salvar_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialfile=os.path.splitext(os.path.basename(self.filepath))[0] + "_com_erros.xlsx"
            )
            if salvar_path:
                try:
                    self.df.to_excel(salvar_path, index=False, header=False)
                    messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{salvar_path}")
                except Exception as e:
                    messagebox.showerror("Erro ao salvar", str(e))

    def exibir_exemplo(self):
        exemplo_janela = tk.Toplevel(self.master)
        exemplo_janela.title("Exemplo de Tabela")
        exemplo_janela.geometry("950x250")

        exemplo_label = tk.Label(exemplo_janela, text="Formato esperado da planilha (com cabeçalho na primeira linha):", font=("Arial", 11))
        exemplo_label.pack(pady=5)

        colunas = ["Repetição", "espécie", "tamanho real aferido com paquimetro", "comprimento aferido aplicativo", "Erro Relativo", "Erro Percentual", "Erro Absoluto"]
        dados = [
            ["1", "batata", "1.14", "1.1", "", "", ""],
            ["2", "batata", "1.12", "1.1", "", "", ""],
            ["3", "batata", "1.22", "1.1", "", "", ""],
            ["4", "batata", "1.14", "1.1", "", "", ""]
        ]

        tree_exemplo = ttk.Treeview(exemplo_janela, columns=colunas, show="headings")
        for col in colunas:
            tree_exemplo.heading(col, text=col)
            tree_exemplo.column(col, width=150)
        for row in dados:
            tree_exemplo.insert("", tk.END, values=row)

        tree_exemplo.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    def mostrar_formulas(self):
        janela = tk.Toplevel(self.master)
        janela.title("Fórmulas Usadas")
        janela.geometry("600x300")

        texto = (
            "📌 Fórmulas Usadas:\n\n"
            "🔸 Erro Absoluto = |Valor Obtido - Valor Real|\n"
            "🔸 Erro Relativo = Erro Absoluto / Valor Real\n"
            "🔸 Erro Percentual = Erro Relativo × 100 (%)\n\n"
            "⚠️ Observação: Se o valor real for zero, o erro relativo e percentual não são calculados (Div/0)."
        )

        label = tk.Label(janela, text=texto, justify="left", font=("Arial", 12), wraplength=580)
        label.pack(padx=20, pady=20)

    def gerar_planilha_exemplo(self):
        salvar_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")],
            initialfile="exemplo_calculadora_erros.xlsx"
        )
        if not salvar_path:
            return

        try:
            dados = [
                ["Repetição", "espécie", "tamanho real aferido com paquimetro", "tamanho aferido com aplicativo", "Erro Relativo", "Erro Percentual", "Erro Absoluto"],
                ["1", "batata", 1.14, 1.1, "", "", ""],
                ["2", "batata", 1.12, 1.1, "", "", ""],
                ["3", "batata", 1.22, 1.1, "", "", ""],
                ["4", "batata", 1.14, 1.1, "", "", ""]
            ]
            df = pd.DataFrame(dados)
            df.to_excel(salvar_path, index=False, header=False)
            messagebox.showinfo("Sucesso", f"Planilha de exemplo salva em:\n{salvar_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar a planilha:\n{str(e)}")

# Iniciar o app
if __name__ == "__main__":
    root = tk.Tk()
    app = ErroApp(root)
    root.mainloop()
