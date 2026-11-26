# Rastreabilidade REQ → teste

Gerada a partir do código dos testes e do resultado da primeira execução. Convenção: o id do
requisito está no nome (`test_req_012_...`). Camadas: **api** (pytest), **web** (Vitest), **e2e** (Playwright),
**evals** (bateria e métricas). Estado: `A` = falha por requisito não implementado, `pass` = passa hoje,
`skip` = só roda em Linux.

| REQ | Requisito | Testes | Estado inicial | Observação |
|---|---|---|---|---|
| REQ-001 | O sistema deve oferecer quatro tipos de exercício: `prever_saida`, `completar_lacuna`, ... | `api` quatro_tipos_de_exercicio_sao_oferecidos | 1×A |  |
| REQ-002 | O sistema deve classificar cada exercício em um nível e um tema dos enums acima. | `api` filtros_malformados_em_exercicios (6)<br>`api` exercicio_tem_nivel_e_tema_dos_enums | 7×A |  |
| REQ-003 | Quando o usuário pedir um exercício, o sistema deve devolver um exercício validado, fil... | `api` devolve_validado_priorizando_nao_resolvidos<br>`e2e` e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso | 2×A |  |
| REQ-004 | O sistema não deve incluir o gabarito na resposta que entrega o exercício ao cliente. | `api` resposta_nao_inclui_gabarito<br>`e2e` e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso | 2×A |  |
| REQ-005 | O sistema deve permitir resolver todos os tipos usando apenas toques, sem digitação de ... | `e2e` e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso | 1×A | Só e2e e só em `prever_saida` (parcial; ver spec-gaps seção 3) |
| REQ-006 | Se não houver exercício validado que atenda ao filtro, então o sistema deve devolver o ... | `api` sem_exercicio_devolve_erro_com_sugestao | 1×A |  |
| REQ-007 | Quando o usuário enviar uma resposta, o sistema deve compará-la ao gabarito armazenado ... | `api` compara_ao_gabarito_e_informa<br>`e2e` e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso | 2×A |  |
| REQ-008 | O sistema deve aceitar como resposta apenas índices numéricos, nunca texto livre. | `api` cliente_nao_consegue_forcar_correta_nem_gabarito<br>`api` aceita_apenas_indices_numericos (9) | 10×A |  |
| REQ-009 | Quando a resposta for correta, o sistema deve registrar a tentativa e mostrar a explica... | `api` acerto_registra_tentativa_e_mostra_explicacao<br>`e2e` e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso | 2×A |  |
| REQ-010 | Se a resposta for inválida (índice fora do intervalo ou formato errado), então o sistem... | `api` exercicio_id_malformado_ou_inexistente (10)<br>`api` resposta_invalida_rejeitada_sem_registrar (6) | 16×A |  |
| REQ-011 | Quando a resposta for incorreta, o sistema deve exibir uma explicação do erro específic... | `api` erro_mostra_explicacao_da_opcao_escolhida<br>`e2e` e2e_02_offline_mostra_erro_amigavel_tenta_de_novo_sem_perder_a_sessao | 2×A |  |
| REQ-012 | O agente explicador deve receber apenas o id do exercício e a opção escolhida, e não de... | `api` explicador_recebe_so_id_e_opcao_e_nao_tem_tool | 1×A | Parcial: assinatura e prompt enviado, não o código |
| REQ-013 | Se o agente explicador falhar ou estourar o tempo, então o sistema deve exibir a explic... | `api` falha_do_explicador_cai_na_explicacao_generica | 1×A |  |
| REQ-014 | Quando um aparelho abrir o app sem `device_id` guardado, o cliente deve gerar um UUID e... | `web` gera_uuid_v4_e_guarda_no_localstorage<br>`web` reusa_o_id_ja_guardado_em_chamadas_seguintes<br>`web` valor_corrompido_no_storage_e_substituido_por_uuid_valido<br>`web` localstorage_indisponivel_nao_quebra_o_app<br>`e2e` e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso | 5×A |  |
| REQ-015 | O sistema deve associar tentativas ao `device_id` sem exigir cadastro, e-mail ou senha. | `api` tentativas_ligadas_ao_device_sem_cadastro<br>`web` cliente_envia_x_device_id_uuid_sem_credenciais | 2×A |  |
| REQ-016 | O sistema deve mostrar ao usuário total de acertos, taxa de acerto por tipo e sequência... | `api` progresso_mostra_acertos_taxa_por_tipo_e_sequencia<br>`e2e` e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso | 2×A | Sequência de dias: definição pendente (GAP-016) |
| REQ-017 | Enquanto o aparelho estiver sem conexão, o app deve exibir uma tela de erro amigável e ... | `web` falha_de_rede_vira_erro_amigavel_sem_stack_nem_url<br>`web` permite_tentar_de_novo_e_o_device_id_permanece<br>`web` erro_code_message_da_api_chega_ao_chamador<br>`e2e` e2e_02_offline_mostra_erro_amigavel_tenta_de_novo_sem_perder_a_sessao | 4×A |  |
| REQ-018 | Se o `device_id` não for um UUID válido, então o sistema deve responder `DEVICE_INVALIDO`. | `api` device_header_hostil (3)<br>`api` device_id_invalido_responde_device_invalido (8)<br>`api` device_id_ausente_tambem_e_invalido | 12×A |  |
| REQ-019 | O sistema deve gerar exercícios por um agente cujo loop está em `apps/api/app/agent/loo... | `api` loop_explicito_com_tools_modelo_e_limite_de_passos | 1×A |  |
| REQ-020 | O sistema deve registrar um log estruturado por passo do loop (execução, passo, tool, m... | `api` log_estruturado_por_passo | 1×A |  |
| REQ-021 | O gerador deve receber apenas valores de enum (tipo, nível, tema) como entrada. | `api` gerador_recebe_apenas_valores_de_enum (4) | 4×A |  |
| REQ-022 | Se o loop atingir o limite de passos sem produzir um exercício válido, então o sistema ... | `api` limite_de_passos_sem_exercicio_valido_encerra_como_falhou | 1×A |  |
| REQ-023 | O sistema deve permitir trocar de provedor ou modelo por configuração, sem mudar o loop. | `api` troca_de_provedor_e_modelo_sem_mudar_o_loop | 1×A | Parcial: a parte de configuração só checa a existência de `carregar_provedor` |
| REQ-024 | Quando o estoque de um (tipo, nível, tema) estiver abaixo de um mínimo configurado, o s... | `api` geracao_em_lote_so_por_cli_nunca_por_requisicao<br>`api` lote_respeita_minimo_de_estoque | 2×A |  |
| REQ-025 | O sistema não deve salvar exercício cujo código de referência não tenha sido executado ... | `api` nao_salva_codigo_que_nao_executou_com_sucesso | 1×A |  |
| REQ-026 | O sistema deve comparar a saída real da execução com a saída afirmada pelo modelo e rej... | `api` saida_real_diferente_da_afirmada_rejeita<br>`api` achar_bug_com_bug_e_correcao_iguais_rejeita<br>`api` ordenar_linhas_sem_permutacao_errada_distinguivel_rejeita | 3×A |  |
| REQ-027 | O sistema deve executar código gerado em sandbox com timeout, limite de memória, sem re... | `api` codigo_legitimo_executa_e_devolve_stdout<br>`api` loop_infinito_estoura_timeout (4)<br>`api` saida_gigante_e_truncada<br>`api` import_de_modulos_perigosos_e_bloqueado (12)<br>`api` nao_le_variaveis_de_ambiente<br>`api` nao_le_nem_escreve_arquivos_do_app<br>`api` sem_rede<br>`api` subprocess_nao_executa_comando_no_host<br>`api` estouro_de_memoria_e_contido<br>`api` fork_bomb_e_contida | 24×A | Memória e fork bomb só em Linux (`skipped` no Windows) |
| REQ-028 | Quando a validação aprovar o exercício, o sistema deve salvá-lo com `status = validado`. | `api` validacao_aprovada_salva_com_status_validado | 1×A |  |
| REQ-029 | Quando a validação rejeitar o exercício, o sistema deve descartá-lo e registrar o motiv... | `api` validacao_rejeitada_descarta_e_registra_motivo | 1×A |  |
| REQ-030 | O sistema deve validar o schema da saída do modelo (tipo, campos, tamanhos) antes de ex... | `api` schema_invalido_rejeitado_antes_de_executar_codigo (16) | 16×A |  |
| REQ-031 | O back-end deve representar falhas de domínio por exceções tipadas. | `api` falhas_de_dominio_sao_excecoes_tipadas | 1×A |  |
| REQ-032 | O back-end deve ter um handler global que responda `{code, message}` com o status HTTP ... | `api` corpo_malformado_em_respostas_nunca_vira_5xx (11)<br>`api` handler_global_responde_code_message_com_status_adequado | 12×A |  |
| REQ-033 | O sistema não deve incluir stack trace, prompt ou detalhe interno em resposta ao cliente. | `api` metodo_e_rota_inexistentes_seguem_o_formato_de_erro<br>`api` nao_vaza_stack_trace_prompt_ou_detalhe_interno | 2×A |  |
| REQ-034 | Se ocorrer erro não previsto, então o sistema deve responder `ERRO_INTERNO`, registrar ... | `api` erro_imprevisto_vira_erro_interno_com_id_de_correlacao | 1×A |  |
| REQ-035 | Se o banco estiver indisponível, então `GET /health` deve responder falha e as demais r... | `api` banco_indisponivel | 1×A |  |
| REQ-036 | O sistema deve tratar todo texto vindo do usuário como dado, nunca como instrução de mo... | `api` texto_do_usuario_e_dado_nunca_instrucao | 1×A | Estrutural (ver spec-gaps seção 3) |
| REQ-037 | Qualquer agente que receba texto livre não deve ter tool de execução. | `api` agente_com_texto_livre_nao_tem_tool_de_execucao | 1×A | Parcial (GAP-011) |
| REQ-038 | O sistema deve ter testes de prompt injection mostrando que conteúdo hostil, em campos ... | `api` texto_hostil_na_resposta_do_usuario_nao_chega_a_nenhum_agente (7)<br>`api` enum_hostil_no_gerador_nao_chama_modelo_nem_tool (7)<br>`api` conteudo_hostil_vindo_do_modelo_nao_muda_tools_nem_saida_validada<br>`api` explicador_ignora_instrucao_embutida_no_enunciado_armazenado | 16×A |  |
| REQ-039 | O repositório não deve conter segredos: só `.env.example` é versionado; valores reais f... | `api` repositorio_sem_segredos | 1×pass | Heurística de padrões; o gitleaks do CI é a barreira real |
| REQ-040 | O sistema deve limitar a taxa de requisições por aparelho e por IP. | `api` limita_taxa_por_aparelho_e_por_ip | 1×A | Limites numéricos pendentes (GAP-040) |
| REQ-041 | O sistema deve restringir CORS à origem do front configurada. | `api` cors_restrito_a_origem_do_front | 1×A |  |
| REQ-042 | O repositório deve ter evals que rodem o mesmo conjunto de casos em 2 ou mais modelos e... | `api` evals_rodam_o_mesmo_conjunto_em_2_ou_mais_modelos<br>`evals` evals/tests/metricas.py (bateria, executor, métricas) (46) | 47×pass | Também coberto por `evals/tests/test_metricas.py` |
| REQ-043 | O CI deve rodar lint, testes e evals determinísticos a cada PR. | `api` ci_roda_lint_testes_e_evals_deterministicos | 1×pass | Conflito com a instrução de não rodar evals no CI (GAP-043) |
| REQ-044 | O sistema deve expor `GET /health` com o status da API e do banco. | `api` health_expoe_status_da_api_e_do_banco | 1×A | Conflita com `test_health.py` (DISP-001) |

## Requisitos sem teste

Nenhum: os 44 requisitos têm ao menos um teste.

Têm teste, mas só **parcial** ou condicionado a decisão: REQ-005, 012, 016, 023, 027, 036, 037, 039, 040, 043, 044.
Motivos em [`spec-gaps.md`](spec-gaps.md), seção 3, e nos itens GAP-0xx.
