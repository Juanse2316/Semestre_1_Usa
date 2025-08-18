import os
import itertools
import re
import matplotlib.pyplot as plt

OUT_DIR = r"F:\Universidad_USA\assets\imagenes_con_fondo"
os.makedirs(OUT_DIR, exist_ok=True)

OPS = {
    '¬': (5, 1, 'R'),
    '!': (5, 1, 'R'),
    '~': (5, 1, 'R'),
    '∧': (4, 2, 'L'),
    '&': (4, 2, 'L'),
    '∨': (3, 2, 'L'),
    '|': (3, 2, 'L'),
    '→': (2, 2, 'R'),
    '->':(2, 2, 'R'),
    '↔': (1, 2, 'L'),
    '⇔': (1, 2, 'L'),
    '<->':(1, 2, 'L'),
}
VAR_PATTERN = re.compile(r'^[a-z]$')
ORDER = ['p','q','r','s','t']

def tokenize(expr: str):
    expr = expr.strip()
    expr = re.sub(r'\s+', ' ', expr)
    expr = expr.replace('<->',' ⟺ ').replace('->',' ⟶ ')
    spaced = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if expr.startswith('⟺', i):
            spaced.append('⟺'); i+=1; continue
        if expr.startswith('⟶', i):
            spaced.append('⟶'); i+=1; continue
        if ch in '()':
            spaced += [' ', ch, ' ']
        elif ch in ['¬','~','!','∧','&','∨','|','→','↔','⇔']:
            spaced += [' ', ch, ' ']
        else:
            spaced.append(ch)
        i += 1
    s = ''.join(spaced).replace('⟺','<->').replace('⟶','->')
    return [p for p in s.split() if p]

def to_postfix(tokens):
    out, stack = [], []
    for t in tokens:
        if VAR_PATTERN.match(t):
            out.append(t)
        elif t == '(':
            stack.append(t)
        elif t == ')':
            while stack and stack[-1] != '(':
                out.append(stack.pop())
            stack.pop()
        else:
            op = t
            if t == '->': op = '→'
            if t == '<->': op = '↔'
            prec, arity, assoc = OPS[op]
            while stack:
                top = stack[-1]
                if top in OPS:
                    tp, ta, tassoc = OPS[top]
                    if (assoc == 'L' and prec <= tp) or (assoc == 'R' and prec < tp):
                        out.append(stack.pop())
                        continue
                break
            stack.append(op)
    while stack:
        out.append(stack.pop())
    return out

def paren_if_needed(s: str) -> str:
    if any(op in s for op in [' ∧ ', ' ∨ ', ' → ', ' ↔ ']):
        return f"({s})"
    return s

def collect_subformulas(postfix):
    st = []
    subs = []
    for t in postfix:
        if VAR_PATTERN.match(t):
            st.append(t)
            if t not in subs: subs.append(t)
        elif t in OPS:
            prec, arity, _ = OPS[t]
            if arity == 1:
                A = st.pop()
                expr = f"¬{paren_if_needed(A)}"
                st.append(expr)
                if expr not in subs: subs.append(expr)
            else:
                B = st.pop(); A = st.pop()
                if t in ('∧','&'): sym = '∧'
                elif t in ('∨','|'): sym = '∨'
                elif t in ('→','->'): sym = '→'
                elif t in ('↔','⇔','<->'): sym = '↔'
                else: sym = t
                expr = f"{paren_if_needed(A)} {sym} {paren_if_needed(B)}"
                st.append(expr)
                if expr not in subs: subs.append(expr)
    return subs

def eval_expr(expr: str, env: dict) -> bool:
    toks = tokenize(expr)
    pfx = to_postfix(toks)
    st = []
    for t in pfx:
        if VAR_PATTERN.match(t): st.append(env[t])
        elif t in OPS:
            prec, arity, _ = OPS[t]
            if arity == 1: st.append(not st.pop())
            else:
                b = st.pop(); a = st.pop()
                if t in ('∧','&'): st.append(a and b)
                elif t in ('∨','|'): st.append(a or b)
                elif t in ('→','->'): st.append((not a) or b)
                elif t in ('↔','⇔','<->'): st.append(a == b)
    return st[0]

def eval_subs(subs, env):
    return [eval_expr(s, env) for s in subs]

def VF(b): return 'V' if b else 'F'

def render_explicit_table_pdf(expr: str, out_path: str):
    tokens = tokenize(expr)
    postfix = to_postfix(tokens)
    subs = collect_subformulas(postfix)
    vars_found = [v for v in ORDER if v in subs]
    subs_no_vars = [s for s in subs if s not in ORDER]
    headers = vars_found + subs_no_vars
    nvars = len(vars_found)
    rows = []
    for combo in itertools.product([True, False], repeat=nvars):
        env = dict(zip(vars_found, combo))
        vals = [VF(env[v]) for v in vars_found] + [VF(x) for x in eval_subs(subs_no_vars, env)]
        rows.append(vals)
    # Auto size
    # --- tamaño y fuente adaptativos ---
    ncols, nrows = len(headers), len(rows)
    base_fs = 12
    fs = max(6, min(12, int(base_fs - 0.25*(ncols-6) - 0.12*(nrows-8))))

    # --- calcular anchos por columna (mínimo + según longitud de encabezado) ---
    min_abs = 0.5           # ancho mínimo "absoluto" por columna (unidad arbitraria)
    char_unit = 0.08        # cuánto “crece” por carácter del encabezado

    raw_widths = [max(min_abs, char_unit*len(str(h))) for h in headers]
    total_raw = sum(raw_widths)
    colWidths = [w/total_raw for w in raw_widths]   # normalizar a fracciones del eje

    # ajustar ancho de figura según el total deseado (más columnas => más ancho)
    fig_w = max(6, 1.0 * total_raw)                 # 1.0 puedes subirlo si quieres más espacio
    fig_h = max(2.5, 0.55*(nrows + 2))

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis('off')

    # crear la tabla con anchos ya fijados
    table = ax.table(cellText=rows, colLabels=headers, colWidths=colWidths, loc='center')

    # no usar auto_set_column_width (anula colWidths)
    table.auto_set_font_size(False)
    table.set_fontsize(fs)
    table.scale(1.0, 1.2)  # vertical un poco más alto; ajusta si hace falta

    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

formulas = [
    # k) Conclusión conjuntiva sin p (inválido)
    "((p → q) ∧ (p → r)) → (q ∧ r)"

]

pdf_paths = []
for i, fml in enumerate(formulas, start=1):
    out_path = os.path.join(OUT_DIR, f"ercicio_9_tabla_{i:02d}.pdf")
    render_explicit_table_pdf(fml, out_path)
    pdf_paths.append(out_path)