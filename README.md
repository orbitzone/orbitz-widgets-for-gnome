# Orbitz - Widgets for GNOME

Widgets de desktop para GNOME Shell, com scripts Python e uma versão personalizada da extensão **Desktop Clock (azclock)**.

## Widgets

- CPU, RAM e espaço em disco.
- Processos com maior consumo de CPU.
- Tráfego de rede.
- Conexões TCP e portas, com modal atualizada ao abrir ou pelo ícone de refresh.
- Temperaturas de CPU/GPU, conforme os sensores disponíveis.
- Volumes externos e espaço livre.
- Clima de Brasília, atualizado a cada cinco minutos.
- Teste de velocidade opcional pela CLI oficial da Ookla.

O layout é configurado nas preferências do Desktop Clock. Este repositório não inclui configurações pessoais, caches, histórico de conexões ou o executável proprietário da Ookla.

## Compatibilidade e dependências

Base: Desktop Clock versão 7, com metadata para GNOME Shell 42, 43 e 44. As personalizações foram usadas no GNOME 42; outras versões precisam de validação. GNOME 45 ou posterior não é suportado por esta base de imports legados.

Requer Python 3, `bash`, `setsid` e `kill` do util-linux, `ss` do iproute2, `getent`, `lsblk` e `glib-compile-schemas`. `sensors` (lm-sensors) e libpsl são opcionais. Scripts de temperaturas/estatísticas usam `/proc` e `/sys` no Linux.

## Instalação manual

Faça backup da extensão e das suas configurações se já utiliza azclock: esta versão usa o mesmo UUID e substitui a instalação existente.

```bash
mkdir -p "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com"
cp -a extension/. "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/"
glib-compile-schemas "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/schemas"
mkdir -p "$HOME/.local/share/orbitz-widgets"
cp widgets/*.py "$HOME/.local/share/orbitz-widgets/"
```

Saia e entre novamente na sessão, habilite a extensão e adicione elementos de comando nas preferências. Use caminhos absolutos, substituindo `SEU_USUARIO`:

```text
python3 /home/SEU_USUARIO/.local/share/orbitz-widgets/cpu-ram-widget.py
```

Repita com os outros scripts. Os intervalos das preferências são em **milissegundos**: 6000 significa 6 segundos. O clima usa cinco minutos na extensão, independentemente do valor exibido no editor atual. Os caches ficam em `$XDG_CACHE_HOME/orbitz-widgets` ou `~/.cache/orbitz-widgets`.

Para alterar a cidade do clima, edite `PARAMS` no script. O script CPU/RAM mede o espaço do filesystem da pasta pessoal.

### Teste de velocidade opcional

Instale/baixe o [Speedtest CLI oficial da Ookla](https://www.speedtest.net/apps/cli) e coloque o executável Linux compatível com sua arquitetura com nome `speedtest` na pasta da extensão, com permissão de execução. Esse binário não é distribuído neste repositório e tem termos próprios de uso pessoal/não comercial. Ao clicar em testar, a integração usa as opções de aceite da licença e privacidade; leia os termos da Ookla antes de habilitar esse recurso.

## Segurança e desempenho

Comandos personalizados executam com as permissões da conta: importe apenas configurações confiáveis. Execuções periódicas não se sobrepõem; comandos comuns têm timeout de 30 segundos e stdout/stderr limitados a 256 KiB. A coleta manual tem timeout de 15 segundos e o Speedtest, de 120 segundos.

O cancelamento encerra o grupo do comando; não é uma sandbox e não cobre processos que criem deliberadamente outra sessão. A modal não tem refresh periódico. A abertura usa detecção adaptativa do ponteiro para compatibilidade com a camada do desktop. Não há promessa de consumo zero ou redução percentual de CPU.

## Créditos e licença

Base criada por Andrew Zaech: [Desktop Clock / azclock](https://gitlab.com/AndrewZaech/azclock). Créditos e avisos originais foram preservados. Personalizações e widgets: orbitzone / Orbitz.

Distribuição deste código sob GPL-3.0, conforme o arquivo LICENSE incluído. Dependências e Speedtest CLI possuem licenças próprias.
