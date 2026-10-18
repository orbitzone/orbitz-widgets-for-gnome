# Correção — roteamento CLI CPU/RAM/armazenamento

Data: 18/10/2026. Estado: repositório estável com teste específico aprovado; instalação e validação gráfica sob responsabilidade do supervisor/frontend.

## Causa e correção

O supervisor reproduziu `cpu-ram-widget.py --hardware cpu/ram` instalado devolvendo métricas `<span>` com exit 0. A comparação local confirmou que tanto o HEAD `2a24e0d` quanto o arquivo refatorado não continham os desvios CLI. O histórico `2026-10-08/quan/outputs/cpu-ram-widget.py` contém roteamento para `--hardware`, `--eject` e `--details`. Trata-se de divergência do snapshot do repositório em relação à instalação histórica; comparação AST com HEAD na RF-01 preservava o snapshot, sem provar equivalência com arquivos instalados.

Alterado somente `widgets/cpu-ram-widget.py` e ampliado `tests/test_collector_entrypoints.py`:

- `--hardware` delega ao auxiliar irmão `hardware-details.py` com `run_name='__main__'`, preservando argumentos e precedência sobre `--details`.
- `--eject` delega a `external_storage.eject_device` com `--device`/`--identity` e retorna `AZCLOCK_EJECT:` JSON. Testado com mock; nenhuma ejeção executada.
- `--details` delega ao auxiliar irmão `armazenamento-widget.py`, preservando flags de externo/dispositivo/identidade.
- Cada desvio retorna antes da amostragem. Sem flags de detalhe, texto/métricas/cache, importação inerte, main guard e execução pelo worker continuam iguais.

## Evidência

`python3 -m unittest discover -s tests -p test_collector_entrypoints.py -v`: **7/7 aprovados**. Dois casos novos: subprocessos reais do coletor copiado para diretório temporário, com auxiliares sintéticos verificando prefixo, `__main__` e passagem dos argumentos para CPU, RAM, armazenamento interno e externo; roteamento de ejeção com identidade e sem amostragem. Permaneceram aprovados os cinco testes anteriores, inclusive importação dos coletores sem efeitos e CPU executada por `exec` no contrato do worker. Sem suíte global nesta correção.

## Divergências adicionais observadas

Não importado o histórico inteiro: ele também usa barra de oito posições, disposição visual distinta, cálculo/cache de espaço disponível e várias linhas de dispositivos externos. O repo usa barra de dez posições e `external_usage` agregado. Essa diferença já existe no HEAD e não é parte do roteamento mínimo corrigido.

Impacto concreto da diferença de dispositivos: `metrics-worker.py` lê `namespace.get('EXTERNAL_DEVICES', [])`; o CPU do repo não define essa variável. `extension/extension.js` aceita `data.devices`, guarda `_externalDevices` e usa a lista no mapa de cliques por dispositivo. Assim o envelope do repo continua com `devices=[]`, sem identidade por linha externa. Restaurar várias linhas/identidades exige alinhar o mapeamento e a apresentação com frontend; informado aos responsáveis, sem mudança visual ou de métricas nesta correção.

## Limites e próximo responsável

Nenhuma instalação, arquivo histórico, ferramenta de atualização, configuração pessoal, frontend ou documentação de produto foi editado. Sem teste gráfico, cofre, rede real ou operação em dispositivos. Supervisor instala somente por seu fluxo autorizado e atualiza documentação/pendências; frontend valida CPU/RAM/SSD e o auditor confirma o estado integrado. Scripts auxiliares e runtime devem acompanhar o coletor na instalação.
