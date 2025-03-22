# Free Games Notifier

Get notified whenever a game becomes free on a platform.

> [!NOTE]
> Currently only supports Epic Games Store.

Made this because, while some platforms provide notifications for such events, they often lack granularity.

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

---

### Related Projects
- [vogler/free-games-claimer](https://github.com/vogler/free-games-claimer)
- [claabs/epicgames-freegames-node](https://github.com/claabs/epicgames-freegames-node)
- [moonstar-x/discord-free-games-notifier](https://github.com/moonstar-x/discord-free-games-notifier)
- [sh13y/epic-free-games-notifier](https://github.com/sh13y/epic-free-games-notifier)

[ntfy.sh]: <https://ntfy.sh/>