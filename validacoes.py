from datetime import date, datetime
import re
import banco

CATEGORIAS = {
    "Voluntário": ("Voluntário de atendimento", "Voluntário de atividades e oficinas",
                   "Voluntário administrativo", "Voluntário de eventos e campanhas", "Voluntário profissional"),
    "Beneficiário": ("Criança", "Adolescente", "Jovem", "Família em situação de vulnerabilidade",
                     "Pessoa em situação de vulnerabilidade social", "Comunidade", "Outros"),
}


def chave_documento(documento):
    return re.sub("[^a-z0-9]", "", documento.lower())


def cpf_valido(chave):
    if not re.fullmatch("[0-9]{11}", chave) or len(set(chave)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(chave[i]) * (tamanho + 1 - i) for i in range(tamanho))
        if int(chave[tamanho]) != (soma * 10 % 11) % 10:
            return False
    return True


def validar_formulario(dados, conn, id_atual=None):
    erros = {}
    grupo = dados["grupo"]
    chave = chave_documento(dados["documento"])
    if grupo not in CATEGORIAS:
        erros["grupo"] = "Escolha o grupo."
    if not dados["nome"]:
        erros["nome"] = "Informe o nome."
    if not 3 <= len(chave) <= 40:
        erros["documento"] = "Informe um documento de 3 a 40 caracteres úteis."
    elif (grupo == "Voluntário" or re.fullmatch("[0-9]{11}", chave)) and not cpf_valido(chave):
        erros["documento"] = "Informe um CPF válido."
    elif banco.documento_em_uso(conn, grupo, chave, id_atual):
        erros["documento"] = "Documento já cadastrado neste grupo."
    try:
        nascimento = datetime.strptime(dados["nascimento"], "%d/%m/%Y").date()
        if nascimento > date.today():
            raise ValueError()
    except ValueError:
        erros["nascimento"] = "Informe uma data válida em DD/MM/AAAA até hoje."
    telefone = re.sub(r"\D", "", dados["telefone"])
    if not re.fullmatch(r"[0-9+(). \-]+", dados["telefone"]) or not re.fullmatch(r"(55)?[0-9]{10,11}", telefone):
        erros["telefone"] = "Informe telefone com DDD e, se necessário, +55."
    if dados["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", dados["email"]):
        erros["email"] = "Confira o e-mail."
    if dados["categoria"] not in CATEGORIAS.get(grupo, ()):
        erros["categoria"] = "Escolha uma categoria do grupo selecionado."
    if dados["categoria"] == "Voluntário profissional" and not dados["especialidade"]:
        erros["especialidade"] = "Informe a especialidade profissional."
    return erros
