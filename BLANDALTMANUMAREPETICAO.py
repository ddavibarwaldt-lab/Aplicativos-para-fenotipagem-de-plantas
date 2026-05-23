import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4

# ===== Função para gerar arquivo Excel de exemplo =====
def gerar_exemplo():
    sementes = 15  # número de sementes de exemplo
    data = []

    for semente in range(1, sementes + 1):
        medida_paq = np.round(np.random.uniform(4.5, 5.5), 2)
        medida_app = np.round(medida_paq + np.random.normal(0, 0.05), 2)
        data.append([semente, medida_paq, medida_app])

    df = pd.DataFrame(data, columns=['semente', 'medida_paquimetro', 'medida_app'])
    caminho = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if caminho:
        df.to_excel(caminho, index=False)
        messagebox.showinfo("Arquivo de Exemplo", f"Arquivo salvo em: {caminho}")

# ===== Função para carregar arquivo e processar =====
def carregar_arquivo():
    caminho = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if not caminho:
        return
    try:
        df = pd.read_excel(caminho)
        colunas_esperadas = ['semente', 'medida_paquimetro', 'medida_app']
        for col in colunas_esperadas:
            if col not in df.columns:
                messagebox.showerror("Erro", f"Coluna '{col}' não encontrada no arquivo")
                return
        processar(df, caminho)
    except Exception as e:
        messagebox.showerror("Erro", str(e))

# ===== Função para processar, gerar Bland–Altman, salvar Excel e PDF =====
def processar(df, arquivo_origem):
    # Cada linha já é uma semente única
    df['dif'] = df['medida_app'] - df['medida_paquimetro']
    df['media'] = (df['medida_app'] + df['medida_paquimetro']) / 2

    d_mean = df['dif'].mean()
    sd_d = df['dif'].std()
    loa_sup = d_mean + 1.96 * sd_d
    loa_inf = d_mean - 1.96 * sd_d

    # Pontos fora dos limites
    fora_limites = ((df['dif'] < loa_inf) | (df['dif'] > loa_sup)).sum()
    perc_fora = (fora_limites / len(df)) * 100

    # ===== INTERPRETAÇÃO =====
    interpretacao = f"""
<b>Resumo numérico:</b><br/>
- Diferença média (App - Paquímetro): {d_mean:.3f}<br/>
- Limites de concordância (95%): {loa_inf:.3f} a {loa_sup:.3f}<br/>
- Pontos fora dos limites: {fora_limites} de {len(df)} ({perc_fora:.1f}%)<br/><br/>
"""

    if abs(d_mean) < 0.05:
        interpretacao += "👉 O viés médio é <b>muito pequeno</b>: o app mede praticamente igual ao paquímetro.<br/>"
    elif abs(d_mean) < 0.1:
        interpretacao += "👉 O viés médio é <b>moderado</b>: o app tende a ter pequena diferença sistemática.<br/>"
    else:
        interpretacao += "👉 O viés médio é <b>alto</b>: o app mede de forma diferente do paquímetro.<br/>"

    if perc_fora <= 5:
        interpretacao += "👉 Quase todos os pontos estão dentro dos limites → <b>boa concordância</b>.<br/>"
    elif perc_fora <= 15:
        interpretacao += "👉 Alguns pontos fora dos limites → <b>atenção a possíveis discrepâncias</b>.<br/>"
    else:
        interpretacao += "👉 Muitos pontos fora dos limites → <b>baixa concordância</b>.<br/>"

    if abs(d_mean) < 0.05 and perc_fora <= 5:
        interpretacao += "<br/><b>Conclusão:</b> O aplicativo apresenta ótima concordância com o paquímetro."
    elif abs(d_mean) < 0.1 and perc_fora <= 15:
        interpretacao += "<br/><b>Conclusão:</b> O aplicativo apresenta concordância aceitável, mas recomenda-se cautela em medidas críticas."
    else:
        interpretacao += "<br/><b>Conclusão:</b> O aplicativo não apresenta boa concordância e não é recomendado como substituto do paquímetro."

    # Mostrar resumo em janela
    messagebox.showinfo("Resultados Bland–Altman", interpretacao.replace("<br/>", "\n"))

    # ===== Gráfico =====
    plt.figure(figsize=(8,5))
    plt.scatter(df['media'], df['dif'], color='blue')
    plt.axhline(d_mean, color='red', linestyle='--', label='Diferença média')
    plt.axhline(loa_sup, color='green', linestyle='--', label='Limite superior')
    plt.axhline(loa_inf, color='green', linestyle='--', label='Limite inferior')
    plt.xlabel('Média dos métodos')
    plt.ylabel('Diferença (App - Paquímetro)')
    plt.title('Gráfico de Bland–Altman')
    plt.legend()
    caminho_fig = arquivo_origem.replace('.xlsx', '_bland_altman.png')
    plt.savefig(caminho_fig, dpi=300, bbox_inches="tight")
    plt.close()

    # ===== Salvar Excel =====
    caminho_saida = arquivo_origem.replace('.xlsx', '_bland_altman.xlsx')
    resumo = pd.DataFrame({
        "Métrica": ["Diferença média", "Limite inferior (95%)", "Limite superior (95%)", "Pontos fora (%)"],
        "Valor": [d_mean, loa_inf, loa_sup, perc_fora]
    })
    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dados Processados", index=False)
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

    # ===== Gerar PDF =====
    caminho_pdf = arquivo_origem.replace('.xlsx', '_laudo.pdf')
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    styles = getSampleStyleSheet()
    estilo_texto = ParagraphStyle('custom', parent=styles['Normal'], fontName='HeiseiKakuGo-W5', fontSize=11, leading=14)

    story = []
    story.append(Paragraph("<b>Laudo Bland–Altman</b>", styles['Title']))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(interpretacao, estilo_texto))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("<b>Gráfico de Bland–Altman:</b>", styles['Heading2']))
    story.append(Image(caminho_fig, width=6*inch, height=4*inch))
    story.append(Spacer(1, 0.5*inch))

    # Rodapé
    data_analise = datetime.now().strftime("%d/%m/%Y %H:%M")
    referencia = ("Bland JM, Altman DG. Statistical methods for assessing agreement between "
                  "two methods of clinical measurement. Lancet. 1986;327(8476):307–310.")
    rodape = f"<br/><br/><i>Arquivo analisado: {arquivo_origem.split('/')[-1]}<br/>Data da análise: {data_analise}<br/><br/>Referência: {referencia}</i>"
    story.append(Paragraph(rodape, estilo_texto))

    doc = SimpleDocTemplate(caminho_pdf, pagesize=A4)
    doc.build(story)

    messagebox.showinfo("Arquivos Salvos", f"Resultados salvos em:\n{caminho_saida}\n{caminho_pdf}")

