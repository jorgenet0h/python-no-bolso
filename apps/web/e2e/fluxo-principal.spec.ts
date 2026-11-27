import { expect, test, type Page } from "@playwright/test";

/**
 * Dois testes e2e do fluxo principal (pessoa: dev júnior, só celular, tempo picado).
 * Seletores por data-testid: contrato proposto em docs/spec-gaps.md. A semente do banco também:
 * 1 exercício prever_saida/iniciante/variaveis com opção correta = índice 1.
 */

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const id = (page: Page, testid: string) => page.getByTestId(testid);

async function deviceIdGuardado(page: Page): Promise<string | undefined> {
  return page.evaluate(() =>
    Object.values({ ...localStorage }).find((v) =>
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(v),
    ),
  );
}

async function abrirExercicio(page: Page) {
  await page.goto("/");
  await id(page, "iniciar").tap();
  await expect(id(page, "enunciado")).toBeVisible();
}

test("test_e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso", async ({ page }) => {
  // REQ-014: primeiro acesso gera e guarda o device_id.
  await page.goto("/");
  expect((await deviceIdGuardado(page)) ?? "(nenhum device_id no localStorage)").toMatch(UUID_V4);

  // REQ-003/004: recebe exercício, sem gabarito visível.
  await id(page, "iniciar").tap();
  await expect(id(page, "enunciado")).toBeVisible();
  const html = await page.content();
  expect(html).not.toMatch(/"gabarito"|saida_esperada/);

  // REQ-005: nenhuma digitação de código na tela do exercício.
  await expect(page.locator("textarea, input[type=text], [contenteditable=true]")).toHaveCount(0);

  // REQ-007/009: escolhe a opção correta (índice 1) só com toques e vê a explicação.
  await id(page, "opcao-1").tap();
  await id(page, "confirmar").tap();
  await expect(id(page, "resultado")).toContainText(/correta|acertou/i);
  await expect(id(page, "explicacao")).not.toBeEmpty();

  // REQ-016: progresso mostra acertos, taxa por tipo e sequência de dias.
  await id(page, "progresso-link").tap();
  await expect(id(page, "total-acertos")).toHaveText(/1/);
  await expect(id(page, "taxa-prever_saida")).toBeVisible();
  await expect(id(page, "sequencia-dias")).toHaveText(/1/);
});

test("test_e2e_02_offline_mostra_erro_amigavel_tenta_de_novo_sem_perder_a_sessao", async ({
  page,
  context,
}) => {
  await abrirExercicio(page);
  const deviceAntes = await deviceIdGuardado(page);
  await id(page, "opcao-0").tap(); // opção errada de propósito (REQ-011)

  // REQ-017: sem conexão, erro amigável e botão de tentar de novo; nada de stack trace.
  await context.setOffline(true);
  await id(page, "confirmar").tap();
  await expect(id(page, "erro-conexao")).toBeVisible();
  await expect(id(page, "erro-conexao")).not.toContainText(/TypeError|Failed to fetch|at \w+\(/);
  await expect(id(page, "tentar-de-novo")).toBeVisible();
  expect(await deviceIdGuardado(page)).toBe(deviceAntes);

  // Volta a conexão: a sessão continua (mesmo exercício, mesma opção) e o reenvio funciona.
  await context.setOffline(false);
  await id(page, "tentar-de-novo").tap();
  await expect(id(page, "resultado")).toContainText(/incorreta|errou|errada/i);
  // REQ-011: explicação do erro da opção escolhida.
  await expect(id(page, "explicacao")).not.toBeEmpty();
  expect(await deviceIdGuardado(page)).toBe(deviceAntes);
});
