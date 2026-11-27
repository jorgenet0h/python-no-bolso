import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { funcao, UUID_V4 } from "./contrato";

type ChamarApi = (caminho: string, init?: RequestInit) => Promise<unknown>;

const json = (corpo: unknown, status = 200) =>
  new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });

describe("REQ-015: tentativas ligadas ao device_id, sem cadastro", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.unstubAllGlobals());

  it("test_req_015_cliente_envia_x_device_id_uuid_sem_credenciais", async () => {
    const chamar = await funcao<ChamarApi>("lib/api", "chamarApi", "REQ-015");
    const fetchFalso = vi.fn().mockResolvedValue(json({ ok: true }));
    vi.stubGlobal("fetch", fetchFalso);
    await chamar("/progresso");
    const init = fetchFalso.mock.calls[0][1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get("x-device-id")).toMatch(UUID_V4);
    expect(headers.get("authorization")).toBeNull();
    expect(init.credentials === undefined || init.credentials === "omit").toBe(true);
  });
});
