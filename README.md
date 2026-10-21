# Free Games Notifier

Get notified whenever a game becomes free on a platform.

> [!NOTE]
> Currently only supports Epic Games Store.

<img src="https://github.com/user-attachments/assets/8a179053-c685-40a6-8d27-64c059dcfdbb" width="280px">

# Usage

## Hands-Free 
The project's scheduled GitHub Action automatically broadcasts free game notifications to a [ntfy.sh] public topic.

To start receiving notifications, install the [ntfy][ntfy.sh] app from the Play Store or App Store and subscribe to the following topic:
```
free-games-public-yo69xlrfm
```

> [!IMPORTANT]
> Since this uses a public `ntfy` topic, anyone can send messages to it. However, I kindly ask that no one spams the topic to keep it useful for everyone who relies on it.

## Manual

The program supports sending notifications through various services provided by [caronc/apprise](https://github.com/caronc/apprise).

You can run the program either locally, scheduling it with a cron job, or by forking the project and using the existing GitHub Action workflow.

### Required Setup
To configure notifications, specify the services using [Apprise Service URI](https://github.com/caronc/apprise?tab=readme-ov-file#productivity-based-notifications).

This can be done in two ways:
1. Using `settings.toml`:
```toml
apprise_urls = [ "ntfy://my_secret_topic" ]
```

2. Using the `FGN_APPRISE_URLS` environment variable: 
```bash
FGN_APPRISE_URLS='[ "ntfy://my_secret_topic" ]'
```

#### Native Android Notifications (Termux):

> [!NOTE]
> For Android notifications, install the [Termux:API] and run `pkg install termux-api` inside [Termux]. Tapping the notification automatically opens the game's page in your default browser.

1. Use termux as notifier in `settings.toml`:
```toml
apprise_urls = [ "termux://" ]
```

2. Setup schedular:
```bash
# Check once a day
free-games-notifier schedule -i 1d
```

---

### Related Projects
- [vogler/free-games-claimer](https://github.com/vogler/free-games-claimer)
- [claabs/epicgames-freegames-node](https://github.com/claabs/epicgames-freegames-node)
- [moonstar-x/discord-free-games-notifier](https://github.com/moonstar-x/discord-free-games-notifier)
- [sh13y/epic-free-games-notifier](https://github.com/sh13y/epic-free-games-notifier)

[ntfy.sh]: <https://ntfy.sh/>
[termux]: https://github.com/termux/termux-app
[termux:api]: https://github.com/termux/termux-api