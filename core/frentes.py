from core.helpers import safe_float


def gerar_inteligencia_frentes(df_frentes_mapa):
    resultados = []

    if df_frentes_mapa.empty:
        return resultados

    for _, row in df_frentes_mapa.iterrows():
        status = str(row["Status do dia"])
        risco_auto = str(row["Risco automático"])

        if status == "Paralisada":
            impacto = "interrupção da atividade local e perda imediata de produtividade"
            recomendacao = "Manter parada até nova avaliação do encarregado em campo."
        elif status == "Operando com restrição":
            impacto = "redução de mobilidade e execução sob limitação operacional"
            recomendacao = "Operar com controle reforçado e circulação pesada limitada."
        elif status == "Monitoramento":
            impacto = "possível piora gradual ao longo do turno"
            recomendacao = "Acompanhar continuamente a frente e revisar condição durante o dia."
        elif status == "Operando normal":
            impacto = "condição estável para execução normal"
            recomendacao = "Manter rotina operacional e observação padrão."
        else:
            impacto = "frente sem informação operacional lançada para o dia"
            recomendacao = "Registrar atualização da frente para melhorar o quadro operacional."

        resultados.append(
            {
                "id": row["id"],
                "nome": row["Nome"],
                "latitude": safe_float(row["Latitude"]),
                "longitude": safe_float(row["Longitude"]),
                "status": status,
                "observacao": str(row["Observação da frente"]),
                "atualizado": str(row["Atualizado"]),
                "impacto": impacto,
                "recomendacao": recomendacao,
                "risco_auto": risco_auto,
                "pico_prob": safe_float(row["Pico prob. chuva"]),
                "pico_chuva": safe_float(row["Pico chuva"]),
            }
        )

    return resultados