# ===== Função para mostrar fórmulas =====
def mostrar_formulas():
    texto = """
Fórmulas usadas no teste Bland–Altman:

1. Diferença entre os métodos:
   dif = Medida_App – Medida_Paquimetro

2. Média entre os métodos:
   media = (Medida_App + Medida_Paquimetro) / 2

3. Viés médio (diferença média):
   d̄ = média(dif)

4. Desvio padrão das diferenças:
   SD = desvio_padrão(dif)

5. Limites de concordância (95%):
   Limite superior = d̄ + 1,96 × SD
   Limite inferior = d̄ – 1,96 × SD

6. Percentual de pontos fora dos limites:
   %fora = (nº pontos fora / nº total) × 100
    """
    messagebox.showinfo("Fórmulas Bland–Altman", texto)

# ===== Interface Tkinter =====
root = tk.Tk()
root.title("Bland–Altman App")
root.geometry("500x250")

label = tk.Label(root, text="Escolha uma opção abaixo:", font=("Arial", 12))
label.pack(pady=10)

botao_exemplo = tk.Button(root, text="Gerar arquivo de exemplo", command=gerar_exemplo, width=30)
botao_exemplo.pack(pady=5)

botao_arquivo = tk.Button(root, text="Selecionar arquivo Excel", command=carregar_arquivo, width=30)
botao_arquivo.pack(pady=5)

botao_formulas = tk.Button(root, text="Mostrar fórmulas matemáticas", command=mostrar_formulas, width=30)
botao_formulas.pack(pady=5)

root.mainloop()
