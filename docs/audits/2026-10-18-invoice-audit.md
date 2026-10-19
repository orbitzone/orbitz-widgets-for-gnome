# INV-01 — auditoria dirigida de faturas — 18/10/2026

Estado: **funcional local e revisão delimitada de integridade aprovadas; interação GTK instalada pendente**. Nenhum impeditivo reproduzido no escopo executado. Não representa emissão fiscal oficial, aprovação gráfica da agenda ou instalação efetuada.

## Alvo e fontes

Checkout sobre HEAD identificado no encerramento abaixo, com alterações locais dos módulos/testes listados no manifesto. Backend e frontend encaminhados estáveis pelo supervisor. Fontes lidas: relatórios invoice-backend, invoice-frontend, invoice-pdf-qa e implementações/testes de domínio, perfis, PDF, menu e sessão. Nenhuma alteração de código pelo auditor. Sem instalação, reload, GSettings pessoal, dados fiscais reais, envio de documento ou operação externa.

A skill PDF foi lida pelo auditor e marker create/2 executado antes da primeira suíte que produz PDFs temporários; não se repetiram renders sem necessidade. QA visual dos quatro PDFs PT/EN pertence ao supervisor (`docs/audits/2026-10-18-invoice-pdf-qa.md`), não foi apresentada como execução própria do auditor.

## Execuções independentes e resultados

```bash
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p test_invoice_backend.py -v
# Após frontend estável, integração dos dois arquivos:
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p 'test_invoice_*.py' -v
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -p test_planner_backend.py -v
git diff --check -- extension/planner/calendar-app.py
```

Backend inicial:11/11 aprovados,0,741s. Integrada: **17/17 aprovados**,0,769s. Regressões planner: **8/8 aprovadas**,1,322s. Não somar execução inicial repetida como casos novos: são25 casos distintos na integração/regressão. Sintaxe AST dos8 arquivos revisados aprovada; diff-check aprovado. Sem suíte global durante mutação ou ampliação desnecessária após estabilidade. DeprecationWarning load_module é da dependência ReportLab, não falha de teste; dependências não editadas.

Teste adicional independente confirmou420min×125,50=878,50 sem alterar o sheet original; NaN/sNaN/Infinity/negativo/exponencial/floatnan recusados; load/save de perfil symlink falham sem alterar arquivo sentinela. Todos os dados usados eram sintéticos/temporários.

## Revisão do domínio e finanças

Minutos inteiros derivados de registros concluídos; Decimal com precisão50 e taxa textual positiva/finita até2casas. Total = minutos×taxa/60 e somente resultado final quantizado HALF_UP em centavos. Três minutos a0,10 resultam0,01, evitando soma por atividade arredondada. Vírgula/ponto aceitos como separador decimal; milhares, múltiplos separadores, expoente e float não são aceitos. Limites/formatação não mudam taxas ou cálculo de timesheets existentes.

Todo histórico é default, período opcional inclusivo exige duas datas válidas/ordenadas. Ativas/arquivadas aceitas; lixeira e timerativo excluídos, aviso de timer aparece na prévia. Fatura não altera registros/timer/arquivamento, tarefas/calendários. validate_snapshot reconstrói e compara minutos, horas, total, entradas e período antes de gravar; adulteração de total foi recusada.

CPF aceita formato numérico; CNPJ permite12posições ASCII alfanuméricas e2dígitos finais, cru/pontuado, normalizando maiúsculas. Casos negativos de tamanho/pontuação/final alfabético recusados. Contrato confirmado pelo supervisor com fonte oficial; auditor verifica cumprimento desse contrato, não cadastro/dígitos fiscais nem consulta identificadores online. Moeda3letras independente do idioma PT/EN, BRL padrão; sem câmbio/impostos/integração fiscal.

## Perfis privados e dados

Arquivo próprio separado de notes/timesheets, respeita XDG_DATA_HOME; emitente/idioma globais e cliente/taxa/moeda por sheet. Troca não reutiliza cliente de outro sheet; testes de duas empresas mantêm isolamento. Perfil é escrito apenas após PDF bem-sucedido; load/cancel/erro de validação/PDF não persistem. Falha do perfil após PDF retorna aviso distinto de exportação falhada.

Leitura limitada2MiB, NOFOLLOW/NONBLOCK+fstat arquivo regular, validação versionada, erro explícito de corrupção sem substituir por defaults. Save usa lock0600/flock, lê dentro da seção exclusiva, atomic_json privado0600 com fsync/replace/limpeza. Concorrência6processos manteve todas as sheets; falha de replace preservou original/limpou temporário. Nenhum caminho de perfil pessoal foi usado, nenhum conteúdo privado adicionado a logs/repo. Lock/atomicidade não são transação global com editores externos não cooperantes; não se afirma proteção absoluta contra alteração simultânea de diretórios por outro processo.

## PDF e proteção de saída

ReportLab tardio, DejaVu Sans/bold incorporadas; teste de pdffonts confirmou fonte Unicode e pdftotext preservou acentos/tags literais/últimas descrições. Paragraph recebe escape XML, controles inválidos recusados; descrições longas são fragmentadas com Paragraph.split e LongTable repete cabeçalhos. Endereço longo pode quebrar página. PT/EN traduz rótulos, preserva dados digitados, moeda independente. Aviso no rodapé distingue Fatura de serviços/Service invoice de documento fiscal eletrônico.

