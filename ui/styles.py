from pathlib import Path
from base64 import b64encode
import streamlit as st


def carregar_css_externo():
    css_path = Path(__file__).resolve().parent.parent / "styles" / "theme.css"

    if css_path.exists() and css_path.is_file():
        try:
            css = css_path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Falha ao carregar CSS externo: {e}")
    else:
        st.info(f"CSS não encontrado em: {css_path}")


def carregar_imagem_base64(path_str: str) -> str:
    caminho = Path(path_str)
    if not caminho.is_absolute():
        caminho = Path(__file__).resolve().parent.parent / path_str

    if caminho.exists() and caminho.is_file():
        return b64encode(caminho.read_bytes()).decode()
    return ""


def render_icon_html(path_str: str, fallback: str = "•", size: int = 30) -> str:
    b64 = carregar_imagem_base64(path_str)
    if b64:
        return (
            f"<img src='data:image/png;base64,{b64}' "
            f"style='width:{size}px;height:{size}px;object-fit:contain;display:block;'/>"
        )
    return f"<span style='font-size:{size}px'>{fallback}</span>"


def get_bg_css(bg_b64: str) -> str:
    if bg_b64:
        return (
            f'background-image: linear-gradient(180deg, rgba(5,10,18,0.70), '
            f'rgba(8,18,34,0.85)), url("data:image/png;base64,{bg_b64}");'
        )
    return "background: linear-gradient(180deg, #07111d 0%, #10233d 45%, #19395c 100%);"


