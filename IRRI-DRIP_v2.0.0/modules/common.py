"""
IRRI-DRIP — shared UI kit, in OpenIrri's visual language.

Every page is built from the same pieces OpenIrri uses: an
``<h1 class="main-header">`` title, an ``info-box`` description, pill tabs,
``st.metric``-style result cards, and the four OpenIrri message boxes
(info / warning / success / error). The functions keep their v1 names so the
engineering pages did not have to be rewritten around a new API.
"""

import html
import json

import streamlit as st

from modules import theme
from modules.theme import COLORS


def _t():
    return theme.tokens()


def inject_css():
    theme.inject()


# --------------------------------------------------------------------------
# State helpers
# --------------------------------------------------------------------------

def save(S, key, payload):
    S[key] = payload


def stage_guard(S, required_key, required_label, page_key=None) -> bool:
    """
    OpenIrri's "Please set up ... first" pattern, with a button that goes
    there. ``page_key`` is the navigation key of the page that produces
    ``required_key`` when the two differ.
    """
    if required_key not in S or not S[required_key]:
        st.warning(f"⚠️ Please complete **{required_label}** first — this page "
                   "inherits its values.")
        if st.button(f"← Go to {required_label}", key=f"guard_{required_key}"):
            st.session_state.page = page_key or required_key
            st.rerun()
        return False
    return True


def goto(page_key: str):
    st.session_state.page = page_key
    st.rerun()


# --------------------------------------------------------------------------
# Page furniture — OpenIrri markup
# --------------------------------------------------------------------------

def page_header(title: str, description: str = ""):
    st.markdown(f'<h1 class="main-header">{html.escape(title)}</h1>',
                unsafe_allow_html=True)
    if description:
        st.markdown(f'<div class="info-box">{description}</div>',
                    unsafe_allow_html=True)


def sub_header(title: str):
    st.markdown(f'<h2 class="sub-header">{html.escape(title)}</h2>',
                unsafe_allow_html=True)


def section(title, subtitle=""):
    """A level-4 heading, as OpenIrri writes them (``#### Title``)."""
    st.markdown(f"#### {title}")
    if subtitle:
        caption(html.escape(subtitle))


_CARD_CLASS = {"ok": "idr-ok", "warn": "idr-warn", "bad": "idr-bad",
               "accent": "idr-accent", "neutral": "idr-neutral"}
_STATUS_TEXT = {"ok": "✓ Normal", "warn": "⚠ Check", "bad": "✗ FAIL"}


def cards(items, columns=4):
    """
    items: (label, value, unit) or (label, value, unit, status),
    status in {"ok","warn","bad","neutral","accent"}. Drawn as OpenIrri
    metric boxes; a status other than neutral/accent adds OpenIrri's status
    pill with a text mark, so the state is never carried by colour alone.
    """
    cells = []
    for it in items:
        label, value, unit = it[0], str(it[1]), it[2]
        status = it[3] if len(it) > 3 else "neutral"
        cls = _CARD_CLASS.get(status, "idr-neutral")
        unit_html = f'<span class="idr-u"> {html.escape(unit)}</span>' if unit else ""
        pill = (f'<div class="idr-s">{_STATUS_TEXT[status]}</div>'
                if status in _STATUS_TEXT else "")
        cells.append(
            f'<div class="idr-card {cls}">'
            f'<div class="idr-k">{html.escape(label)}</div>'
            f'<div class="idr-v">{html.escape(value)}{unit_html}</div>{pill}</div>')
    st.markdown('<div class="idr-cards">' + "".join(cells) + "</div>",
                unsafe_allow_html=True)


def metric_row(items):
    cards(items, columns=max(1, len(items)))


_BOX = {"ok": "success-box", "warn": "warning-box", "bad": "error-box",
        "accent": "info-box"}
_MARK = {"ok": "✓", "warn": "⚠", "bad": "✗", "accent": "ℹ"}


