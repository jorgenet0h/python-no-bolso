/**
 * Adaptador entre os testes do front e a implementação (mesma ideia de apps/api/tests/contrato.py).
 * Os testes saem da SPEC; o que a spec não fixa (nomes de módulo e funções) fica aqui e está
 * documentado em docs/spec-gaps.md. Falha por requisito não implementado começa com
 * NAO-IMPLEMENTADO, o que separa a categoria A (falta implementar) da B (erro do teste).
 */

export const PREFIXO = "NAO-IMPLEMENTADO";

export function naoImplementado(req: string, detalhe: string): never {
  throw new Error(`${PREFIXO} [${req}] ${detalhe} (contrato proposto em docs/spec-gaps.md)`);
}

type Carregador = () => Promise<Record<string, unknown>>;

// import.meta.glob só lista o que existe: módulo ausente vira entrada ausente, não erro de coleta.
// @ts-ignore import.meta.glob é do Vite; o Next não conhece o tipo
const disponiveis: Record<string, Carregador> = import.meta.glob("../lib/*.{ts,tsx}");

export async function carregar(modulo: string, req: string): Promise<Record<string, unknown>> {
  const nome = modulo.replace(/^lib\//, "");
  const chave = Object.keys(disponiveis).find((k) => /\/lib\/([^/]+)\.tsx?$/.exec(k)?.[1] === nome);
  if (!chave) naoImplementado(req, `módulo '${modulo}' não existe`);
  return disponiveis[chave]();
}

export async function funcao<T>(modulo: string, nome: string, req: string): Promise<T> {
  const mod = await carregar(modulo, req);
  if (typeof mod[nome] !== "function") naoImplementado(req, `'${modulo}.${nome}' não existe`);
  return mod[nome] as T;
}

export const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
