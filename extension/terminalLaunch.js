// Forward the user's launch context through collectors to the terminal window.
var create = ({Gio, global, Language}) => (argv, owner = null) => {
    const hasModal = !!owner?._networkModalGrab;
    if (hasModal && (typeof owner._closeNetworkDialog !== 'function' || typeof owner._openNetworkDialog !== 'function'))
        throw new Error('Não foi possível preparar o painel modal para abrir o terminal.');
    const context = global.create_app_launch_context(0, -1);
    const info = Gio.AppInfo.create_from_commandline('/usr/bin/tilix', 'Terminal Orbitz',
        Gio.AppInfoCreateFlags.SUPPORTS_STARTUP_NOTIFICATION);
    const startupId = context.get_startup_notify_id(info, []);
    if (!startupId) throw new Error('Não foi possível criar o contexto de ativação do terminal.');
    const launcher = new Gio.SubprocessLauncher({flags: Gio.SubprocessFlags.NONE});
    // The Shell activation token is interoperable between Wayland and X11.
    launcher.setenv('DESKTOP_STARTUP_ID', startupId, true);
    launcher.setenv('XDG_ACTIVATION_TOKEN', startupId, true);
    if (Language) {
        launcher.setenv('ORBITZ_LOCALE', Language.getLocale(), true);
        const directory = Language.directory();
        if (directory) launcher.setenv('ORBITZ_I18N_DIR', directory, true);
    }
    // Dismiss the modal before the child can ask Tilix to open; otherwise the
    // Shell may keep the keyboard grab while Tilix is already being activated.
    if (hasModal) owner._closeNetworkDialog();
    let proc;
    try {
        proc = launcher.spawnv(argv);
    } catch (error) {
        context.launch_failed(startupId);
        if (hasModal) owner._openNetworkDialog();
        throw error;
    }
    return proc;
};
