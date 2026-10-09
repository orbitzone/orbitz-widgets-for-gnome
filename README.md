# Orbitz — Widgets for GNOME

**Linux desktop widgets for system monitoring, network diagnostics, hardware temperatures, storage and weather — powered by GNOME Shell and Python.**

Orbitz combines seven standalone Python scripts with a customized version of [Desktop Clock (azclock)](https://gitlab.com/AndrewZaech/azclock). Display system information directly on your GNOME desktop and open a network panel to inspect TCP connections, listening ports or run an optional internet speed test.

[Download ZIP](https://github.com/orbitzone/orbitz-widgets-for-gnome/archive/refs/heads/main.zip) · [Report an issue](https://github.com/orbitzone/orbitz-widgets-for-gnome/issues) · [Source code](https://github.com/orbitzone/orbitz-widgets-for-gnome)

## Widgets

| Widget / script | What it does |
|---|---|
| **CPU, RAM and storage** — `cpu-ram-widget.py` | Shows CPU utilization, RAM usage and storage usage for the filesystem containing your home directory, with text progress bars. |
| **Top processes** — `processos-widget.py` | Lists up to seven processes ranked by CPU consumption over a one-second sample. Process usage may exceed 100% on multicore systems. |
| **Network traffic** — `rede-widget.py` | Shows current receive/transmit rates for the interface selected from the IPv4 default route. This measures traffic, not your connection's maximum speed. |
| **TCP connections and ports** — `seguranca-widget.py` | Counts non-loopback TCP connections and listening ports. Click the widget to open a panel with local ports and remote destinations; click a hostname to copy its full name. Counts do not indicate whether a connection is malicious. |
| **Hardware temperatures** — `temperaturas-widget.py` | Reads available CPU/GPU sensors from Linux sysfs, with an optional `sensors` fallback. Intel coretemp and AMDGPU are handled directly; unavailable readings display `N/D`. |
| **External volumes** — `volumes-widget.py` | Shows usage and free space for detected removable/external volumes and desktop mount locations. System mounts are filtered out. |
| **Weather** — `clima-widget.py` | Shows current conditions, temperature, feels-like temperature, humidity, daily low/high and precipitation probability through Open-Meteo. Defaults to Brasília, Brazil. |

The network panel also includes an optional **Ookla Speedtest CLI** integration for download/upload speed in Mbps, latency in ms and the last test time. Results appear after a successful test. Speed tests run only when requested.

**Language:** this README is in English. Widget labels and panel messages currently remain in Portuguese. Script filenames are preserved for compatibility.

## Stack and compatibility

| Component | Technology / version |
|---|---|
| Desktop integration | GNOME Shell extension written in JavaScript using GJS |
| UI and async operations | St, Clutter, Pango, Gio and GLib; GTK/libadwaita for preferences |
| Extension base | Desktop Clock / azclock **version 7** |
| GNOME versions | Metadata declares **42, 43 and 44**; development and use were on **GNOME 42**. Versions 43/44 require validation. |
| Widget scripts | **Python 3.10.12** was used for development checks; Python **3.10** is the reference runtime. Newer releases need validation. |
| Python dependencies | Standard library only — no pip packages required |
| System data | Linux `/proc`, `/sys`, filesystem statistics and command-line utilities |
| Weather provider | Open-Meteo HTTPS API; no API key configured in the script |
| Optional speed testing | Official Ookla Speedtest CLI, installed separately |

**GNOME 45+ is not supported by this extension's legacy import architecture.** This is a Linux/GNOME project; other desktop environments are not supported by the extension. Standalone scripts can still be run in a Linux terminal.

### Required system utilities

Install Python 3, Bash, `setsid`, `/usr/bin/kill`, `ss`, `getent`, `lsblk` and `glib-compile-schemas` using your distribution's package manager. These are commonly provided by util-linux, iproute2, libc utilities and GLib packages. The extension currently expects `setsid` and `kill` at `/usr/bin`.

Optional: `sensors` from lm-sensors, `libpsl.so.5` for shortened hostname display, and the official Ookla CLI. Missing temperature sensors or optional tools can limit the corresponding feature.

## Download and install

Clone the repository, or download and extract the ZIP linked above:

```bash
git clone https://github.com/orbitzone/orbitz-widgets-for-gnome.git
cd orbitz-widgets-for-gnome
```

**Existing Desktop Clock users:** back up your extension directory and export your settings first. Orbitz keeps the UUID `azclock@azclock.gitlab.com` and replaces that installation; it is not a separate extension that can run alongside the original.

From the repository root:

```bash
mkdir -p "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com"
cp -a extension/. "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/"
glib-compile-schemas "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/schemas"

mkdir -p "$HOME/.local/share/orbitz-widgets"
cp widgets/*.py "$HOME/.local/share/orbitz-widgets/"
```

Log out and back in, then enable **Desktop Clock** through the GNOME Extensions app. Open its preferences to add widgets and configure command elements, fonts, colors, positions and alignment. Personal layout settings are not bundled: copying the files does not automatically create the seven widgets.

### Configure each widget

Add a command element for each script you want. Use an absolute path, replacing `YOUR_USER` with your Linux username:

```text
python3 /home/YOUR_USER/.local/share/orbitz-widgets/cpu-ram-widget.py
```

Change the filename for the other entries in the widget table. Use the actual path to your home directory if it is not under `/home`.

Polling intervals are in **milliseconds**: `6000` means 6 seconds, `12000` means 12 seconds and `20000` means 20 seconds. The weather command is explicitly scheduled every **five minutes**, regardless of the value currently shown in the interval editor.

The network panel refreshes **when opened** or when its bottom-left refresh icon is clicked. It does not periodically refresh its contents. Closing it cancels an active refresh or speed test.

### Change the weather location

Edit `PARAMS` in your installed `clima-widget.py`: set `latitude`, `longitude` and `timezone`, and update the Brasília display text and cache filename if needed. The script keeps the last valid forecast when a request fails.

Caches are stored under `$XDG_CACHE_HOME/orbitz-widgets`, falling back to `~/.cache/orbitz-widgets`. They are not tracked in this repository.

### Enable optional speed testing

Download/install the [official Ookla Speedtest CLI](https://www.speedtest.net/apps/cli) for your Linux architecture. Place the executable as `speedtest` inside the installed extension directory and give it execute permission:

```bash
chmod +x "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/speedtest"
```

The proprietary binary is **not bundled**. It has separate terms for personal, non-commercial use. Review the [EULA](https://www.speedtest.net/about/eula), [terms](https://www.speedtest.net/about/terms) and [privacy policy](https://www.speedtest.net/about/privacy) before enabling it: the integration invokes the CLI with license/privacy acceptance flags and has no additional acceptance dialog. A test transfers data over your internet connection.

## Reliability, security and performance

- One periodic command runs at a time per element; canceled executions cannot publish stale results.
- Combined stdout/stderr is limited to **256 KiB** per execution.
- Timeouts are **30 seconds** for periodic commands, **15 seconds** for panel refresh and **120 seconds** for speed tests.
- Command groups are terminated on cancellation; this is not a sandbox and does not cover descendants that deliberately create a separate session.
- Weather and DNS caches are validated and written atomically with restricted file permissions.
- Identical command text is not reapplied to the UI. Panel details are collected on demand.

Custom commands run with your account's permissions. Only import configuration files you trust. The panel's opening detector uses adaptive pointer checks for compatibility with the desktop layer; the project does not claim zero idle CPU or a measured percentage reduction.

## Troubleshooting

- **No widgets appear:** enable the extension and add command elements in its preferences.
- **A widget shows an error:** run its configured command in a terminal; check the path, required utilities and permissions.
- **No temperatures:** verify that your hardware exposes supported sensors; unsupported readings can remain unavailable.
- **Speed test unavailable:** check the binary's name, architecture and execute permission.
- **Changes do not load:** disable/re-enable the extension; if necessary, log out and back in.
- **Unsupported GNOME version:** check `gnome-shell --version` against the compatibility section.

## Contributing

Bug reports and pull requests are welcome. Include your distribution, GNOME/Python versions, affected widget and reproduction steps. Remove personal IP addresses, hostnames and credentials from logs before posting. Preserve the existing UI behavior and measurement semantics when proposing performance changes.

## Credits and licenses

Desktop Clock / azclock was created by **Andrew Zaech**. Original notices and asset credits are preserved in [`extension/README.md`](extension/README.md). Some upstream visual assets have their own Creative Commons attribution/share-alike terms; consult those credits.

Orbitz customizations and Python widgets: **orbitzone / Orbitz**. See [`LICENSE`](LICENSE) for the included GNU GPL v3 license text. System dependencies and Ookla Speedtest CLI retain their own licenses.

**Project topics:** GNOME Shell extension, Linux desktop widgets, Python system monitor, CPU monitor, RAM monitor, network monitoring, TCP connections, hardware temperatures, disk usage, weather widget and internet speed test.