Destino.pdf local; temporário no mesmo diretório,0600,flush/fsync/publicação e fsync diretório. Sem overwrite, hardlink atômico impede clobber mesmo se destino aparecer durante render. Overwrite exige bool explícito e arquivo regular sem symlink, revalida dev/inode/size/mtime; falha de render preserva original, temporários limpos. Não há promessa de rollback após publicação seguida de falha fsync nem transação contra mudança após última checagem. Testes cobrem conflitos/renderfalha/symlink; sem operação em documentos reais.

## Frontend/menu e limites dos testes

Menu header horizontal à direita da data/título, três ações, statusfooter mantido e ações antigas movidas sem duplicar: arquivadas chama mesmo callback e atualiza contagem/nome acessível; backups chama planner_tools.open_backups; invoice abre novo formulário. Teste de menu usa atores sintéticos e verifica ordem/callbacks/contagem1→0, não posição em pixels.

InvoiceSession lê dados frescos ao revisar, guarda snapshot/cópia do perfil; exportação congela o que foi revisado. Editar invalida snapshot/desabilita salvar; falhaAPPLY limpa prévia antiga; trocar sheet carrega perfil/rascunho correto e bloqueia revisão se seleção não carregou. A UI mostra a natureza de fatura, timer excluído e escopo global/sheet dos dados lembrados. Textos CPF/CNPJ livres não restringem letras.

Chooser nativo configura overwriteconfirmation e associa overwrite=True ao mesmo filename que emitiu confirm-overwrite antes do aceite. Cancelar chooser volta ao formulário sem export/save; cancelar diálogo não persiste. PDF usa somente snapshot válido; import ReportLab ausente no módulo ou dentro de write produz mensagem amigável sem salvar perfil. Falha pós-PDF de perfil mantém resultado PDF e aviso separado.

**Limite relevante:** testes de sessão comprovam ordem/export/persistência/invalidação e roundtripPDF real; não executam FileChooserDialog real, foco/Tab/atalhos/AT, confirmação nativa de overwrite, workarea ou transições completas dos sinais GTK. Essas partes foram lidas estaticamente e continuam pendentes de teste manual; não apresentadas como integração gráfica aprovada. Parecer UX favorável estático não substitui GTK real.

## Achados e conclusão

Nenhum defeito impeditivo reproduzido nos contratos auditados. Sem alegar ausência absoluta de defeitos ou aprovação fiscal. Melhorias fora do escopo não foram implementadas. RAM/EXT, branding e migração não são resolvidos por esta entrega.

- Funcional local:17 casosinvoice+8regressõesplanner aprovados,8sintaxes; domain/perfil/export e callbacks testados.
- PDF visual: amostras PT/EN quatro páginas aprovadas pelo supervisor, conforme relatório próprio; extração/fontes/extremos/falhas testados pelo auditor sem repetir renders.
- UI visual/interação: pendente em GTK real; sem sessão ativa/instalação pelo auditor.
- Segurança/integridade: revisão delimitada sem impeditivo reproduzido; dados sintéticos, atomicidade/locks/conflitos exercitados; não certificação integral ou emissão oficial.
- Desempenho: não medido.

Próximo responsável: supervisor integra aceite/limites e coordena aplicação somente autorizada; usuário/frontend verificam menu/preview/cancel/overwrite/foco na agenda real. Não é necessário logoutGNOME para um aplicativoPython atualizado, mas é necessário encerrar/reabrir a agenda para carregar módulos novos. Não aplicar sem verificar que todos os módulos/dependências acompanham a entrega.

## Identidade do alvo

HEAD: `d5d8aae14711ebf33da9fd13a1673b1558a966d5`.

| Arquivo | SHA-256 |
|---|---|
| `extension/planner/invoice.py` | `0f5a89c622161bfda6b45ebe022c5cd75b271807a30226983dec93de40615a17` |
| `extension/planner/invoice_profiles.py` | `dcb4b007dd33f2338c5f2c6558e1b966a4863f5227d4ec545e5326c8fe60ac3c` |
| `extension/planner/invoice_pdf.py` | `633d1d698b0c9d22bcb1559a0b70320f366e8a77cf4cbeb7b5c9ff183537bdb7` |
| `extension/planner/invoice_ui.py` | `2d5555a53cd6c606fed7e52f330b08d7004251e25db97eb37572fc6ae7c282e8` |
| `extension/planner/planner_menu.py` | `c7323fd688365db88ec9ddcd7b82d576ff6db12e1d93adc0098f38f52cb75339` |
| `extension/planner/calendar-app.py` | `92460db733e604f44441785b99db42d37241ba418b99c786e3c78e4fdd42dda1` |
| `tests/test_invoice_backend.py` | `43c037042cc7357cb8d3e2577c36bec1c0e9b230430b641377513560c86f3f24` |
| `tests/test_invoice_frontend.py` | `25d5fea29dfa2726845f33a0226762f2069ea557d78f9a0a2479e3538e486716` |

Hashes backend conferidos ao fim da etapa backend e permanecem iguais na integração. Fontesfrontend identificadas no encerramento acima; sem mutações planejadas informadas. Nenhum PDF temporário é entregue como documento pessoal/fiscal.
