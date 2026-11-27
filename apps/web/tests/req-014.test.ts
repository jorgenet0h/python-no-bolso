import { beforeEach, describe, expect, it, vi } from "vitest";
import { funcao, UUID_V4 } from "./contrato";

type ObterDeviceId = () => string;

const valores = () => Object.values({ ...localStorage });

describe("REQ-014: aparelho sem device_id gera um UUID e guarda localmente", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("test_req_014_gera_uuid_v4_e_guarda_no_localstorage", async () => {
    const obter = await funcao<ObterDeviceId>("lib/device-id", "obterDeviceId", "REQ-014");
    const id = obter();
    expect(id).toMatch(UUID_V4);
    expect(valores()).toContain(id);
  });

  it("test_req_014_reusa_o_id_ja_guardado_em_chamadas_seguintes", async () => {
    const obter = await funcao<ObterDeviceId>("lib/device-id", "obterDeviceId", "REQ-014");
    const primeiro = obter();
    expect(obter()).toBe(primeiro);
    expect(obter()).toBe(primeiro);
    expect(Object.keys({ ...localStorage })).toHaveLength(1);
  });

  it("test_req_014_valor_corrompido_no_storage_e_substituido_por_uuid_valido", async () => {
    const obter = await funcao<ObterDeviceId>("lib/device-id", "obterDeviceId", "REQ-014");
    obter();
    const chave = Object.keys({ ...localStorage })[0];
    const lixo = "'; DROP TABLE tentativas; --";
    localStorage.setItem(chave, lixo);
    const novo = obter();
    expect(novo).toMatch(UUID_V4);
    expect(novo).not.toBe(lixo);
  });

  it("test_req_014_localstorage_indisponivel_nao_quebra_o_app", async () => {
    const obter = await funcao<ObterDeviceId>("lib/device-id", "obterDeviceId", "REQ-014");
    const bloqueado = () => {
      throw new DOMException("bloqueado", "SecurityError");
    };
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(bloqueado);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(bloqueado);
    expect(obter()).toMatch(UUID_V4);
  });
});
