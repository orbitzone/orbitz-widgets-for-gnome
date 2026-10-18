# Post-its Orbitz

Aplicativo GTK independente. Não importa código do GNOME Shell e não altera a extensão dos widgets.

- Clique no cartão e escreva. Trocar de aplicativo não fecha a nota.
- Arraste o título para mover; arraste o canto inferior direito para redimensionar.
- Botão direito no título ou no texto: nova nota, cores, manter acima, ocultar, arquivar e restaurar.
- Ctrl+N: nova nota. Ctrl+Z / Ctrl+Shift+Z: desfazer/refazer. Ctrl+H: ocultar.
- Abra **Post-its Orbitz** no menu de aplicativos para mostrar as notas ocultas.
- O aplicativo inicia no login. Para parar: botão direito → Encerrar post-its.

A nota anterior é copiada uma única vez. O arquivo antigo de notas e tarefas permanece intacto. As novas edições ficam em `~/.local/share/orbitz-postits/notes.sqlite3`, com transações SQLite e backups diários em `backups/` (até 14 cópias). O texto é gravado a cada mudança; um erro aparece no próprio cartão e impede ocultar uma nota ainda não salva.

O lançador usa GTK/XWayland para permitir posição persistente no Ubuntu com Wayland. O aplicativo reposiciona suas próprias janelas por GTK ao abrir ou ao detectar mudança de monitores. Não usa temporizadores para mover janelas de outros processos, capturas globais de teclado ou edição dentro do Shell.

Validação: gravações transacionais, conflito de revisão, importação sem alterar o original, arquivo/restauração e recuperação após SIGKILL; 400 alternâncias de foco entre uma nota e uma janela de edição em GNOME Shell isolado, com dois monitores virtuais. Os testes não equivalem a uma garantia de ausência de falhas em hardware real. Suspensão física, desconexão de monitores reais e escalas mistas ainda precisam de validação no uso diário.
