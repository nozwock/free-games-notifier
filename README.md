# Free Games Notifier

Get notified whenever a game becomes free on a platform.

> [!NOTE]
> Currently only supports Epic Games Store.

<img src="https://github.com/user-attachments/assets/8a179053-c685-40a6-8d27-64c059dcfdbb" width="280px">

## Usage

### Hands-Free
The project's scheduled GitHub Action automatically broadcasts free game notifications to a [ntfy.sh] public topic.

To start receiving notifications, install the [ntfy][ntfy.sh] app from the Play Store or App Store and subscribe to the following topic:
```
free-games-public-yo69xlrfm
```

> [!IMPORTANT]
> Since this uses a public `ntfy` topic, anyone can send messages to it. However, I kindly ask that no one spams the topic to keep it useful for everyone who relies on it.

### Manual

The program supports sending notifications through various services provided by [caronc/apprise](https://github.com/caronc/apprise).

You can run the program either locally, scheduling it with a cron job, or by forking the project and using the existing GitHub Action workflow.

#### Installation

You can install the package using [uv] (recommended), or alternatives like `pipx`:

```bash
uv tool install git+https://github.com/nozwock/free-games-notifier
```

#### Configuration
To configure notifications, specify the services using [Apprise Service URI](https://github.com/caronc/apprise?tab=readme-ov-file#productivity-based-notifications).

This can be done in two ways:
1. Using `settings.toml` (in `~/.config/free-games-notifier/` or the current working directory):
```toml
apprise_urls = [ "ntfy://my_secret_topic" ]
```

2. Using the `FGN_APPRISE_URLS` environment variable: 
```bash
FGN_APPRISE_URLS='[ "ntfy://my_secret_topic" ]'
```

#### Scheduling

You can schedule periodic checks by editing your crontab with `crontab -e`:

```cron
# Check once a day (e.g. at 18:00)
0 18 * * * free-games-notifier
```

---

### Local Android Notifications (Termux)

> [!IMPORTANT]
> **Prerequisites**:
> 1. Install the **[Termux:API]** app and then the following package in [Termux]:
>    ```bash
>    pkg install termux-api
>    ```
> 2. Grant **"Display over other apps"** to **Termux** in Settings.
>    Required on Android 10+ so background notifications clicks can open URLs in browser ([details](https://github.com/termux/termux-tasker#draw-over-apps-permission-optional)).

<!-- https://github.com/pydantic/pydantic-core/issues/1012#issuecomment-2511269688 -->
1. Install the package in Termux:
```bash
uv tool install \
    --extra-index-url https://termux-user-repository.github.io/pypi/ \
    git+https://github.com/nozwock/free-games-notifier
```

2. Use termux as notifier in `~/.config/free-games-notifier/settings.toml`:
```toml
apprise_urls = [ "termux://" ]
```

3. Setup scheduler (e.g. to check once a day):
```bash
free-games-notifier schedule add -i 1d
```

## Related Projects
- [vogler/free-games-claimer](https://github.com/vogler/free-games-claimer)
- [claabs/epicgames-freegames-node](https://github.com/claabs/epicgames-freegames-node)
- [moonstar-x/discord-free-games-notifier](https://github.com/moonstar-x/discord-free-games-notifier)
- [sh13y/epic-free-games-notifier](https://github.com/sh13y/epic-free-games-notifier)

[uv]: https://github.com/astral-sh/uv
[ntfy.sh]: <https://ntfy.sh/>
[termux]: https://github.com/termux/termux-app
[termux:api]: https://github.com/termux/termux-api