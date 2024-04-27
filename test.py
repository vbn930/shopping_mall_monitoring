from discord_webhook import DiscordWebhook, DiscordEmbed
import time

webhook = DiscordWebhook(url="https://discord.com/api/webhooks/1233783047523012759/u7-Qh6WMH0jBgI4mSLNZJCXZHGQKDQsOLKnMzBdFFqI__lWPMjPluST501w5_KhCcHjD",
                         content="Test")
webhook.execute()
time.sleep(20)
webhook.delete()

