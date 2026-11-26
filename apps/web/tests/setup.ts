/**
 * Node recente expõe um `localStorage` global experimental (sem métodos, sem arquivo) que esconde
 * o do jsdom. Os testes de REQ-014/015/017 dependem do Storage do jsdom, então ele é reinstalado.
 */
type JanelaJsdom = { localStorage: Storage; sessionStorage: Storage; Storage: typeof Storage };
const dom = (globalThis as unknown as { jsdom?: { window: JanelaJsdom } }).jsdom;

if (dom) {
  for (const nome of ["localStorage", "sessionStorage", "Storage"] as const) {
    Object.defineProperty(globalThis, nome, { value: dom.window[nome], configurable: true, writable: true });
  }
}
