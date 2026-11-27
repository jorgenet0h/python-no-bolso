"""Exceções de domínio tipadas (REQ-031). O handler global as converte em {code, message} (REQ-032)."""


class ErroDominio(Exception):
    code = "ERRO_DOMINIO"
    status_code = 400
    mensagem_padrao = "Erro."

    def __init__(self, message: str | None = None):
        self.message = message or self.mensagem_padrao
        super().__init__(self.message)


class SemExercicio(ErroDominio):
    code = "SEM_EXERCICIO"
    status_code = 404
    mensagem_padrao = "Não há exercício para esse filtro. Tente um filtro mais amplo."


class ExercicioNaoEncontrado(ErroDominio):
    code = "EXERCICIO_NAO_ENCONTRADO"
    status_code = 404
    mensagem_padrao = "Exercício não encontrado."


class RespostaInvalida(ErroDominio):
    code = "RESPOSTA_INVALIDA"
    status_code = 422
    mensagem_padrao = "Resposta inválida."


class FiltroInvalido(ErroDominio):
    code = "FILTRO_INVALIDO"
    status_code = 422
    mensagem_padrao = "Filtro inválido."


class EnumInvalido(ErroDominio):
    code = "ENUM_INVALIDO"
    status_code = 422
    mensagem_padrao = "Valor fora dos valores permitidos."


class DeviceInvalido(ErroDominio):
    code = "DEVICE_INVALIDO"
    status_code = 400
    mensagem_padrao = "Identificador de aparelho ausente ou inválido."


class LimiteExcedido(ErroDominio):
    code = "LIMITE_EXCEDIDO"
    status_code = 429
    mensagem_padrao = "Muitas requisições. Tente de novo em instantes."


class Indisponivel(ErroDominio):
    code = "INDISPONIVEL"
    status_code = 503
    mensagem_padrao = "Serviço temporariamente indisponível. Tente de novo."
