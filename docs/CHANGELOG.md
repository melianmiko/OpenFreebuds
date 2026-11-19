# 0.19.0
- [Device compatibility] Add full HUAWEI FreeBuds 5 support: dual-connect, L2HC, custom EQ, low-latency mode, half-in-ear detection, find-earbud, case battery, two ANC modes and level control. HD spatial audio remains Huawei-phone only.
- [Device compatibility] Register FreeBuds Lipstick 2 as a FreeBuds 5 alias; the official command pages match and only shell/color assets differ.
- [Device compatibility] Align gesture registration with the 2.0.7.321 touchsetting config: Pro 2 gains light-hold and custom EQ, Pro 3 gains light-hold and charging-box tone, Pro 4 gains double/triple tap and adaptive volume, FreeBuds 7 gains light-hold and in-call double-tap, and FreeClip 1st gen is limited to its official double/triple set.
- [Device compatibility] Restrict independent spatial audio to FreeBuds 7 / 7i / Neo, FreeBuds Pro 5 and FreeClip 2 / 2 S. Pro 3 / Pro 4 keep Huawei-phone-side HD spatial audio only and no longer mount the independent handler.
- [Device compatibility] Limit charging-case tone controls by model: FreeBuds Pro 3, Pro 4 and FreeClip 1 expose only the master switch; FreeClip 2/2 S, FreeBuds 6/7 and FreeBuds Pro 5 keep the full lid/tone controls.
- [Device compatibility] Expose drop reminder on FreeBuds 7, FreeBuds 6, FreeClip 2, FreeClip 2 S, FreeClip and FreeBuds Neo; Neo mounts because its official config declares `drop_detection`, and runtime support is decided by the device response.
- [Feature] Add a smart-charging switch (`config.smart_charge`, MBB feature 4) with readback, GUI group and translations; mounted for FreeBuds 6/7/7i/Neo, FreeBuds Pro 4/5 and FreeClip 2/2 S. Verified read/write on FreeClip 2.
- [Feature] Add a left-right auto-switch (`config.left_right_auto`, `0x2B9A`) with readback, GUI group and translations; mounted for FreeClip, FreeClip 2/2 S and the new W Buds 1/2 minimal driver. W Buds support is response-gated; hardware read/write on FreeClip 2 remains unverified because SPP returned 10048.
- [Feature] Listen for HUAWEI `0x2B7F` prompt events: cleaning reminder, cleaning cancelled, earbud not seated and drop. The parser is read-only and is mounted on FreeClip 1/2/2 S (cleaning + drop) and FreeBuds 6/7/Neo (drop only). Frames are assumed to arrive over SPP from the captured IConnect TLV; IConnect transport is not implemented and SPP delivery is still unverified.
- [Feature] Show prompt events as cross-platform system notifications. Drop uses a high-priority notification, cleaning and misplacement use normal priority, and cleaning cancellation clears the existing notification where the platform supports it. Windows/macOS use the Qt system tray; Linux prefers freedesktop D-Bus notifications and falls back to Qt.
- [Change] FreeClip 1 now uses a standalone driver with an explicit handler list instead of inheriting the Pro 3 driver.
- [Fix] Device info shows the market name `HUAWEI FreeClip` for model `00014B` instead of the internal codename `Dove`.
- [Docs] Correct FreeClip 1 gesture documentation: it has no swipe; its lab click-and-hold / five-tap volume modes are not modeled yet. The APK lab page lists `00014B`, and its MBB `0x2BB2` backend exists, so this is a handler gap rather than a missing protocol.
- [Feature] Enable in-call long-press for FreeBuds 5, 5i, 6, 6i, 7i, Neo and SE 4 where the official page provides it.
- [Fix] Read the long-press in-call value from parameter 4 instead of the right-ear value.
- [Fix] Do not expose an in-call long-press option for FreeClip 2 / 2 S; its AI-key page has no such field.
- [Docs] Add the HUAWEI model capability matrix and long-term driver TODO.
- [Device compatibility] Add FreeBuds 6, FreeBuds 7, FreeBuds 7i, FreeBuds Neo, first-gen FreeClip, FreeBuds Pro 4 and FreeClip 2 S / Collector's Edition.
- [Device compatibility] FreeClip 2 S shares FreeClip 2 behavior; FreeBuds Pro 4 and first-gen FreeClip gain read-only head control.
- [Device compatibility] Add a device catalog with capability, feature and official Chinese color data.
- [Device compatibility] Follow the official find-earbud matrix: all models except FreeBuds Pro (1st gen) and FreeBuds Studio.
- [Feature] Add find-earbud with per-ear ringing state, status readback and a safety stop timeout.
- [Feature] Split long-press and swipe actions per ear and align the official action values.
- [Feature] FreeBuds Pro 5 gains the official pinch, tap, long-press, pinch-and-hold and swipe gesture set from the 2.0.7.321 touchsetting config.
- [Feature] FreeClip 2 and FreeClip 2 S gain the official in-call double-tap setting: answer/end the call or disable it.
- [Feature] Add adaptive volume, head control, spatial audio and drop alert.
- [Feature] Rebuild charging-case tone settings so every option saves correctly; the built-in tone no longer streams audio.
- [Feature] Add a three-layer prompt-tone library: bundled catalog, official cloud snapshot and custom tones with migration.
- [Feature] Download missing official tone resources automatically, retrying at most once per six hours.
- [Feature] Add a prompt-tone editor with waveform, two-handle trimming, preview, loudness gain and bilingual naming.
- [Feature] Add ZIP import for shared prompt-tone packages; identical sounds are skipped and id/file-name conflicts are resolved without overwriting local data.
- [Feature] The editor waveform zooms at the cursor with Ctrl+wheel, pans with the wheel and offers a full-track overview.
- [Feature] Add a compact editor toolbar with reset, zoom out, logarithmic slider, zoom in and a zoom readout.
- [Feature] Charging-case tone changes require both earbuds in the case, and the panel refreshes when both enter.
- [Feature] Show wearing state in the battery header; disconnected earbuds no longer show 0%.
- [Feature] Add a "Show welcome screen" button to UI settings; reopening it preloads the saved tray and autostart choices.
- [Feature] Derive case power state from case charging only.
- [Feature] Device info shows the localized model color without automatic row numbers.
- [Change] Editor start/end fields apply on focus loss or Enter; the typed value wins and the other handle is clamped to the device limit.
- [Change] Drop alert now says the other earbud plays a ringtone instead of implying an in-app notification.
- [Change] Tone editor handles snap at the maximum length and carry the other handle; there is no minimum selection.
- [Fix] Hide unsupported battery, ANC, EQ and dual-connect entries when switching devices, and refresh the tray menu every time it opens.
- [Fix] FreeBuds Pro 5 gesture pages no longer show unsupported actions; in-call double-tap and triple-tap now use their official value sets.
- [Fix] Ignore the placeholder tone id reported while the earbuds are outside the charging case and keep the last valid selection.
- [Fix] Load Qt's own translations with Qt's underscore locale names, so standard context-menu actions such as "Copy Link Location" are localized.
- [Fix] Tone editor fields stay in sync after clamping; only the waveform grows with the window while the start/end row fills the width.
- [Fix] Closing the editor or main window stops preview playback and releases the temporary file.
- [Fix] Long tone imports keep the full source; only the final selection is capped.
- [Fix] Fix a false equalizer timeout on FreeClip 2.
- [Fix] Fix Bluetooth port conflicts when reconnecting.
- [Fix] Fix prompt-tone uploads failing on some devices.
- [Fix] Connect/disconnect failures stay in dialogs and no longer terminate the tray app.
- [Fix] "Leave application" stops the manager in both roles and exits the daemon cleanly.
- [Fix] Show a dedicated warning when another Bluetooth app holds the port, once per outage.
- [Fix] Follow the system language on systems that report locale names such as `zh_CN`, so Chinese UI and the first-run welcome screen no longer start in English.
- [i18n] Update English, Simplified Chinese, German, Spanish, Brazilian Portuguese, Russian and Turkish strings.

