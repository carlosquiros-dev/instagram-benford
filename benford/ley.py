"""Ley de Benford: primer dígito, conteo, chi-cuadrado y clasificación."""
import math

from config import CHI_BOT, CHI_POSIBLE_BOT

# Probabilidad de Benford de que un número empiece con el dígito d: log10(1 + 1/d)
BENFORD = {d: math.log10(1 + 1 / d) for d in range(1, 10)}


def primer_digito(n: int) -> int | None:
    """1234 -> 1 ; 0 -> None (el 0 no tiene primer dígito)."""
    return int(str(n)[0]) if n > 0 else None


def contar(numeros: list[int]) -> dict[int, int]:
    """Cuántos números empiezan con 1, con 2, ... con 9."""
    conteo = {d: 0 for d in range(1, 10)}
    for n in numeros:
        d = primer_digito(n)
        if d:
            conteo[d] += 1
    return conteo


def chi_cuadrado(conteo: dict[int, int]) -> float:
    """Distancia entre lo contado y lo que espera Benford."""
    total = sum(conteo.values())
    if total == 0:
        return 0.0
    return sum((conteo[d] - total * BENFORD[d]) ** 2 / (total * BENFORD[d]) for d in range(1, 10))


def clasificar(chi: float) -> str:
    """Humano, Posible bot o Bot según el chi-cuadrado."""
    if chi > CHI_BOT:
        return "Bot"
    if chi > CHI_POSIBLE_BOT:
        return "Posible bot"
    return "Humano"