# Orbitz — Widgets for GNOME

**Linux desktop widgets for system monitoring, network diagnostics, hardware temperatures, storage and weather — powered by GNOME Shell and Python.**

**Target platform: Ubuntu 22.04 LTS Desktop (Jammy), with GNOME Shell 42 and Python 3.10.** Ubuntu Server without a GNOME desktop and Ubuntu flavors using KDE/Xfce are not covered. Ubuntu 24.04 and later are not supported by this legacy extension.

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

An optional **Now Playing** command widget uses `playerctl` / MPRIS to show media from Spotify and Chrome/Chromium. It is configured separately; it is not an eighth Python script.

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

## Ubuntu 22.04: install dependencies first

Check the desktop/runtime before installation:

```bash
. /etc/os-release
printf '%s\n' "$PRETTY_NAME"
gnome-shell --version
python3 --version
```

Expect Ubuntu **22.04**, GNOME Shell **42.x** and Python **3.10.x**. Do not bypass GNOME's version check to install this extension on GNOME 45+.

### Required packages

These commands install dependencies, not the widgets. Run them on your Ubuntu 22.04 desktop:

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update
sudo apt install git python3 bash util-linux procps iproute2 libc-bin \
  coreutils ca-certificates libglib2.0-bin dconf-cli gjs \
  gnome-shell-extension-prefs gir1.2-gtk-4.0 gir1.2-adw-1
```

| Packages | Used for |
|---|---|
| `python3` | All seven scripts; no pip packages required |
| `bash`, `util-linux`, `procps`, `coreutils` | Command execution, isolated process groups (`setsid`), cancellation (`/usr/bin/kill`), volumes (`lsblk`) and file installation |
| `iproute2`, `libc-bin` | TCP socket information (`ss`) and hostname lookup (`getent`) |
| `gjs`, `gir1.2-gtk-4.0`, `gir1.2-adw-1` | JavaScript runtime and preferences UI bindings |
| `libglib2.0-bin`, `gnome-shell-extension-prefs`, `dconf-cli` | Compile schemas, manage extension preferences and export/import configuration |
| `git`, `ca-certificates` | Download source and validate HTTPS requests |

The standard Ubuntu Desktop session supplies GNOME Shell, St, Clutter and the session D-Bus. Run the widgets as your desktop user, not with `sudo`.

### Optional packages

```bash
sudo apt install lm-sensors libpsl5 gir1.2-gweather-4.0
```

- `lm-sensors`: temperature fallback/diagnostics; run `sensors` to inspect available readings. A package cannot create a sensor your hardware/driver does not expose. Direct temperature handling is for Intel coretemp and AMDGPU; NVIDIA and other hardware may remain unavailable.
- `libpsl5`: shortened registrable-domain display for network hostnames; the full hostname is still copied on click.
- `gir1.2-gweather-4.0`: the upstream preferences' location/time-zone helper. This is separate from the Python weather widget, which uses Open-Meteo and the standard library.

Internet access is required for package downloads, weather and speed tests; DNS lookup depends on your resolver. CPU/RAM/storage monitoring works locally.

## Download and install

Clone the repository, or download and extract the ZIP linked above:

```bash
git clone https://github.com/orbitzone/orbitz-widgets-for-gnome.git
cd orbitz-widgets-for-gnome
```

**Existing Desktop Clock users:** back up your extension directory and export your settings first. For example:

```bash
dconf dump /org/gnome/shell/extensions/azclock/ > "$HOME/azclock-settings-backup.ini"
if [ -d "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com" ]; then
  cp -a "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com" \
    "$HOME/azclock-extension-backup-$(date +%Y%m%d-%H%M%S)"
fi
```

Orbitz keeps the UUID `azclock@azclock.gitlab.com` and replaces that installation; it is not a separate extension that can run alongside the original.

From the repository root:

```bash
mkdir -p "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com"
cp -a extension/. "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/"
glib-compile-schemas "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/schemas"

