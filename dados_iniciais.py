import banco
from validacoes import chave_documento, validar_formulario


def main():
    conn = banco.conectar_banco()
    try:
        if banco.listar_pessoas(conn):
            print("Banco já contém cadastros. Demonstração não inserida.")
            return
        ids = []
        for nome, grupo, categoria, documento in (
            ("Voluntária de exemplo", "Voluntário", "Voluntário de atendimento", "52998224725"),
            ("Família de exemplo A", "Beneficiário", "Família em situação de vulnerabilidade", "DEMO-002"),
            ("Família de exemplo B", "Beneficiário", "Família em situação de vulnerabilidade", "DEMO-003"),
        ):
            dados = {c: "" for c in banco.CAMPOS}
            dados.update(nome=nome, grupo=grupo, categoria=categoria, documento=documento,
                         nascimento="01/01/2000", telefone="11900000000")
            erros = validar_formulario(dados, conn)
            if erros:
                raise ValueError(erros)
            ids.append(banco.salvar(conn, dados, chave_documento(documento)))
        for i, atividade in ((0,"Recepção"), (0,"Oficina"), (1,"Encontro"), (1,"Oficina")):
            banco.registrar_participacao(conn, ids[i], atividade, "2026-11-01")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
