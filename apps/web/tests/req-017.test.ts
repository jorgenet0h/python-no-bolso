import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { funcao } from "./contrato";

type ChamarApi = (caminho: string, init?: RequestInit) => Promise<unknown>;
type ErroApi = { code?: string; message?: string } | null;

const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

const capturaErro = (p: Promise<unknown>) =>
  p.then(
    () => null,
    (e: unknown) => e as ErroApi,
  );

const deviceDaChamada = (chamada: unknown[]) =>
  new Headers((chamada[1] as RequestInit).headers).get("x-device-id");

describe("REQ-017: sem conexão, erro amigável e nova tentativa (cliente da API)", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.unstubAllGlobals());

  it("test_req_017_falha_de_rede_vira_erro_amigavel_sem_stack_nem_url", async () => {
    const chamar = await funcao<ChamarApi>("lib/api", "chamarApi", "REQ-017");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const erro = await capturaErro(chamar("/exercicios"));
    expect(erro).not.toBeNull();
    expect(erro?.code).toBeTruthy();
    expect(erro?.message).toBeTruthy();
    expect(String(erro?.message)).not.toMatch(/TypeError|Failed to fetch|localhost/);
  });

  it("test_req_017_permite_tentar_de_novo_e_o_device_id_permanece", async () => {
    const chamar = await funcao<ChamarApi>("lib/api", "chamarApi", "REQ-017");
    const fetchFalso = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(json({ id: "x" }));
    vi.stubGlobal("fetch", fetchFalso);
    await capturaErro(chamar("/exercicios"));
    const antes = Object.values({ ...localStorage });
    await expect(chamar("/exercicios")).resolves.toBeTruthy();
    expect(Object.values({ ...localStorage })).toEqual(antes);
    const [primeira, segunda] = fetchFalso.mock.calls.map(deviceDaChamada);
    expect(primeira).toBe(segunda);
  });

  it("test_req_017_erro_code_message_da_api_chega_ao_chamador", async () => {
    const chamar = await funcao<ChamarApi>("lib/api", "chamarApi", "REQ-017");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(json({ code: "INDISPONIVEL", message: "Tente novamente." }, 503)),
    );
    const erro = await capturaErro(chamar("/exercicios"));
    expect(erro?.code).toBe("INDISPONIVEL");
    expect(erro?.message).toBe("Tente novamente.");
  });
});
