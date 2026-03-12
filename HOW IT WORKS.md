# 📡 How the Network Works

Musubi isn't magic — here's what's actually happening inside your server when a call connects.

---

## The Booth Channel

When you run `/setup`, you designate a single channel as your **booth**. This is the only channel Musubi listens to and relays from. Messages anywhere else in your server are completely ignored. Think of the booth as a telephone handset — it's the one place where the call happens.

---

## Placing a Call

When someone runs `/call`, Musubi checks the network for another server that's also waiting. If one is found, the two booths are linked and messages start flowing immediately. If nobody is waiting, your server enters a queue and Musubi searches for up to 30 seconds before giving up with a "no answer."

Under the hood, each call is a single database row shared between both servers. Both sides read from and write to that same row — there's no duplication, no mirroring, just one record that represents the whole call.

---

## Message Relay

Every message sent in your booth during an active call is picked up by Musubi and re-posted in the other server's booth using a **webhook**. This is why messages appear with the sender's name and avatar rather than from the bot account — webhooks let Musubi impersonate the look of each user on the other end.

If a user has anonymous mode on, their name and avatar are replaced with `📞 Anonymous` and the bot's own avatar. Nobody on the other side can tell who sent it.

---

## When a Call Ends

Either server can hang up at any time with `/hangup`. The relay stops immediately — Musubi marks the session as ended in memory before the DB write even completes, so there's no grace period where stray messages sneak through. Both booths receive an "ended" notice and the line goes quiet.

Calls also end automatically after **30 minutes of no messages**, to keep the network clean and free for other servers.

---

## XP

Every message you send during a call earns your server XP. It's not tracked per-user — it's a server-wide score that reflects how active your community is on the network. XP resets at the start of each monthly cycle, with a snapshot saved so past leaderboards aren't lost. Guild Premium doubles your XP rate.

---

## Safety

Before any message is relayed, Musubi runs it through a filter stack:

- Is this user banned from the network?
- Does the message contain a Discord invite link?
- Does it match any phrase on the global blocklist?
- Is it excessively capitalised, flooding the channel, or repeating the same content?

If any check fires, the message is silently dropped — no error, no notification. From the sender's perspective it just didn't go through.

---

## Premium

Premium unlocks things that would otherwise be too heavy for the free network to sustain for everyone — file attachments, stickers, custom nicknames and avatars, and priority matchmaking. It's not pay-to-win; the core call experience is identical for all servers. Premium just adds polish for communities that want it.

---

> For the full technical breakdown — caching strategy, session model, DB write patterns — see the source code and inline comments in `datamanager.py` and `bridge.py`.
