# Orbitz — Widgets for GNOME

**Custom Desktop Clock / azclock widgets for GNOME Shell: Linux system monitoring, network diagnostics, hardware temperatures, storage, weather and Now Playing — powered by Python and GJS.**

**Target platform: Ubuntu 22.04 LTS Desktop (Jammy), with GNOME Shell 42 and Python 3.10.** Ubuntu Server without a GNOME desktop and Ubuntu flavors using KDE/Xfce are not covered. Ubuntu 24.04 and later are not supported by this legacy extension.

Orbitz combines nine standalone Python widget scripts and shared runtime modules with a customized version of [Desktop Clock (azclock)](https://gitlab.com/AndrewZaech/azclock). Display system information directly on your GNOME desktop and open a network panel to inspect TCP connections, listening ports or run an optional internet speed test.

**Looking for azclock / Desktop Clock custom commands?** This project contains a customized copy of Andrew Zaech's **azclock v7** extension and ready-to-use Python command widgets for **Ubuntu 22.04 / GNOME 42**. It keeps the original `azclock@azclock.gitlab.com` UUID and is a community customization, not an official upstream release. See [installation](#download-and-install), [widget commands](#configure-each-widget) and [upstream azclock](https://gitlab.com/AndrewZaech/azclock).

[Download ZIP](https://github.com/orbitzone/orbitz-widgets-for-gnome/archive/refs/heads/main.zip) · [Report an issue](https://github.com/orbitzone/orbitz-widgets-for-gnome/issues) · [Source code](https://github.com/orbitzone/orbitz-widgets-for-gnome)

## Table of contents

- [Screenshots](#screenshots)
- [Desktop overview](#desktop-overview)
- [Security panel](#security-panel)
- [Docker panel](#docker-panel)
- [Firewall inspection](#firewall-inspection)
- [Now Playing](#now-playing)
- [Widgets](#widgets)
- [Stack and compatibility](#stack-and-compatibility)
- [Ubuntu 22.04: install dependencies first](#ubuntu-2204-install-dependencies-first)
- [Required packages](#required-packages)
- [Optional packages](#optional-packages)
- [Download and install](#download-and-install)
- [Configure each widget](#configure-each-widget)
- [Change the weather location](#change-the-weather-location)
- [Enable optional speed testing](#enable-optional-speed-testing)
- [Optional Now Playing widget: Spotify and Chrome/Chromium](#optional-now-playing-widget-spotify-and-chromechromium)
- [Per-widget requirements checklist](#per-widget-requirements-checklist)
- [Manual startup and stop control](#manual-widget-controller)
- [Docker widget](#docker-widget)
- [Firewall event widget](#firewall-event-widget)
- [Reliability, security and performance](#reliability-security-and-performance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Credits and licenses](#credits-and-licenses)

## Screenshots

Screenshots from the configured desktop on October 11, 2026. Layout, fonts and positions are configurable.

### Desktop overview

Clock/weather, processes, CPU/RAM/storage, temperatures and separate traffic, security, Docker and firewall widgets.

![Desktop with system metrics, weather and separate network, security, Docker and firewall widgets](docs/images/desktop-widgets.png)

### Security panel

Local TCP listeners and remote destinations. Opening the panel or clicking refresh collects a new snapshot. Speed testing is available separately by clicking the download/upload traffic widget.

![Security panel with TCP listeners, remote connections and manual refresh](docs/images/network-panel.png)

### Docker panel

Running containers and published host ports. Recognized web services open in the browser; other ports remain visible without an automatic web link.

![Docker panel showing Portainer and PostgreSQL port mappings](docs/images/docker-panel.png)

### Firewall inspection

Review persistent activity and changes across ports, destinations or protocols. Inspect selected IPs and ports for supporting evidence.

![Firewall pattern analysis with persistence, port variation and local-source context](docs/images/firewall-inspection.png)

### Now Playing

Playback status, artist and title, followed by a small Spotify or Chrome icon identifying the selected player.

![Now Playing showing Tech N9ne — Speedom with the Spotify icon after the title](docs/images/now-playing.png)

## Widgets

| Widget / script | What it does |
|---|---|
| **CPU, RAM and storage** — `cpu-ram-widget.py` | Shows CPU utilization, RAM usage and SSD usage for the filesystem containing your home directory, with text progress bars. An **EXT** row appears when external storage is mounted; its percentage combines used space and capacity across the detected filesystems, counting each filesystem once. The widget does not mount devices. |
| **Failed services** — `servicos-widget.py` | Counts failed systemd services for the system and current user separately. Click for compact cards with recorded result, exit status and state-change time in tooltips. Read-only, refreshed every 60 seconds. |
| **Top processes** — `processos-widget.py` | Lists up to seven processes ranked by CPU consumption. Click for a performance snapshot, CPU/RAM rankings, contextual suggestions and available process, startup and power-profile actions. Includes a compact PSI bottleneck summary and three detail columns for CPU, memory and storage I/O. Process usage may exceed 100% on multicore systems. |
| **Network traffic** — `rede-widget.py` | Shows current receive/transmit rates for the interface selected from the default route (IPv4, with IPv6 fallback). This measures traffic, not your connection's maximum speed. |
| **TCP connections and ports** — `seguranca-widget.py` | Counts non-loopback TCP connections and listening ports. Click the widget to open a panel with local ports and remote destinations; click a hostname to copy its full name. Counts do not indicate whether a connection is malicious. |
| **Hardware temperatures** — `temperaturas-widget.py` | Reads available CPU/GPU sensors from Linux sysfs, with an optional `sensors` fallback. Intel coretemp and AMDGPU are handled directly; unavailable readings display `N/D`. |
| **Firewall** — `firewall-widget.py` | Shows the number of noteworthy UFW activity patterns in a rolling 24-hour window. Click for persistence and path-variation evidence, with discovery traffic summarized as background noise. |
| **Weather** — `clima-widget.py` | Shows current conditions, temperature, feels-like temperature, humidity, daily low/high and precipitation probability through Open-Meteo. Defaults to Brasília, Brazil. |
| **Docker** — `docker-widget.py` | Counts running containers; opens a panel with names, published ports and browser links for web services. |

The download/upload traffic widget opens a dedicated quality and speed panel with an optional **Ookla Speedtest CLI** integration for download/upload speed in Mbps, latency in ms and the last test time. Results appear after a successful test. Speed tests run only when requested.

**Language:** this README is in English. Widget labels and panel messages currently remain in Portuguese. Script filenames are preserved for compatibility.

An optional **Now Playing** widget reads MPRIS metadata directly from Spotify and Chrome/Chromium, with a player icon after the title. It is configured separately and has no additional Python script.


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
| `python3` | All nine widgets and their helper modules; no pip packages required |
| `bash`, `util-linux`, `procps`, `coreutils` | Command execution, isolated process groups (`setsid`), cancellation (`/usr/bin/kill`), volumes (`lsblk`) and file installation |
| `iproute2`, `libc-bin` | TCP socket information (`ss`) and hostname lookup (`getent`) |
| `gjs`, `gir1.2-gtk-4.0`, `gir1.2-adw-1` | JavaScript runtime and preferences UI bindings |
| `libglib2.0-bin`, `gnome-shell-extension-prefs`, `dconf-cli` | Compile schemas, manage extension preferences and export/import configuration |
| `git`, `ca-certificates` | Download source and validate HTTPS requests |

The standard Ubuntu Desktop session supplies GNOME Shell, St, Clutter and the session D-Bus. Run the widgets as your desktop user, not with `sudo`.

### Additional packages by feature

A package being preinstalled does **not** make it optional. In particular, UFW is a requirement of the firewall widget even on Ubuntu installations that already include it.

**Required by a feature** means that the feature cannot work without the package/service/permission. Displaying “unavailable” instead of crashing is error handling, not successful operation. **Truly optional** means a working fallback exists or a supplemental action is omitted without breaking the main widget.

Install the packages for the features you intend to use. The following adds the complete temperature list, terminal actions, process/startup tools and hostname display support:

```bash
sudo apt install lm-sensors gnome-terminal gnome-system-monitor \
  gnome-startup-applications xdg-utils libpsl5 gir1.2-gweather-4.0
```

| Feature | Package / dependency | Purpose |
|---|---|---|
| Full temperature sensor panel | **`lm-sensors`**, which supplies **`sensors`** | `sensors -j` enumerates temperature readings, including Apple SMC sensors on supported hardware. The collector also reads Linux `/sys/class/hwmon` and thermal zones as a fallback. |
| NVIDIA temperature, when available | Matching NVIDIA driver providing `nvidia-smi` | Optional GPU query; use the driver appropriate for your hardware. `lm-sensors` alone does not supply this command. |
| Terminal actions | `gnome-terminal` | Displays the selected command and requires Enter before executing update or process actions. |
| Process inspection | `gnome-system-monitor` | Graphical process monitor. If absent, the action falls back to `top`, supplied by the required `procps` package. |
| Startup application review | `gnome-startup-applications` | Supplies `gnome-session-properties`. If absent, the action uses `xdg-open` to open the user's autostart folder. |
| Open startup folders and links | `xdg-utils` and a configured browser/file manager | Supplies `xdg-open` for the startup-folder fallback. Desktop links also use the session's default URI handler. |
| Power-profile actions | `power-profiles-daemon` | Supplies `powerprofilesctl`. Buttons appear only for profiles supported by the service and hardware. |
| Shortened network hostnames | `libpsl5` | Optional registrable-domain display; full hostnames are preserved for inspection/copy. |
| Preferences location/time-zone helper | `gir1.2-gweather-4.0` | Optional upstream preferences binding; independent of the Python Open-Meteo weather widget. |
| UFW pattern analysis | `ufw`, systemd journal and permission to read kernel logs | `journalctl` is supplied by `systemd` on the supported Ubuntu desktop. Logging must already be configured; installing a package alone does not enable collection. |
| Docker panel | Docker CLI and a running, accessible Docker daemon | Reads `docker ps`, `docker context inspect` and `docker inspect`. Docker access must be available to the desktop account. |
| Snap updates | `snapd` and its service | Supplies `snap`; only needed when monitoring/managing Snap packages. |
| Flatpak updates | `flatpak` and configured remotes | Only needed when monitoring/managing Flatpak applications. |
| APT updates | `apt` | Included with Ubuntu; used to inspect local indexes and open explicitly confirmed maintenance commands. |
| Internet speed test | Official **Ookla Speedtest CLI** | Separate optional installation described below. The Python package/command `speedtest-cli` is not the executable used by this integration. |
| Downloading the optional speed-test archive | `curl`, `tar` | Used only by the manual installation example below. |
| Controller and collector shutdown | `python3`, `coreutils`, `util-linux`; bundled `extension/stop-collectors.py` | Native `timeout`, `kill` and `setsid`, plus the owned-process-tree shutdown helper. No additional Python library or pip dependency is required. |

### Required services and tools for the complete widget suite

For all nine configured widgets, package providers and terminal maintenance actions, the following are **feature requirements**, not merely cosmetic extras:


```bash
sudo apt install lm-sensors gnome-terminal ufw snapd flatpak

# If Docker is not already installed: Ubuntu's packaged Docker distribution.
# Existing Docker Engine/CLI installations can be used instead.
sudo apt install docker.io
```

These packages are in addition to the base packages above. Existing Docker Engine/CLI installations satisfy the Docker requirement; do not install a second distribution just to satisfy this guide.

Package installation alone is insufficient: the Docker daemon must be running and accessible, UFW must have usable logging and the session must be able to read it, and Snap/Flatpak need their services or remotes as appropriate. Installing UFW does not enable firewall policy or logging. This guide does not automatically change those settings.

Without Docker/daemon access, the Docker widget reports unavailable. Without readable UFW logs, firewall analysis cannot produce a verified diagnosis. Without `gnome-terminal`, terminal actions cannot open. Without `lm-sensors`, `/sys` fallback may show some temperatures, but the complete sensor list is not guaranteed. Missing Snap or Flatpak is reported as “Não instalado” during package listing; commands that invoke those tools still require them. In particular, the combined “Buscar atualizações” command requires APT, Snap **and** Flatpak. Choose only installed-provider actions if using a reduced setup.

### Optional enhancements with defined fallback

| Package | Actual behavior when absent |
|---|---|
| `gnome-system-monitor` | The process action uses `top` from required `procps` instead. |
| `gnome-startup-applications` | Startup review opens the autostart folder using `xdg-open`; install `xdg-utils` for this fallback. |
| `libpsl5` | Full hostnames are shown instead of shortened registrable domains. |
| `gir1.2-gweather-4.0` | Preferences disable location search; other settings and the Python weather widget remain available. |
| `power-profiles-daemon` | Profile actions are omitted; the process monitoring widget still works. Install this package to use `powerprofilesctl`, subject to hardware support. |

The Ookla CLI is **required to execute the speed-test button**; it is not required to list network connections. NVIDIA's `nvidia-smi` is similarly a requirement for that GPU query, not for unrelated CPU sensors. This distinction applies to individual capabilities, not to every component of the suite.

For sensors, verify the command before opening the temperature panel:

```bash
sensors
sensors -j
```

Only temperatures actually exposed by the hardware and loaded drivers can be displayed. Invalid or inaccessible readings are omitted. Installing `lm-sensors` does not create unavailable sensors; the widget does not automatically run `sensors-detect`, load kernel modules or alter fan controls.

Internet access is required for package downloads, weather and speed tests; DNS lookup depends on your resolver. CPU/RAM/storage and temperature monitoring work locally. The built-in Now Playing integration uses MPRIS over the session D-Bus and **does not require `playerctl`**, even though its compatibility command label contains that name.

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

Open its preferences to add widgets and configure command elements, fonts, colors, positions and alignment. Personal layout settings are not bundled: copying the files does not automatically create the widgets.

### Configure each widget

Add a command element for each script you want. Use an absolute path, replacing `YOUR_USER` with your Linux username:

```text
python3 /home/YOUR_USER/.local/share/orbitz-widgets/cpu-ram-widget.py
```

In the preferences, add a widget, add a **command** element, paste its command and set its polling interval. Repeat for each script. Fonts, colors, orientation and positioning are manual preferences; no personal layout is automatically imported.

To generate the eight absolute command paths for your account:

```bash
for script in cpu-ram-widget.py processos-widget.py rede-widget.py \
  seguranca-widget.py temperaturas-widget.py clima-widget.py firewall-widget.py docker-widget.py servicos-widget.py armazenamento-widget.py; do
  printf 'python3 "%s/.local/share/orbitz-widgets/%s"\n' "$HOME" "$script"
done
```

Copy the resulting lines into the appropriate command elements. Keep the Python filenames unchanged: network-panel detection and the weather interval use them.

Change the filename for the other entries in the widget table. Use the actual path to your home directory if it is not under `/home`.

Polling intervals are in **milliseconds**: `6000` means 6 seconds, `12000` means 12 seconds and `20000` means 20 seconds. Set weather to **300000 ms** (five minutes); the extension enforces that schedule. The interval editor now accepts values up to one hour. Keep **traffic and security in separate widgets**, each with one command element, so they can be positioned independently.

The network panel refreshes **when opened** or when its bottom-left refresh icon is clicked. It does not periodically refresh its contents. Closing it cancels an active refresh or speed test.

### Change the weather location

Edit `PARAMS` in your installed `clima-widget.py`: set `latitude`, `longitude` and `timezone`, and update the Brasília display text and cache filename if needed. The script keeps the last valid forecast when a request fails.

Runtime caches use `$XDG_CACHE_HOME/orbitz-widgets`, falling back to `~/.cache/orbitz-widgets`. Weather and DNS retain a sibling `work/` directory next to the scripts directory. Caches are private, validated and excluded from the repository.

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

Add a separate command widget with this command value:

```text
playerctl -p spotify,chromium metadata
```

The customized extension recognizes this value and reads **MPRIS directly over the session D-Bus**. Playerctl is not required for this built-in integration and no shell pipeline runs each second. Metadata updates through player/property events; the polling control indicates event-based updates.

The widget displays playback status, artist and title as plain text, followed by a **16 px Spotify or Chrome SVG icon**. A playing player takes priority over a paused one; Spotify wins when both are playing. The icon is hidden when no matching player is available. Spotify, Chromium and Chrome must expose MPRIS metadata in the same desktop session. Website metadata may omit the artist.

This display does not capture audio, require a Spotify API key or control playback. Custom Playerctl commands outside this recognized value still use the regular command execution path. Playerctl can be installed separately for diagnostics, but is optional.

## Per-widget requirements checklist

| Feature | Additional requirement beyond the required packages |
|---|---|
| CPU/RAM/home filesystem | Linux `/proc` and access to your home filesystem |
| Top processes | Readable `/proc`; some processes may be hidden by system permissions |
| Traffic | Active default route (IPv4, with IPv6 fallback); the selected interface may be a VPN |
| TCP panel | `ss`/`getent`; hostname lookup can be absent or time out |
| Temperatures | Supported hardware sensors/drivers; optional lm-sensors |
| Weather | Internet access and correct coordinates/time zone; default is Brasília |
| Speed test | Separate official Ookla executable, correct architecture and accepted terms |
| Docker | Docker CLI and permission to query the configured daemon |
| Now Playing | An application exposing MPRIS in your session; built-in mode does not require Playerctl |

Package names were checked against Ubuntu 22.04 sources and the development machine. **A full clean-VM installation test has not yet been performed**, so this guide does not claim that all hardware/app combinations have been validated.

## Docker widget

Configure a separate command widget with `python3 /home/YOUR_USER/.local/share/orbitz-widgets/docker-widget.py`. Its label is **Docker Containers: N**. Use a 15000 ms interval for the summary. Click it to open a panel listing running containers and their published host ports; refresh is manual.

The collector uses read-only `docker ps` and projected `docker inspect` queries. It does not start or stop containers, alter firewall rules or change socket permissions. A TCP listener list alone does not necessarily show Docker NAT mappings, which is why Docker has its own widget.

The panel shows up to 100 port entries and reports omitted entries. Unpublished containers still appear. Known web ports receive browser links; UDP, PostgreSQL and Portainer's tunnel port 8000 do not receive automatic links. The sample Portainer mapping 9443 → 9000 uses HTTP, based on its internal web port.

To specify another protocol, host or application path, create `~/.config/orbitz-widgets/docker-urls.json`:

```json
{"portainer:9443": "http://127.0.0.1:9443", "my-service:1234": "https://localhost:1234/app"}
```

Keys may be `container-name:host-port` or just `container-name`. URLs require HTTP/HTTPS and an explicit port, without embedded credentials, query or fragment. Automatic localhost links are disabled for remote Docker contexts; configure an accessible URL explicitly.

## Firewall event widget

Configure a command element with `python3 /home/YOUR_USER/.local/share/orbitz-widgets/firewall-widget.py`. The extension refreshes its summary every 60 seconds. Opening the panel or clicking refresh updates the analysis and shows supporting evidence.

Requires UFW logging and permission to read kernel journal entries in your session. The collector never invokes sudo or changes firewall rules. Collection failures retain the previous snapshot and explicitly mark it as unavailable or stale. Logged events are not a complete count of blocked packets: logging may be rate-limited or disabled.

The collector uses journal cursors to resume after the last processed record. Each round reads up to 10,000 records within an eight-second budget; subsequent rounds continue the backlog without recounting old records. Data is aggregated into five-minute intervals and expires after approximately 24 hours. The cache is bounded to 8 MiB and 512 origins; incomplete collection or storage eviction is reported as partial coverage. The panel shows up to 30 prioritized patterns and reports additional patterns.

Initial review criteria:

- **Persistence with variation:** at least 12 records across three five-minute intervals spanning ten minutes, plus six destination ports, three destination addresses or two protocols.
- **Persistent repetition:** the same temporal persistence, with at least 30 records even without path variation.
- **Many-port sequence:** at least 30 records across 12 destination ports, even within a short burst.

Multicast, IGMP and common local UDP discovery are summarized rather than rendered as incident cards. Local/reserved origins receive explicit context about potentially legitimate device communication. Each card explains the observations, timestamps and recent activity. These are review heuristics, not proof of an attack or authentication failures.

Click an IP or destination port to inspect cached supporting evidence and recent raw samples. Port inspection also queries visible local listeners. Reverse DNS and public-IP RDAP remain explicit manual actions.

The process modal samples CPU, available RAM, swap, CPU temperature when available and home-partition free space. It ranks processes by CPU and RSS, offers contextual suggestions and exposes only installed process/startup tools and supported power profiles. Buttons show their effect and command in tooltips. Actions open in a terminal and require Enter before execution; selecting performance mode can increase energy use, heat and noise. RAM caches are not automatically cleared.

Use the copy button to copy the selected address/port and Back to return to the grouped overview. Inspection runs only on click, with a timeout, output cap and cancellation on close, refresh or a new selection.

Reverse DNS is a separate opt-in button. Public IPs additionally offer an external WHOIS/RDAP link through [RDAP.org](https://about.rdap.org/), opening registry information in the browser. These actions may disclose the queried address to the resolver/provider and are never performed automatically. No WHOIS package, API key or background lookup service is required.

The refresh shares the network panel's timeout, bounded output, cancellation and stale-response protections. The cache is private and atomic. Adaptive pointer detection is still used for opening the panel; there is no background log watcher.

## Reliability, security and performance

- CPU, process and traffic widgets share one persistent Python collector. Their one-second sampling windows are preserved; use 12000, 12000 and 6000 ms intervals respectively. Install **all `widgets/*.py` files together**, including `metrics-worker.py` and `widget_runtime.py`.
- Media uses MPRIS events; panel-opening detection uses one shared adaptive timer. Unchanged clock text does not trigger another relayout.
- Sensor discovery, volume inventories and home-filesystem usage use validated caches of up to one minute. Volume mount changes invalidate the inventory; IPv6 routes are supported for traffic fallback.
- Regular commands run once at a time per element, with stale-response protection. Combined stdout/stderr is capped at **256 KiB**; Python collectors also use bounded reads, with a **2 MiB** kernel-log limit.
- Timeouts remain **30 seconds** for regular commands, **15 seconds** for panel refresh and **120 seconds** for speed tests. Group cancellation is asynchronous; the metrics collector has a watchdog and restart delay.
- Security details display at most **200 connections**, Docker at most **100 entries**, and firewall at most **30 pattern cards**, with truncation indicated where applicable.
- Settings export uses typed JSON. Import accepts JSON and legacy dconf data, validates schema/structure/size, and presents commands for confirmation before applying them. It does not spawn `dconf load`.

Custom commands execute with your account's permissions. Cancellation is not a sandbox and cannot contain descendants that deliberately create another session. Docker access retains the daemon's existing privileges; no new permissions are granted by these widgets.

Syntax checks, GJS subprocess/cancellation tests, malformed-data cases, cache/URL validation and package hashes were verified after the changes. Full desktop CPU/memory profiling and a clean-VM installation test have not been completed; no global percentage performance improvement is claimed.

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

**Project topics:** azclock, Desktop Clock, azclock custom commands, Desktop Clock widgets, Ubuntu 22.04, GNOME Shell extension, Linux desktop widgets, Python system monitor, CPU monitor, RAM monitor, network monitoring, TCP connections, hardware temperatures, disk usage, weather widget, Spotify now playing, MPRIS, Docker containers and internet speed test.

Clock/weather widgets keep a default width of 440 px and wrap long text onto additional lines. Other widgets use their natural width. Set **Widget width (px; 0 = default)** to override the width and enable wrapping for a particular widget; anchors use the final width and height.

The **Atualizações** widget (`atualizacoes-widget.py`, Ubuntu) groups APT, Snap and Flatpak updates, installed/available versions, APT security origins and reboot-requesting packages. APT reads local indexes; Flatpak uses cached metadata; Snap queries its service. Old APT indexes, failures and partial results are explicitly marked. Refresh is manual; opening the dialog rereads the list. Action buttons use a compact four-column grid with command tooltips; the unused-dependency action is labeled “Remover sobras”.

Actions open GNOME Terminal, display the command and wait for Enter before execution. APT update, upgrade, full-upgrade, autoclean, autoremove, Snap refresh, Flatpak update and update/upgrade/autoclean are separate choices. APT retains its normal confirmations; no passwords are stored. After completing an action, click **Reler lista**.

Custom buttons are defined in `~/.config/orbitz-widgets/update-actions.json`, a JSON array of up to ten objects with `name` and `command` strings. Example: `[{"name":"Atualizar APT","command":"sudo apt update && sudo apt upgrade"}]`. Commands run only through an explicit click and terminal confirmation.

Click the CPU/GPU temperature widget to view available temperature sensors grouped by component in a single row of four fixed columns: CPU, GPU, RAM and storage on the left two; auxiliary sensors on the right two, with manual refresh. Groups share columns, with headings and spacing only inside each column. Repeated driver labels are moved to the help tooltip to save space. Readings above 80 °C are red in the summary and details. Unavailable or invalid sensor values are hidden from the detail panel and reappear after a successful refresh. Each sensor has a question-mark button with a brief description shown on hover, focus or click. Unknown SMC locations are explicitly labeled as unidentified. The detail panel uses fixed columns without pagination or vertical scrolling. The configured summary polling interval is unchanged.

## Regression checks

Run `python3 -m unittest discover -s tests -v` and `node tests/test_temperature_layout.js` after widget changes. The [individual audit](docs/auditoria-widgets-2026-10-14.md) records fixes, measurements and validation limits. Bounded subprocesses also use the coreutils `timeout` watchdog.

## Manual widget controller

The controller is a separate extension component, not one of the configured desktop widgets. Its purpose is to **reduce the risk of desktop freezes or login-session failures caused by automatically starting a faulty widget or dependency during Linux startup**: after every login or extension enable, the widget suite starts **paused** and waits for an explicit click. This is a manual startup gate, not a guarantee against every system failure.

The transparent 40×36-pixel control uses a 24-pixel SVG icon:

- **White:** widgets are stopped; click to start the suite.
- **Lime green:** widgets are running; click to stop the suite. The control remains unavailable while shutdown finishes.
- **Position:** upper-right corner of the monitor containing the most saved widget positions; primary monitor fallback. Only saved-position metadata is read before activation. Full configuration validation, widget construction, collectors and polling timers wait for the start click.

Stopping destroys widget actors and dialogs, removes timers and subscriptions, cancels in-flight reads, and terminates owned collector process trees, including subprocesses in separate sessions or created by worker threads. The control remains available for another start. Configuration and cache files remain on disk without executing code. The active state is not restored automatically on the next login.

Configuration or widget-construction failures roll back startup and leave the control available. The switch cannot isolate syntax/module-loading errors in the extension itself, kernel/driver faults or failures in GNOME. External applications and terminal actions explicitly opened by the user have their own lifecycle: stopping the widgets does not interrupt package installation or shut down system services.

Implementation files:

- [`extension/extension.js`](extension/extension.js), class `AzClock`: control, monitor selection, manual startup and teardown.
- [`extension/stop-collectors.py`](extension/stop-collectors.py): verifies process ownership and start time before stopping collector trees. Keep this file installed alongside `extension.js`.
- [`extension/media/controls/`](extension/media/controls/): white and lime SVG assets; keep this directory in the installed extension.

Controller regression checks: `node tests/test_widget_controller.js` and `python3 -m unittest discover -s tests -v`. The lifecycle test uses mocked GNOME actors; process-tree termination is tested with real child processes. See the individual audit for the validation limits.

### Bottleneck indicators (PSI)

The processes widget reads `/proc/pressure/{cpu,memory,io}` alongside its existing sample. Click it to see three columns with 10-, 60- and 300-second averages, suggestions, and a manual refresh. Below them, two compact cards show the top three CPU and RAM consumers; tooltips carry process IDs, system details and observations. The processes panel does not use a scrolling list. No additional sampling process, timer, network call or disk history is created. The master control stops this collection with the other widgets.

PSI measures time during which tasks wait for resources, **not resource utilization** or attribution to a specific process. Yellow (at least 5%) and red (at least 20%) use the 10-second `some` average as UI heuristics, not universal fault thresholds. Memory and I/O also show `full`, when all non-idle tasks are stalled; system-level CPU `full` is intentionally omitted. Low PSI does not rule out application-specific problems. Missing or unreadable PSI is shown as unavailable/partial, never as healthy.

Requires kernel PSI support and read access to `/proc/pressure`; no extra package or administrator permission is needed. Install `pressure_metrics.py` with the other `widgets/*.py` helpers. See the [kernel PSI documentation](https://docs.kernel.org/accounting/psi.html).

### Failed services

The services widget requires `systemctl` (from Ubuntu's `systemd` package), a running systemd system manager and access to the current user's systemd manager for session services. It queries only failed `.service` units; failed timers, sockets and historical failures of units no longer marked failed are outside this view. Missing tools, denied queries or an unavailable user bus are reported as incomplete, never as a verified healthy state.

Use `python3 /path/to/widgets/servicos-widget.py` with a 60000 ms polling interval. The widget is included in the settings template and follows the master start/stop control. A summary uses two bounded queries; opening or manually refreshing the panel adds at most one batched detail query per scope. Each query has a two-second timeout and an output cap. Up to six services per scope are displayed, with the remaining count indicated.

Tooltips show systemd's `Result`, `ExecMainStatus` and `StateChangeTimestamp`, when available. The timestamp is the last state change, not a guaranteed failure time; a result or exit status alone does not establish the root cause. This widget does not read journal messages, use sudo, restart services or reset failure records. Detailed log investigation remains available through `journalctl -b -u UNIT` (or `journalctl --user -b -u UNIT`) according to your session's permissions.

### Connection quality and traffic panel

Click the download/upload widget (`rede-widget.py`) to open quality cards and the manual Ookla speed test. The external-connections panel now focuses only on listeners and remote connections. Quality is measured on opening this panel or clicking **Testar qualidade**, never by the background traffic collector. Closing the panel or stopping the widget suite cancels active tests. Quality and speed tests cannot run simultaneously.

Install **`iputils-ping`** for ICMP probes and **`iproute2`** for IPv4 gateway discovery (`sudo apt install iputils-ping iproute2`). The quality feature requires both; traffic counters still work without them. Install `network_quality.py` beside `rede-widget.py`. Each quality sample sends five numeric-address ICMP probes to the default IPv4 gateway and five to **1.1.1.1 (Cloudflare)**. Gateway discovery is capped at one second; each probe process at four seconds, with bounded output. A VPN or IPv6-only connection may not expose an IPv4 gateway.

Cards show average round-trip time and sample packet loss; tooltips identify the destination and timing variation (ping mdev). Color thresholds are illustrative: yellow for any loss or latency over 20 ms locally / 100 ms externally, red for at least 20% loss. Five packets provide only a short sample. ICMP filtering or rate limiting can produce nonresponses without an internet outage; one external destination does not characterize every application or diagnose the cause. The optional speed test transfers substantially more data and starts only when its button is clicked.

### Storage space and disk health

Storage is integrated into the **Stats** widget (`cpu-ram-widget.py`): click the **SSD** line for internal volumes or **EXT** for removable/desktop-mounted volumes. There is no separate storage widget. A `!` before SSD indicates at least one internal volume at 90% space/inode usage. Disk usage and the internal alert inventory are cached for 60 seconds. `armazenamento-widget.py` is the shared details helper. The panel uses a three-column card grid with available space, usage bars and SMART status. Tooltips show capacity, inode usage, device/model, temperature and NVMe estimated life consumed when available. Volumes mounted multiple times are deduplicated by filesystem device ID. Unmounted partitions, loop/Snap filesystems and network filesystems are outside the block-device inventory. Up to twelve filesystems are displayed; truncation is indicated.

Requires `lsblk` from `util-linux`. **SMART health additionally requires `smartctl` from `smartmontools`, compatible hardware and existing read permission** (`sudo apt install smartmontools` installs the package, but does not grant device access). Without SMART, filesystem space remains functional and health is explicitly unavailable. The widget does not invoke sudo, change permissions, wake standby disks intentionally, mount filesystems or start disk self-tests. SMART is queried only when opening/refreshing details, at most four devices, two seconds each; inventory has a three-second timeout and bounded output. A SMART pass is not a guarantee against failure.

Space/inode usage is yellow at 90% and red at 95%. NVMe critical warnings, reported SMART failure or estimated life consumed at least 100% mark disk health for attention. A healthy space indicator does not assert healthy hardware. The master widget control starts and stops the collector as with the other command widgets.

EXT details show capacity and free space plus a first-level directory listing (six entries per card, up to thirty in its tooltip). Subdirectories and file contents are not opened, symlinks are not traversed, and permission errors are shown. SSD cards also display total filesystem capacity explicitly. Volumes on USB/removable devices or mounted under `/media`, `/run/media`, or `/mnt` are treated as external. The SSD usage percentage accounts for space unavailable to the current user (including filesystem reservations), matching the details card. Install the storage helper alongside `cpu-ram-widget.py`.

### Parent widgets and automatic layout

Choose **Add Widget → Widget pai · painel** to create a panel, or enable **Usar como widget pai** in an existing widget. In each existing widget's configuration, **Widget pai · mover para** moves it into the selected panel; selecting **Desktop · sem pai** detaches it. **Criar subwidget** creates an empty child for adding elements through its configuration page. Grouped widgets are marked with ↳ in the list; panels use ▦. The list order controls child order, and the parent controls the grid's one to four columns, spacing, padding, background and position. Width expands to accommodate a minimum card width rather than overlapping columns.

Children retain their commands, sampling intervals and click-open panels, while the container provides consistent card styling and text alignment. Their saved desktop coordinates are retained and ignored while grouped. Move the whole panel rather than aligning individual rows. Deleting a parent returns its children to their saved desktop positions by default; the confirmation also offers deleting its children. Disabling panel mode always releases the children. Cloning a panel creates a fresh ID and does not steal its children. One grouping level is supported; invalid or missing parent relationships fall back to the desktop. No new polling loop or collector is added for layout. The master start/stop control destroys all child actors and their collectors normally.