mkdir -p "$HOME/.local/share/orbitz-widgets"
cp widgets/*.py "$HOME/.local/share/orbitz-widgets/"
```

Log out and back in so GNOME discovers the installed extension. Then enable **Desktop Clock** through the GNOME Extensions app, or run:

```bash
gnome-extensions enable azclock@azclock.gitlab.com
gnome-extensions prefs azclock@azclock.gitlab.com
```

Open its preferences to add widgets and configure command elements, fonts, colors, positions and alignment. Personal layout settings are not bundled: copying the files does not automatically create the seven widgets.

### Configure each widget

Add a command element for each script you want. Use an absolute path, replacing `YOUR_USER` with your Linux username:

```text
python3 /home/YOUR_USER/.local/share/orbitz-widgets/cpu-ram-widget.py
```

In the preferences, add a widget, add a **command** element, paste its command and set its polling interval. Repeat for each script. Fonts, colors, orientation and positioning are manual preferences; no personal layout is automatically imported.

To generate the seven absolute command paths for your account:

```bash
for script in cpu-ram-widget.py processos-widget.py rede-widget.py \
  seguranca-widget.py temperaturas-widget.py volumes-widget.py clima-widget.py; do
  printf 'python3 "%s/.local/share/orbitz-widgets/%s"\n' "$HOME" "$script"
done
```

Copy the resulting lines into the appropriate command elements. Keep the Python filenames unchanged: network-panel detection and the weather interval use them.

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

For **x86_64 / amd64** only, this example downloads the official Linux CLI 1.2.0 without adding a system repository. Check `uname -m`; for another architecture use the matching download on Ookla's official page.

```bash
sudo apt install curl tar
speedtest_tmp=$(mktemp -d)
curl --fail --location --proto '=https' --tlsv1.2 \
  https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz \
  -o "$speedtest_tmp/speedtest.tgz" && \
  tar -xzf "$speedtest_tmp/speedtest.tgz" -C "$speedtest_tmp" speedtest && \
  install -m 755 "$speedtest_tmp/speedtest" \
    "$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/speedtest"
rm -rf "$speedtest_tmp"
```

Verify installation without running a bandwidth test:

```bash
"$HOME/.local/share/gnome-shell/extensions/azclock@azclock.gitlab.com/speedtest" --version
```

The proprietary binary is **not bundled**. It has separate terms for personal, non-commercial use. Review the [EULA](https://www.speedtest.net/about/eula), [terms](https://www.speedtest.net/about/terms) and [privacy policy](https://www.speedtest.net/about/privacy) before enabling it: the integration invokes the CLI with license/privacy acceptance flags and has no additional acceptance dialog. A test transfers data over your internet connection.

## Optional Now Playing widget: Spotify and Chrome/Chromium

The extra component is [**playerctl**](https://github.com/altdesktop/playerctl), a command-line client for the **MPRIS** media interface on your session D-Bus. No additional GNOME media extension or Python package is required for this command widget.

```bash
sudo apt install playerctl
playerctl --version
```

Install the media applications separately if needed:

- **Spotify:** the official [Spotify Snap](https://snapcraft.io/spotify) can be installed with `sudo snap install spotify`. If Snap support was removed, install `snapd` first with `sudo apt install snapd` and follow its session/restart instructions.
- **Google Chrome:** download the official **64-bit `.deb` for Debian/Ubuntu** from [Google](https://www.google.com/chrome/), then install the downloaded file with `sudo apt install ./google-chrome-stable_current_amd64.deb` from its directory. This example is for amd64; follow Google's supported system requirements for other machines.
- **Chromium:** an alternative on Ubuntu is `sudo snap install chromium`.

Open Spotify or Chrome/Chromium, start playback and inspect which players are exposed:

```bash
playerctl --list-all
playerctl metadata --format '{{status}}  {{artist}} — {{title}}'
```

Add another **command** element in Desktop Clock. This example selects Spotify and Chromium/Chrome, escapes media text before the extension renders markup, and stays visually blank if no matching player is available:

```text
playerctl -p spotify,chromium,chrome metadata --format '{{status}}  {{artist}} — {{title}}' 2>/dev/null | python3 -c 'import html,sys; text=sys.stdin.read().strip(); print(html.escape(text) if text else "\u200b")'
```

Use the names printed by `playerctl --list-all` if your applications expose a different name. Spotify is listed first in the selection; if several apps are open, select the specific player you want with `-p NAME`. You may also omit `-p` to use Playerctl's default selection.

Set a finite polling interval such as `6000` ms for this element. Do **not** use `--follow` in a periodically executed widget: it would leave the command running until the extension's timeout.

Browser playback must expose MPRIS/media metadata. Not every site provides artist/title, and sandboxed applications may not expose a player. If Chrome is absent from the list, check its media integration/settings and restart playback/the browser; Playerctl cannot display a player that the browser does not advertise. This integration displays metadata; it does not fix playback failures or install Spotify/Chrome automatically.

## Per-widget requirements checklist

| Feature | Additional requirement beyond the required packages |
|---|---|
| CPU/RAM/home filesystem | Linux `/proc` and access to your home filesystem |
| Top processes | Readable `/proc`; some processes may be hidden by system permissions |
| Traffic | Active IPv4 default route; the selected interface may be a VPN |
| TCP panel | `ss`/`getent`; hostname lookup can be absent or time out |
| Temperatures | Supported hardware sensors/drivers; optional lm-sensors |
| External volumes | Mounted removable/external volumes; an empty widget can be normal |
| Weather | Internet access and correct coordinates/time zone; default is Brasília |
| Speed test | Separate official Ookla executable, correct architecture and accepted terms |
| Now Playing | Separate Playerctl package and an application exposing MPRIS in your session |

Package names were checked against Ubuntu 22.04 sources and the development machine. **A full clean-VM installation test has not yet been performed**, so this guide does not claim that all hardware/app combinations have been validated.

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

**Project topics:** GNOME Shell extension, Linux desktop widgets, Python system monitor, CPU monitor, RAM monitor, network monitoring, TCP connections, hardware temperatures, disk usage, weather widget, Spotify now playing, MPRIS, Playerctl and internet speed test.
