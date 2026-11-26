# Estado inicial dos testes

Primeira execução completa da suíte, **antes de existir implementação de funcionalidade**. A falha era esperada.

- **(A)** falha porque o requisito ainda não está implementado. É a falha certa.
- **(B)** falha por erro do próprio teste (import, fixture, sintaxe, config). Todas as ocorrências foram corrigidas antes do fim da sessão.

Falhas de categoria A apontam, no motivo, o que falta existir (módulo, função, rota ou comportamento). Testes parametrizados aparecem em uma linha só, com o número de casos.

## Falhas de categoria B encontradas e corrigidas

A execução final tem **0 falhas B**. Estas foram achadas pelo caminho e corrigidas:

- `contrato.py`: `exercicio_exemplo(tipo="inventado")` dava `KeyError` na coleta de `test_req_validacao.py`.
- `test_req_019` falhava em `is_file()` e `test_req_034` em `JSONDecodeError`: a causa real (módulo ou handler ausente) ficava escondida; agora dizem `NAO-IMPLEMENTADO`.
- Vitest: `import()` estático de módulo ausente derrubava a coleta (trocado por `import.meta.glob`); o `localStorage` experimental do Node 26 escondia o do jsdom (`tests/setup.ts`).
- Playwright: `TypeError` do matcher quando não havia `device_id`; agora a mensagem é de asserção.
- Achados ao rodar os testes contra uma implementação de referência descartável (150 de 152 passam; as 2 falhas são o REQ-043 e o `test_health.py`, conflitos de spec): caso `recursao-e-loop` do sandbox morria com `RecursionError` e nunca dava timeout; falso positivo do REQ-039 no canário de URL de banco do próprio teste; **falta de isolamento de banco e de rate limit entre testes** (fixture `_isolamento` no `conftest.py`).
- Lint: o ruff 0.17 do ambiente tem regras padrão que o hook de pre-commit aplica; testes ajustados.

Limite desta verificação: a referência foi escrita por um agente com acesso aos testes, então prova que eles são **satisfazíveis**, não que a interpretação da spec é a certa (ver `spec-gaps.md`). Os testes Linux-only de memória e fork bomb nunca rodaram: no Windows ficam `skipped` só depois de a implementação existir, e hoje falham antes, por `app.sandbox` ausente. Dos dois e2e, só o primeiro passo de cada foi exercitado (o resto depende do front).

## Resumo

| Resultado | Casos |
|---|---|
| (A) requisito não implementado | 160 |
| (B) erro do próprio teste | 0 |
| passa hoje | 50 |
| pulado (só Linux) | 0 |

## API (pytest)