def banner(kind: str, text: str):
    """OpenIrri's info / warning / success / error boxes, with a text mark."""
    colour = {"ok": COLORS["status_ok"], "warn": COLORS["status_warning"],
              "bad": COLORS["status_error"]}.get(kind, COLORS["status_info"])
    st.markdown(
        f'<div class="{_BOX.get(kind, "info-box")}">'
        f'<b style="color:{colour}">{_MARK.get(kind, "ℹ")}</b>&nbsp; {text}</div>',
        unsafe_allow_html=True)


def verdict(ok: bool, ok_text: str, bad_text: str):
    banner("ok" if ok else "bad", html.escape(ok_text if ok else bad_text))


def note(text: str, tight: bool = False):
    st.markdown(f'<div class="info-box idr-note">{text}</div>',
                unsafe_allow_html=True)


def caption(text: str):
    st.markdown(f'<div class="idr-caption">{text}</div>', unsafe_allow_html=True)


def help_field(label: str, explanation: str):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.35rem;'
        f'font-size:0.88rem;font-weight:500">{html.escape(label)}'
        f'<span title="{html.escape(explanation)}" '
        f'style="cursor:help;color:{_t()["muted"]}">ⓘ</span></div>',
        unsafe_allow_html=True)


def welcome(title: str, body: str):
    """OpenIrri's welcome block: an info-box with an h3 and a paragraph."""
    st.markdown(f'<div class="info-box"><h3>{title}</h3><p>{body}</p></div>',
                unsafe_allow_html=True)


def context_strip(S):
    setup = S.get("setup")
    if not setup:
        return
    op = S.get("operation") or {}
    bits = [
        ("Project", setup.get("name") or "untitled"),
        ("Area", f"{setup.get('area_ha', 0):.2f} ha"),
        ("Crop", setup["crop"]["name"]),
        ("Soil", setup["soil"]["name"]),
        ("Source", f"{setup.get('q_avail', 0):.0f} m³/h"),
    ]
    if op.get("n_subunits"):
        bits.append(("Subunits / shifts", f"{op['n_subunits']} / {op['shifts']}"))
    inner = "".join(
        f'<span><span>{html.escape(k)}</span> <b>{html.escape(str(v))}</b></span>'
        for k, v in bits)
    st.markdown(f'<div class="idr-ctx">{inner}</div>', unsafe_allow_html=True)


def save_button(label="💾 Save", key=None) -> bool:
    return st.button(label, type="primary", key=key)


def dev_panel(S, key: str):
    """In Developer Mode, show the stored state of this page."""
    if not st.session_state.get("dev_mode"):
        return
    with st.expander(f"🔧 Developer — stored state `{key}`", expanded=False):
        data = S.get(key)
        if data is None:
            st.markdown('<div class="idr-dev">nothing stored yet</div>',
                        unsafe_allow_html=True)
        else:
            st.code(json.dumps(data, indent=1, default=str)[:20000], language="json")


# --------------------------------------------------------------------------
# Data editors that keep their edits
# --------------------------------------------------------------------------
#
# st.data_editor stores the user's edits as deltas against the frame it was
# given. Feeding the edited frame back in as the next run's input makes the
# base drift under the deltas, and a base that changes shape (a CSV upload,
# a new set of blocks) silently re-applies old edits to new rows. The base is
# therefore held fixed in session state and replaced only deliberately, with
# a new widget key so the old deltas are discarded with it.

def stable_editor(key: str, make_df, **kwargs):
    base_key, ver_key = f"_base_{key}", f"_ver_{key}"
    if base_key not in st.session_state:
        st.session_state[base_key] = make_df()
        st.session_state[ver_key] = 0
    return st.data_editor(st.session_state[base_key],
                          key=f"{key}__v{st.session_state[ver_key]}", **kwargs)


def reset_editor(key: str, df):
    st.session_state[f"_base_{key}"] = df
    st.session_state[f"_ver_{key}"] = st.session_state.get(f"_ver_{key}", 0) + 1


KEEP_KEYS = {"S", "page", "dark_mode_pref", "dev_mode"}


def clear_drafts():
    """Forget every page draft and editor — used when a project is opened or
    a new one started, so no widget carries a value from the previous one."""
    for k in list(st.session_state.keys()):
        if k not in KEEP_KEYS:
            del st.session_state[k]
