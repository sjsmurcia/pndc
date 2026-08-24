from app.services.codigo import (
    ALFABETO,
    PREFIJO,
    generar_codigo,
    hashear_codigo,
    normalizar,
    verificar_codigo,
)


def test_formato_del_codigo():
    codigo = generar_codigo()
    partes = codigo.split("-")
    assert partes[0] == PREFIJO
    assert len(partes) == 4
    assert all(len(p) == 4 for p in partes[1:])


def test_sin_caracteres_ambiguos():
    """O/0 e I/1/L se confunden al leer o dictar un codigo."""
    for prohibido in "O0I1L":
        assert prohibido not in ALFABETO


def test_dos_codigos_no_se_repiten():
    codigos = {generar_codigo() for _ in range(200)}
    assert len(codigos) == 200


def test_el_hash_no_contiene_el_codigo():
    """Lo esencial: del hash no se puede leer el codigo."""
    codigo = generar_codigo()
    hash_guardado = hashear_codigo(codigo)
    assert codigo not in hash_guardado
    assert normalizar(codigo) not in hash_guardado


def test_dos_hashes_del_mismo_codigo_difieren():
    """Argon2 usa sal aleatoria: dos hashes del mismo codigo no coinciden,
    y aun asi ambos verifican."""
    codigo = generar_codigo()
    a = hashear_codigo(codigo)
    b = hashear_codigo(codigo)
    assert a != b
    assert verificar_codigo(codigo, a)
    assert verificar_codigo(codigo, b)