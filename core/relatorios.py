from io import BytesIO
from textwrap import wrap

from config import APP_TITLE
from core.helpers import formatar_datahora_local, safe_float


def gerar_relatorio_pdf_bytes(ano, mes, resumo_dict, parecer, previsao_df):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.lib import colors
    except Exception:
        return None

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 4 * cm

    def nova_pagina_se_preciso(y_atual, fonte="Helvetica", tamanho=10):
        if y_atual < 3 * cm:
            c.showPage()
            return height - 2 * cm
        c.setFont(fonte, tamanho)
        return y_atual

    def escrever_linhas(texto, x, y_atual, largura=95, fonte="Helvetica", tamanho=10, passo=0.5 * cm):
        c.setFont(fonte, tamanho)
        for linha in wrap(str(texto), width=largura):
            y_atual = nova_pagina_se_preciso(y_atual, fonte, tamanho)
            c.drawString(x, y_atual, linha)
            y_atual -= passo
        return y_atual

    c.setFillColor(colors.HexColor("#0b1b30"))
    c.rect(0, height - 3 * cm, width, 3 * cm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, height - 1.35 * cm, "RELATÓRIO EXECUTIVO METEOROLÓGICO")
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, height - 2.05 * cm, APP_TITLE)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, f"Período: {mes:02d}/{ano}")
    y -= 0.7 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Emitido em: {formatar_datahora_local()}")
    y -= 1.0 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Resumo do período")
    y -= 0.6 * cm

    for chave, valor in resumo_dict.items():
        y = escrever_linhas(f"- {chave}: {valor}", 2.2 * cm, y)

    y -= 0.3 * cm
    y = nova_pagina_se_preciso(y, "Helvetica-Bold", 12)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Parecer executivo")
    y -= 0.7 * cm

    for linha in parecer.split(". "):
        txt = linha.strip()
        if txt:
            if not txt.endswith("."):
                txt += "."
            y = escrever_linhas(txt, 2.2 * cm, y)

    if not previsao_df.empty:
        y -= 0.3 * cm
        y = nova_pagina_se_preciso(y, "Helvetica-Bold", 12)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Previsão de curto prazo")
        y -= 0.7 * cm

        for _, row in previsao_df.iterrows():
            texto = (
                f"- {row['Data_fmt']}: {row.get('Condição', 'Sem condição')} | "
                f"{safe_float(row['Chuva Prevista (mm)']):.1f} mm | "
                f"{row.get('Decisão', 'Sem decisão')}"
            )
            y = escrever_linhas(texto, 2.2 * cm, y)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
