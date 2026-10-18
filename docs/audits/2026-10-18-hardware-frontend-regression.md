# Diagnóstico frontend — CPU/RAM/SSD — 18/10/2026

Estado: **frontend estável; nenhuma correção de produção frontend necessária pela evidência disponível**. Sintomas relatados após atualização/login: CPU/SSD falham na consulta, RAM não abre. Instalação e coletor foram investigados pelo supervisor/backend.

## Evidência e resultado

- `extension/panels/storage.js` recebe todas as dependências externas usadas: Gio, GLib, Main, Pango, St e getData. A composição em `extension.js` as fornece; nenhuma referência ausente foi identificada.
- `tests/test_hardware_panel_flow.js` é a única alteração desta entrega. Carrega os métodos reais de hit test, press/release e refresh da extensão, além de renderHardware/renderStorage das fábricas reais. Respostas do subprocesso e atores GNOME são sintéticos; abertura/modalidade é simulada.
- Sequência **CPU → RAM → SSD → RAM → CPU**, conservando o objeto de diálogo entre aberturas: todos selecionam/renderizam o painel esperado; CPU/RAM enviam `--hardware cpu/ram --details`, SSD envia apenas `--details` e limpa `_hardwareMode`. O clique usa texto com barras UTF-8 e prefixo de alerta no SSD.
- Comandos executados: `node tests/test_hardware_panel_flow.js` e `node --check tests/test_hardware_panel_flow.js`: aprovados. Nenhuma suíte global ou nova tentativa gráfica foi executada.

## Causa apurada na colaboração

Supervisor observou no coletor instalado retorno de span de métricas, exit 0, para `--hardware cpu/ram`, onde o frontend exige `AZCLOCK_HARDWARE:`. Backend informou correção dos roteamentos no repositório, com `--hardware` antes de `--details` e encaminhamento ao helper. Segundo comparação backend com histórico, a omissão já estava no snapshot HEAD anterior à RF-01. Verificação dos processos/helper e aplicação instalada pertencem aos relatórios backend/supervisor; não foram repetidas pelo frontend.

## Limites e próximos responsáveis

O sintoma RAM não abrir **não foi reproduzido no frontend sintético**. Esse teste não comprova geometria Pango real, foco/modalidade GNOME ou entrada na instalação ativa. Não foi criada correção especulativa. Se persistir após atualização verificada do coletor, supervisor deve fornecer erro/cenário da instalação para reprodução direcionada; frontend continua responsável por corrigir achado próprio confirmado.

Backend também informou divergência separada de dispositivos externos (`devices=[]` versus mapa por linha); não foi confundida com CPU/RAM nem alterada nesta entrega.

Sem instalação, reload, alteração de backend, dados pessoais, commit ou push. A atualização exige novo instalador/hashes sob responsabilidade do supervisor antes de orientar novo teste do usuário. Validação visual/interativa permanece pendente. UX recebe diagnóstico e limites pelo canal autorizado.
