import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.helpers import safe_float, safe_int


def build_pluviometrico_chart(df, maximo, modo_comando):
    chuva_plot = df["Chuva (mm)"].fillna(0.0)

    fig = make_subplots(specs=[[{"secondary_y": False}]])
    cores_barras = []
    contornos_barras = []

    for i, valor in enumerate(chuva_plot):
        v = safe_float(valor)

        if v <= 0:
            cores_barras.append("rgba(70, 88, 110, 0.18)")
            contornos_barras.append("rgba(120, 145, 170, 0.08)")
        elif v >= 30:
            cores_barras.append("rgba(255, 82, 82, 0.92)")
            contornos_barras.append("rgba(255, 214, 214, 0.45)")
        elif v >= 10:
            cores_barras.append("rgba(255, 184, 61, 0.92)")
            contornos_barras.append("rgba(255, 233, 190, 0.35)")
        else:
            cores_barras.append("rgba(64, 189, 248, 0.92)")
            contornos_barras.append("rgba(220, 242, 255, 0.28)")

    fig.add_trace(
        go.Bar(
            x=df["Dia"],
            y=chuva_plot,
            name="Intensidade diária",
            width=0.62,
            marker=dict(
                color=cores_barras,
                line=dict(color=contornos_barras, width=1.2),
            ),
            hovertemplate=(
                "<b>Dia %{x}</b><br>"
                "Chuva: <b>%{y:.1f} mm</b><br>"
                "<extra></extra>"
            ),
        )
    )

    fig.add_hrect(
        y0=0, y1=10,
        fillcolor="rgba(34, 197, 94, 0.035)",
        line_width=0,
    )
    fig.add_hrect(
        y0=10, y1=30,
        fillcolor="rgba(245, 158, 11, 0.045)",
        line_width=0,
    )
    fig.add_hrect(
        y0=30,
        y1=max(60, maximo + 15),
        fillcolor="rgba(255, 82, 82, 0.050)",
        line_width=0,
    )

    fig.add_hline(
        y=10,
        line_dash="dot",
        line_width=1,
        line_color="rgba(100, 255, 170, 0.20)",
    )
    fig.add_hline(
        y=30,
        line_dash="dot",
        line_width=1,
        line_color="rgba(255, 190, 70, 0.22)",
    )

    if maximo > 0:
        idx_max = chuva_plot.idxmax()
        dia_max = safe_int(df.loc[idx_max, "Dia"])
        valor_max = safe_float(chuva_plot.loc[idx_max])

        fig.add_annotation(
            x=dia_max,
            y=valor_max,
            text=f"<b>Pico crítico</b><br>{valor_max:.1f} mm",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1.4,
            arrowcolor="rgba(255,255,255,0.92)",
            ax=46,
            ay=-42,
            font=dict(color="white", size=11),
            bgcolor="rgba(12, 24, 40, 0.92)",
            bordercolor="rgba(255, 214, 214, 0.25)",
            borderwidth=1,
            borderpad=6,
        )

    fig.add_annotation(
        xref="paper",
        yref="y",
        x=1.01,
        y=5,
        text="<b>NORMAL</b>",
        showarrow=False,
        xanchor="left",
        font=dict(size=10, color="rgba(167, 243, 208, 0.85)"),
    )
    fig.add_annotation(
        xref="paper",
        yref="y",
        x=1.01,
        y=20,
        text="<b>ATENÇÃO</b>",
        showarrow=False,
        xanchor="left",
        font=dict(size=10, color="rgba(253, 230, 138, 0.86)"),
    )
    fig.add_annotation(
        xref="paper",
        yref="y",
        x=1.01,
        y=max(40, maximo * 0.75 if maximo > 0 else 40),
        text="<b>CRÍTICO</b>",
        showarrow=False,
        xanchor="left",
        font=dict(size=10, color="rgba(254, 202, 202, 0.88)"),
    )

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.01,
        text="SISTEMA METEOROLÓGICO TÁTICO | OP. CORUMBÁ",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font=dict(size=9, color="rgba(120, 180, 220, 0.55)"),
    )
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.99,
        y=0.01,
        text="UPLINK: ATIVO",
        showarrow=False,
        xanchor="right",
        yanchor="bottom",
        font=dict(size=9, color="rgba(120, 255, 180, 0.70)"),
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(3, 10, 20, 0.96)",
        height=610 if modo_comando else 575,
        margin=dict(l=14, r=18, t=24, b=14),
        bargap=0.22,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(8, 20, 36, 0.98)",
            bordercolor="rgba(103, 232, 249, 0.16)",
            font=dict(color="white", size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.005,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color="rgba(235,245,255,0.92)"),
        ),
        xaxis=dict(
            title="Ciclo diário",
            showgrid=True,
            gridcolor="rgba(120,180,220,0.07)",
            gridwidth=1,
            zeroline=False,
            tickmode="linear",
            dtick=1,
            color="rgba(235,243,255,0.90)",
        ),
        yaxis=dict(
            title="Intensidade diária (mm)",
            showgrid=True,
            gridcolor="rgba(120,180,220,0.07)",
            gridwidth=1,
            zeroline=False,
            color="rgba(235,243,255,0.90)",
        ),
    )

    return fig