| Arquivo | Teste | Casos | Cat. | Motivo |
|---|---|---|---|---|
| `test_api_payloads_malformados` | `test_req_032_corpo_malformado_em_respostas_nunca_vira_5xx` | 11 | A | rota POST /respostas não existe (HTTP 404) |
| `test_api_payloads_malformados` | `test_req_010_exercicio_id_malformado_ou_inexistente` | 10 | A | rota POST /respostas não existe (HTTP 404) |
| `test_api_payloads_malformados` | `test_req_008_cliente_nao_consegue_forcar_correta_nem_gabarito` | 1 | A | módulo 'app.db' não existe |
| `test_api_payloads_malformados` | `test_req_002_filtros_malformados_em_exercicios` | 6 | A | rota GET /exercicios não existe (HTTP 404) |
| `test_api_payloads_malformados` | `test_req_018_device_header_hostil` | 3 | A | rota GET /progresso não existe (HTTP 404) |
| `test_api_payloads_malformados` | `test_req_033_metodo_e_rota_inexistentes_seguem_o_formato_de_erro` | 1 | A | NAO-IMPLEMENTADO [REQ] sem handler global: o framework responde {'detail'} em vez de {code, message} |
| `test_health` | `test_health_responde_ok` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_prompt_injection` | `test_req_038_texto_hostil_na_resposta_do_usuario_nao_chega_a_nenhum_agente` | 7 | A | módulo 'app.db' não existe |
| `test_prompt_injection` | `test_req_038_enum_hostil_no_gerador_nao_chama_modelo_nem_tool` | 7 | A | módulo 'app.agent.loop' não existe |
| `test_prompt_injection` | `test_req_038_conteudo_hostil_vindo_do_modelo_nao_muda_tools_nem_saida_validada` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_prompt_injection` | `test_req_038_explicador_ignora_instrucao_embutida_no_enunciado_armazenado` | 1 | A | módulo 'app.agent.explicador' não existe |
| `test_req_agente` | `test_req_019_loop_explicito_com_tools_modelo_e_limite_de_passos` | 1 | A | apps/api/app/agent/loop.py não existe |
| `test_req_agente` | `test_req_020_log_estruturado_por_passo` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_req_agente` | `test_req_021_gerador_recebe_apenas_valores_de_enum` | 4 | A | módulo 'app.errors' não existe |
| `test_req_agente` | `test_req_022_limite_de_passos_sem_exercicio_valido_encerra_como_falhou` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_req_agente` | `test_req_023_troca_de_provedor_e_modelo_sem_mudar_o_loop` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_req_agente` | `test_req_024_geracao_em_lote_so_por_cli_nunca_por_requisicao` | 1 | A | módulo 'app.cli' não existe |
| `test_req_agente` | `test_req_024_lote_respeita_minimo_de_estoque` | 1 | A | módulo 'app.cli' não existe |
| `test_req_correcao` | `test_req_007_compara_ao_gabarito_e_informa` | 1 | A | módulo 'app.db' não existe |
| `test_req_correcao` | `test_req_008_aceita_apenas_indices_numericos` | 9 | A | módulo 'app.db' não existe |
| `test_req_correcao` | `test_req_009_acerto_registra_tentativa_e_mostra_explicacao` | 1 | A | módulo 'app.db' não existe |
| `test_req_correcao` | `test_req_010_resposta_invalida_rejeitada_sem_registrar` | 6 | A | módulo 'app.db' não existe |
| `test_req_correcao` | `test_req_011_erro_mostra_explicacao_da_opcao_escolhida` | 1 | A | módulo 'app.db' não existe |
| `test_req_correcao` | `test_req_012_explicador_recebe_so_id_e_opcao_e_nao_tem_tool` | 1 | A | módulo 'app.agent.explicador' não existe |
| `test_req_correcao` | `test_req_013_falha_do_explicador_cai_na_explicacao_generica` | 1 | A | módulo 'app.db' não existe |
| `test_req_erros` | `test_req_031_falhas_de_dominio_sao_excecoes_tipadas` | 1 | A | módulo 'app.errors' não existe |
| `test_req_erros` | `test_req_032_handler_global_responde_code_message_com_status_adequado` | 1 | A | rota GET /exercicios não existe (HTTP 404) |
| `test_req_erros` | `test_req_033_nao_vaza_stack_trace_prompt_ou_detalhe_interno` | 1 | A | rota POST /respostas não existe (HTTP 404) |
| `test_req_erros` | `test_req_034_erro_imprevisto_vira_erro_interno_com_id_de_correlacao` | 1 | A | sem handler global: 500 sem corpo {code, message} |
| `test_req_erros` | `test_req_035_banco_indisponivel` | 1 | A | módulo 'app.db' não existe |
| `test_req_erros` | `test_req_044_health_expoe_status_da_api_e_do_banco` | 1 | A | NAO-IMPLEMENTADO [REQ] GET /health devolve só {'status': 'ok'}, sem o status do banco |
| `test_req_exercicios` | `test_req_001_quatro_tipos_de_exercicio_sao_oferecidos` | 1 | A | módulo 'app.db' não existe |
| `test_req_exercicios` | `test_req_002_exercicio_tem_nivel_e_tema_dos_enums` | 1 | A | módulo 'app.db' não existe |
| `test_req_exercicios` | `test_req_003_devolve_validado_priorizando_nao_resolvidos` | 1 | A | módulo 'app.db' não existe |
| `test_req_exercicios` | `test_req_004_resposta_nao_inclui_gabarito` | 1 | A | módulo 'app.db' não existe |
| `test_req_exercicios` | `test_req_006_sem_exercicio_devolve_erro_com_sugestao` | 1 | A | módulo 'app.db' não existe |
| `test_req_progresso` | `test_req_015_tentativas_ligadas_ao_device_sem_cadastro` | 1 | A | módulo 'app.db' não existe |
| `test_req_progresso` | `test_req_016_progresso_mostra_acertos_taxa_por_tipo_e_sequencia` | 1 | A | módulo 'app.db' não existe |
| `test_req_progresso` | `test_req_018_device_id_invalido_responde_device_invalido` | 8 | A | rota GET /progresso não existe (HTTP 404) |
| `test_req_progresso` | `test_req_018_device_id_ausente_tambem_e_invalido` | 1 | A | rota GET /progresso não existe (HTTP 404) |
| `test_req_qualidade` | `test_req_042_evals_rodam_o_mesmo_conjunto_em_2_ou_mais_modelos` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_req_qualidade` | `test_req_043_ci_roda_lint_testes_e_evals_deterministicos` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_req_seguranca` | `test_req_036_texto_do_usuario_e_dado_nunca_instrucao` | 1 | A | módulo 'app.db' não existe |
| `test_req_seguranca` | `test_req_037_agente_com_texto_livre_nao_tem_tool_de_execucao` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_req_seguranca` | `test_req_039_repositorio_sem_segredos` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_req_seguranca` | `test_req_040_limita_taxa_por_aparelho_e_por_ip` | 1 | A | rota GET /exercicios não existe (HTTP 404) |
| `test_req_seguranca` | `test_req_041_cors_restrito_a_origem_do_front` | 1 | A | NAO-IMPLEMENTADO [REQ] sem CORSMiddleware: nenhum header access-control-allow-origin |
| `test_req_validacao` | `test_req_025_nao_salva_codigo_que_nao_executou_com_sucesso` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_req_validacao` | `test_req_026_saida_real_diferente_da_afirmada_rejeita` | 1 | A | módulo 'app.validador' não existe |
| `test_req_validacao` | `test_req_026_achar_bug_com_bug_e_correcao_iguais_rejeita` | 1 | A | módulo 'app.validador' não existe |
| `test_req_validacao` | `test_req_026_ordenar_linhas_sem_permutacao_errada_distinguivel_rejeita` | 1 | A | módulo 'app.validador' não existe |
| `test_req_validacao` | `test_req_028_validacao_aprovada_salva_com_status_validado` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_req_validacao` | `test_req_029_validacao_rejeitada_descarta_e_registra_motivo` | 1 | A | módulo 'app.agent.loop' não existe |
| `test_req_validacao` | `test_req_030_schema_invalido_rejeitado_antes_de_executar_codigo` | 16 | A | módulo 'app.validador' não existe |
| `test_sandbox_adversarial` | `test_req_027_codigo_legitimo_executa_e_devolve_stdout` | 1 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_loop_infinito_estoura_timeout` | 4 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_saida_gigante_e_truncada` | 1 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_import_de_modulos_perigosos_e_bloqueado` | 12 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_nao_le_variaveis_de_ambiente` | 1 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_nao_le_nem_escreve_arquivos_do_app` | 1 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_sem_rede` | 1 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_subprocess_nao_executa_comando_no_host` | 1 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_estouro_de_memoria_e_contido` | 1 | A | módulo 'app.sandbox' não existe |
| `test_sandbox_adversarial` | `test_req_027_fork_bomb_e_contida` | 1 | A | módulo 'app.sandbox' não existe |

## Front (Vitest)

| Arquivo | Teste | Casos | Cat. | Motivo |
|---|---|---|---|---|
| `ts` | `test_req_014_gera_uuid_v4_e_guarda_no_localstorage` | 1 | A | módulo 'lib/device-id' não existe |
| `ts` | `test_req_014_reusa_o_id_ja_guardado_em_chamadas_seguintes` | 1 | A | módulo 'lib/device-id' não existe |
| `ts` | `test_req_014_valor_corrompido_no_storage_e_substituido_por_uuid_valido` | 1 | A | módulo 'lib/device-id' não existe |
| `ts` | `test_req_014_localstorage_indisponivel_nao_quebra_o_app` | 1 | A | módulo 'lib/device-id' não existe |
| `ts` | `test_req_015_cliente_envia_x_device_id_uuid_sem_credenciais` | 1 | A | módulo 'lib/api' não existe |
| `ts` | `test_req_017_falha_de_rede_vira_erro_amigavel_sem_stack_nem_url` | 1 | A | módulo 'lib/api' não existe |
| `ts` | `test_req_017_permite_tentar_de_novo_e_o_device_id_permanece` | 1 | A | módulo 'lib/api' não existe |
| `ts` | `test_req_017_erro_code_message_da_api_chega_ao_chamador` | 1 | A | módulo 'lib/api' não existe |

## E2E (Playwright)

| Arquivo | Teste | Casos | Cat. | Motivo |
|---|---|---|---|---|
| `fluxo-principal.spec.ts` | `test_e2e_01_resolver_so_com_toques_acertar_ver_explicacao_e_progresso` | 1 | A | NAO-IMPLEMENTADO [REQ] front sem tela de exercício: nenhum device_id é guardado no localStorage (REQ-014) |
| `fluxo-principal.spec.ts` | `test_e2e_02_offline_mostra_erro_amigavel_tenta_de_novo_sem_perder_a_sessao` | 1 | A | NAO-IMPLEMENTADO [REQ] front sem tela de exercício: locator `iniciar` nunca aparece (timeout) |

## Evals (pytest)

| Arquivo | Teste | Casos | Cat. | Motivo |
|---|---|---|---|---|
| `test_metricas` | `test_executor_roda_codigo_legitimo` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_executor_barra_codigo_perigoso_antes_de_executar` | 12 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_executor_timeout_em_loop_infinito` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_self_bleu_textos_iguais_sao_quase_1_e_variados_sao_menores` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_self_bleu_precisa_de_pelo_menos_dois_textos` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_b_exercicio_valido_passa` | 4 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_b_rejeita_campo_faltando_extra_e_enum_invalido` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_a_saida_certa_passa` | 4 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_a_detecta_saida_afirmada_errada` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_a_detecta_codigo_que_nao_executa` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_a_nao_executa_codigo_perigoso_do_modelo` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_a_aceita_diferenca_so_de_espaco_no_fim` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_c_so_se_aplica_a_achar_bug` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_c_defeito_falha_e_correcao_funciona` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_c_defeito_igual_a_correcao_reprova` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_c_defeito_que_nao_falha_reprova` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_c_correcao_que_nao_funciona_reprova` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_d_so_se_aplica_a_ordenar_linhas` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_d_ordem_unica_passa` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_d_ordem_ambigua_reprova` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_d_nenhuma_ordem_valida_reprova` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_d_pecas_demais_reprova_sem_explodir` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_extrair_json_aceita_cerca_markdown_e_trata_lixo_como_invalido` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_resposta_invalida_do_modelo_conta_como_falha_de_schema` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_provedor_que_levanta_excecao_vira_acao_falhou` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_modelo_que_nunca_entrega_atinge_o_limite_de_passos` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_o_prompt_enviado_ao_modelo_so_tem_enums_e_id_do_caso` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_bateria_deterministica_mesmos_casos_em_todos_os_modelos` | 1 | passa | nada a implementar (ou comportamento já existente) |
| `test_metricas` | `test_mock_perfeito_passa_em_todas_as_metricas` | 1 | passa | nada a implementar (ou comportamento já existente) |