def get_global_css(modo_comando: bool, bg_css: str) -> str:
    return f"""
<style>
.stApp {{
    {bg_css}
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

[data-testid="stHeader"] {{
    background: rgba(0, 0, 0, 0);
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, rgba(7,16,29,0.98), rgba(13,31,54,0.98));
    border-right: 1px solid rgba(120,180,255,0.12);
}}

.block-container {{
    max-width: {"1880px" if modo_comando else "1500px"};
    padding-top: {"0.35rem" if modo_comando else "0.9rem"};
    padding-bottom: 2rem;
}}

.main-command-box {{
    border-radius: 22px;
    padding: {"18px 24px" if modo_comando else "22px 24px"};
    background:
        radial-gradient(circle at top left, rgba(92,162,255,0.16), transparent 28%),
        linear-gradient(135deg, rgba(13,27,47,0.86), rgba(7,17,31,0.90));
    border: 1px solid rgba(141,196,255,0.16);
    box-shadow:
        0 0 0 1px rgba(112,175,255,0.06),
        0 18px 40px rgba(0,0,0,0.24),
        0 0 30px rgba(68,138,255,0.10);
    margin-bottom: 16px;
}}

.command-kicker {{
    color: #9cc8ff;
    font-size: {"0.95rem" if modo_comando else "0.82rem"};
    letter-spacing: 1.2px;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 6px;
}}

.command-title {{
    color: #f5f9ff;
    font-size: {"2.6rem" if modo_comando else "2.15rem"};
    font-weight: 900;
    line-height: 1.1;
    margin-bottom: 0.35rem;
    text-shadow: 0 0 18px rgba(135,193,255,0.18);
}}

.command-subtitle {{
    color: #d4e6ff;
    font-size: {"1.08rem" if modo_comando else "0.98rem"};
}}

.metric-card {{
    border-radius: 20px;
    padding: {"20px 20px 18px 20px" if modo_comando else "18px 18px 16px 18px"};
    min-height: {"162px" if modo_comando else "148px"};
    background:
        radial-gradient(circle at top left, rgba(118,188,255,0.18), transparent 32%),
        linear-gradient(180deg, rgba(17,40,70,0.92), rgba(9,20,37,0.92));
    border: 1px solid rgba(140,196,255,0.16);
    box-shadow:
        0 14px 32px rgba(0,0,0,0.22),
        0 0 24px rgba(77,146,255,0.08);
}}

.metric-card-head {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}}

.metric-card-label {{
    color: #dceaff;
    font-weight: 700;
    font-size: {"1.08rem" if modo_comando else "0.96rem"};
}}

.metric-card-value {{
    color: #ffffff;
    font-size: {"2.65rem" if modo_comando else "2.15rem"};
    font-weight: 900;
    line-height: 1;
    text-shadow: 0 0 18px rgba(148,202,255,0.16);
}}

.metric-card-sub {{
    color: #bad7ff;
    font-size: {"0.95rem" if modo_comando else "0.86rem"};
    margin-top: 10px;
    line-height: 1.45;
}}

.panel-shell {{
    border-radius: 22px;
    padding: 16px 16px 14px 16px;
    background:
        radial-gradient(circle at top center, rgba(90,160,255,0.08), transparent 24%),
        linear-gradient(180deg, rgba(12,28,50,0.86), rgba(7,17,31,0.92));
    border: 1px solid rgba(137,192,255,0.12);
    box-shadow:
        0 18px 36px rgba(0,0,0,0.20),
        inset 0 1px 0 rgba(255,255,255,0.03);
    margin-bottom: 16px;
}}

.panel-title {{
    color: #f3f8ff;
    font-weight: 900;
    font-size: {"1.18rem" if modo_comando else "1.04rem"};
    margin-bottom: 10px;
    letter-spacing: 0.3px;
}}

.forecast-box {{
    border-radius: 18px;
    padding: 14px;
    min-height: {"220px" if modo_comando else "206px"};
    background:
        radial-gradient(circle at top left, rgba(106,176,255,0.16), transparent 32%),
        linear-gradient(180deg, rgba(24,53,92,0.92), rgba(10,22,40,0.92));
    border: 1px solid rgba(142,198,255,0.14);
    box-shadow:
        0 12px 26px rgba(0,0,0,0.18),
        0 0 18px rgba(87,152,255,0.07);
}}

.forecast-day {{
    color: #f3f8ff;
    font-size: {"1.05rem" if modo_comando else "0.98rem"};
    font-weight: 800;
    margin-bottom: 8px;
}}

.forecast-main {{
    color: #ffffff;
    font-size: {"2.05rem" if modo_comando else "1.8rem"};
    font-weight: 900;
    line-height: 1;
    margin-bottom: 8px;
}}

.forecast-cond {{
    color: #d8e9ff;
    font-size: {"0.98rem" if modo_comando else "0.9rem"};
    min-height: 22px;
    margin-bottom: 8px;
}}

.forecast-temp {{
    color: #bdd8ff;
    font-size: {"0.92rem" if modo_comando else "0.84rem"};
    margin-bottom: 10px;
}}

.forecast-decision {{
    color: #eef6ff;
    font-size: {"0.92rem" if modo_comando else "0.83rem"};
    line-height: 1.4;
}}

.tactical-readout {{
    border-radius: 16px;
    padding: 14px 16px;
    background:
        radial-gradient(circle at top left, rgba(112,182,255,0.10), transparent 30%),
        linear-gradient(180deg, rgba(18,36,60,0.88), rgba(9,19,34,0.88));
    border: 1px solid rgba(139,194,255,0.14);
    box-shadow: 0 10px 24px rgba(0,0,0,0.18);
}}

.tactical-badge {{
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: {"0.92rem" if modo_comando else "0.8rem"};
    font-weight: 800;
    letter-spacing: 0.4px;
    margin-bottom: 10px;
}}

.badge-green {{
    background: rgba(16,185,129,0.16);
    color: #a7f3d0;
    border: 1px solid rgba(16,185,129,0.24);
}}

.badge-blue {{
    background: rgba(59,130,246,0.16);
    color: #bfdbfe;
    border: 1px solid rgba(59,130,246,0.24);
}}

.badge-yellow {{
    background: rgba(250,204,21,0.16);
    color: #fde68a;
    border: 1px solid rgba(250,204,21,0.24);
}}

.badge-red {{
    background: rgba(239,68,68,0.16);
    color: #fecaca;
    border: 1px solid rgba(239,68,68,0.24);
}}

.badge-gray {{
    background: rgba(148,163,184,0.16);
    color: #e2e8f0;
    border: 1px solid rgba(148,163,184,0.24);
}}

.command-mini-card, .alert-auto-box, .front-risk-card {{
    border-radius: 18px;
    padding: 16px 18px;
    background:
        radial-gradient(circle at top left, rgba(96,171,255,0.16), transparent 30%),
        linear-gradient(180deg, rgba(17,38,66,0.92), rgba(8,19,34,0.92));
    border: 1px solid rgba(141,196,255,0.16);
    box-shadow:
        0 12px 24px rgba(0,0,0,0.20),
        0 0 18px rgba(87,152,255,0.07);
    margin-bottom: 16px;
}}

.command-mini-label {{
    color: #9ecbff;
    font-size: {"0.88rem" if modo_comando else "0.78rem"};
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}}

.command-mini-status {{
    color: #ffffff;
    font-size: {"1.85rem" if modo_comando else "1.45rem"};
    font-weight: 900;
    line-height: 1.1;
    margin-bottom: 10px;
}}

.command-mini-line {{
    color: #dceaff;
    font-size: {"1rem" if modo_comando else "0.9rem"};
    line-height: 1.5;
}}

.alert-auto-title {{
    color: #ffffff;
    font-size: {"1.3rem" if modo_comando else "1.18rem"};
    font-weight: 900;
    margin-bottom: 8px;
}}

.alert-auto-text {{
    color: #dceaff;
    font-size: {"1rem" if modo_comando else "0.92rem"};
    line-height: 1.5;
}}

.alert-auto-metrics {{
    margin-top: 10px;
    color: #bdd8ff;
    font-size: {"0.94rem" if modo_comando else "0.84rem"};
    line-height: 1.45;
}}

.map-panel-note {{
    color: #bdd8ff;
    font-size: {"0.95rem" if modo_comando else "0.84rem"};
    margin-bottom: 8px;
}}

.front-risk-title {{
    color: #ffffff;
    font-size: {"1.15rem" if modo_comando else "1rem"};
    font-weight: 800;
    margin-bottom: 6px;
}}

.front-risk-text {{
    color: #dceaff;
    font-size: {"0.96rem" if modo_comando else "0.88rem"};
    line-height: 1.45;
}}

.command-mini-dot {{
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 999px;
    margin-right: 8px;
}}

.dot-green {{
    background: #10b981;
    box-shadow: 0 0 12px rgba(16,185,129,0.55);
}}

.dot-blue {{
    background: #3b82f6;
    box-shadow: 0 0 12px rgba(59,130,246,0.55);
}}

.dot-yellow {{
    background: #facc15;
    box-shadow: 0 0 12px rgba(250,204,21,0.55);
}}

.dot-red {{
    background: #ef4444;
    box-shadow: 0 0 12px rgba(239,68,68,0.55);
}}

.dot-gray {{
    background: #94a3b8;
    box-shadow: 0 0 12px rgba(148,163,184,0.55);
}}

.alerta-piscando {{
    animation: piscarAlerta 1s infinite;
    border-radius: 18px;
    padding: 16px 18px;
    margin-bottom: 16px;
    background: linear-gradient(90deg, rgba(127,29,29,0.92), rgba(220,38,38,0.92));
    border: 1px solid rgba(254,202,202,0.55);
    box-shadow:
        0 0 0 1px rgba(255,255,255,0.05),
        0 0 22px rgba(239,68,68,0.45),
        0 0 40px rgba(239,68,68,0.25);
}}

.alerta-piscando-titulo {{
    color: #ffffff;
    font-size: {"1.45rem" if modo_comando else "1.2rem"};
    font-weight: 900;
    line-height: 1.1;
    margin-bottom: 6px;
    text-transform: uppercase;
}}

.alerta-piscando-texto {{
    color: #fff5f5;
    font-size: {"1.02rem" if modo_comando else "0.92rem"};
    line-height: 1.45;
    font-weight: 700;
}}

@keyframes piscarAlerta {{
    0% {{
        opacity: 1;
        transform: scale(1);
    }}
    50% {{
        opacity: 0.78;
        transform: scale(1.01);
    }}
    100% {{
        opacity: 1;
        transform: scale(1);
    }}
}}

div[data-testid="stDataFrame"] {{
    border-radius: 14px;
    overflow: hidden;
}}

.stButton > button,
.stDownloadButton > button {{
    border-radius: 12px !important;
    width: 100%;
    border: 1px solid rgba(255,255,255,0.08) !important;
}}

div[data-testid="stExpander"] {{
    border: 1px solid rgba(141,196,255,0.10);
    border-radius: 16px;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(12,28,50,0.72), rgba(7,17,31,0.78));
}}

div[data-testid="stExpander"] details summary {{
    font-size: {"1.06rem" if modo_comando else "0.95rem"};
    font-weight: 800;
    color: #eaf3ff;
}}

{"[data-testid='stSidebar'] {display:none;} section[data-testid='stSidebar'] {display:none;}" if modo_comando else ""}
</style>
"""