# 0.18.1
- [Device compatibility] Initial Freebuds 3 support (thx @qiushixiang)
- [Feature] Configurable per-earbud and case battery tray indicators (thx @sinanakyazici)
- [Fix] Crash for unknown ANC level option
- [Platform] Initial macOS packaing config and UX enhancements (not ready for production)

# 0.18.0
- [Platform] Initial macOS compatibility (thx @IAL32)
- [Device compatibility] HUAWEI FreeBuds Pro 5 (thx @JehuAlv)
- [Device compatibility] HUAWEI FreeClip / FreeClip 2 (thx @hereshui3)
- [Feature] Low battery / device connection popup (thx @Ast1va)

# 0.17.3
- [i18n] Add German translation (#87)
- [Fix] Python 3.14 compatibility

# 0.17.1
- [i18n] Add Turkish language (#71)
- [Fix] Libraries list in about tab

# 0.17.0
- [i18n] Add Simplified Chinese translation (#65)
- [Device compatibility] Mark FreeClip as an alias for Pro 3
- [Fix] Copy unsupported equalizer preset dialog failure

# 0.16.2
- [Fix] Windows portable version data location
- This release will be available only as win32 portable version

# 0.16.1
- [Device compatibility] HUAWEI FreeBuds Pro 4 (as alias for Pro 3)
- [Fix] Couple of FreeBuds SE 2 related bugs

# 0.16.0
-  [Device compatibility] HUAWEI FreeBuds SE 2
-  [Feature] Self-repair if config file is broken 
-  [Feature] Automation on device connect
-  [Feature] Add long-tap in-call gesture setting field 
-  [Feature] win32 portable build 
-  [Dep] Add py3.13 to supported 

# 0.15.1
- [Fix] Rework Flatpak autostart management mechanism
- This version would be only released as Flatpak package

# 0.15.0
- [Device compatibility] Add HUAWEI FreeBuds 6i compatibility
- [Device compatibility] Add HUAWEI FreeBuds Studio compatibility
- [Feature] ANC & battery available in main window;
- [Feature] "Show main window" action, available in hotkeys, tray icon click and web-server;
- [Feature] Ability to disable background mode & work without system tray, for Linux environments like GNOME;
- [Fix] Flatpak multi-instance detection & "Run at boot" setting.

# 0.14.1
- [Fix] Crash when using with old devices, like 4i / SE

# 0.14.0
- [Core] Client-server architecture, close #14;
- [Core] Web-server authorization
- [Core] Rewritten (mostly from scratch) to asyncio ;
- [Core] Drop pybluez  from dependencies, now will use predefined port numbers instead of SDP detection;
- [UI] Rewritten from scratch to asyncio  and PyQT6, introduce redesigned Settings UI;
- [UI] Disable logging to CLI / `journalctl` if -v  isn't present, close #29;
- [Device compatibility] Bug fixes for modern HUAWEI Devices (5i, Pro 2, Pro 3);
- [HUAWEI FreeBuds 5i & other] Better Dual-Connect configuration;
- [HUAWEI FreeBuds 5i & other] Add low-latency mode setting;
- [HUAWEI FreeBuds 5i & other] Add triple-tap settings;
- [HUAWEI FreeBuds 5i & other] Fix SQ preference switch;
- [Device compatibility] Add HUAWEI FreeLace Pro 2 compatibility;
- [Linux] Flatpak as installation option
- [i18n] Add Spanish translation, thanks to @Pedro-vk (GitHub)
- [i18n] Add  partial Portuguese (Brazilian), thanks to  @Lobo (Accent)

# 0.13.3
- Fix: Random crash when enumerating dual-connect devices
- Fix: Crash when disabling Bluetooth under windows

# 0.13.2
- Fix: Crash due to unknown equalizer preset

# 0.13.1
- New: HUAWEI FreeBuds Pro 2 support (add profile, partial)
- New: add equalizer presets & device switch to context menu (can be disabled in settings)
- Fix: HUAWEI FreeBuds Pro: remove double-tap, add dual-connect
- Fix: crash when iterating paired devices in 5i, Pro 2, Pro 3
- Fix: disable "Settings" button on non-configurable modules
- Fix: add correct WM_CLASS for better desktop integration (linux)
- Fix: missing i18n

# 0.13.0
- New: HUAWEI FreeBuds 5i support (full)
- New: HUAWEI FreeBuds SE support (full)
- New: HUAWEI FreeBuds Pro support (partial)
- New: HUAWEI FreeBuds Pro 3 support (partial)
- New: Workaround for non-working "Pause when plug off headphone" under Linux (MPRIS-helper)
- New: Advanced bug-report log generator, auto-view bugreport when app crashes
- Fix: Remove WMI-console dependency (win32)
- Fix: Updater crash (win32)
- Minor: Move uncommon features to separate modules
- Minor: Redesign some UI parts

# 0.12.3
- Fix update checker crash

# 0.12.2
- Fix: Crash in Windows 10-11
- Packaging: declare min Python version
- Update dependencies (Pillow, mmk_updater, sv_ttk)
- Begin migration from Launchpad PPA

# 0.12.1
- New: HUAWEI FreeLace Pro support (full)
- New: HUAWEI FreeBuds 5i support (partial)
- New: HUAWEI FreeBuds Pro 2 support (partial)
- Update RU translations
- Disable adapter validation at start
- Minor bugfixes
