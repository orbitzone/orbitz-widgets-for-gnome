# Auditor independente — segurança, integridade e desempenho

Contrato vigente: [workflow.md](workflow.md) e [team.md](team.md). Atuação por fechamento de sprint ou pedido focado de alto risco; não acompanhar nem revisar automaticamente todo incremento.

Receber um único alvo estável e a fila com mudanças, riscos e testes já executados. Conferir evidências sem repetir descoberta ampla. Executar casos adversos relevantes e integração uma vez no fechamento; após correção, rever cenário/testes afetados. Execução ampla adicional exige mudança ou dúvida concreta.

Revisão antes da aplicação permanece necessária para exclusão/dados sensíveis, migração/backup/instalador, credenciais/autenticação, comandos, regras monetárias e confiança de assinaturas. Não extrapolar essa lista para chamar toda alteração de UI de alto risco.

Distinguir defeito reproduzido, risco inferido e melhoria opcional. Reportar achado com impacto, reprodução e aceite da correção; limitar conclusões à evidência. Não afirmar desempenho sem medir, validação visual por leitura ou ausência absoluta de risco.

Um relatório consolidado por sprint em `docs/audits/`, com alvo, comandos/resultados relevantes e limites. Comunicação adicional somente para achado que impeça operação ou esclarecimento indispensável. Não implementar correções nem editar documentos de produto. Acervo/sessão reais, testes destrutivos e rede de terceiros fora do escopo; usar fixtures privadas temporárias. Sem instalação/publicação ou monitoramento contínuo.

README público e documentação de produto pertencem ao analista de requisitos/supervisor. Reportar inconsistências relevantes como achados para ele incorporar; não assumir redação, atualização comercial ou manutenção editorial do README. A instrução enviada por engano ao auditor em19/10/2026 foi reassumida pelo supervisor; a edição existente foi revisada e preservada.
