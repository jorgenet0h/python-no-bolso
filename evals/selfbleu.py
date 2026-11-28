"""Self-BLEU em Python puro (sem nltk). Quanto MAIOR, mais parecidos entre si os textos gerados
(menos variedade). Cada texto é a hipótese e todos os outros são referências."""

from __future__ import annotations

import math
import re
from collections import Counter


def tokens(texto: str) -> list[str]:
    return re.findall(r"\w+|[^\w\s]", texto.lower())


def _ngramas(toks: list[str], n: int) -> Counter:
    return Counter(tuple(toks[i:i + n]) for i in range(len(toks) - n + 1))


def bleu(hipotese: list[str], referencias: list[list[str]], max_n: int = 4) -> float:
    """BLEU com suavização add-1 nos n-gramas de ordem > 1 e penalidade de brevidade."""
    if not hipotese or not referencias:
        return 0.0
    logs = []
    for n in range(1, max_n + 1):
        hip = _ngramas(hipotese, n)
        total = sum(hip.values())
        if total == 0:
            break
        maximos: Counter = Counter()
        for ref in referencias:
            for gram, c in _ngramas(ref, n).items():
                maximos[gram] = max(maximos[gram], c)
        acertos = sum(min(c, maximos[g]) for g, c in hip.items())
        if n == 1:
            if acertos == 0:
                return 0.0
            logs.append(math.log(acertos / total))
        else:
            logs.append(math.log((acertos + 1) / (total + 1)))
    if not logs:
        return 0.0
    tam_ref = min((len(r) for r in referencias), key=lambda r: abs(r - len(hipotese)))
    bp = 1.0 if len(hipotese) >= tam_ref else math.exp(1 - tam_ref / len(hipotese))
    return bp * math.exp(sum(logs) / len(logs))


def self_bleu(textos: list[str], max_n: int = 4) -> float | None:
    """Média do BLEU de cada texto contra os demais. None se houver menos de 2 textos."""
    toks = [tokens(t) for t in textos]
    if len(toks) < 2:
        return None
    pontos = [bleu(toks[i], toks[:i] + toks[i + 1:], max_n) for i in range(len(toks))]
    return sum(pontos) / len(pontos)
