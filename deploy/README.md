# Deploying InstantInterviewPrep for free

This folder runs the whole app (agent, accounts, Google sign-in, password-reset email) on one small Linux server:
the app container plus [Caddy](https://caddyserver.com), which serves HTTPS with a free certificate it renews by
itself. The recommended server is Google Cloud's **Always Free e2-micro** VM, with a free
[DuckDNS](https://www.duckdns.org) name as the address.

| Piece | Free allowance |
|---|---|
| Google Cloud e2-micro VM (2 shared vCPUs, 1 GB RAM) | One, all month, in `us-west1`, `us-central1` or `us-east1` |
| Standard persistent disk | 30 GB |
| Outbound traffic | 1 GB a month from North America (beyond that, a small per-GB charge) |
| DuckDNS name (`yourname.duckdns.org`) + Let's Encrypt HTTPS | Free |
| Gmail SMTP for reset emails | About 500 emails a day |

Things that are *not* free: the Anthropic API that powers AI mode is billed per use (leave `ANTHROPIC_API_KEY`
empty to run the free demo mode), and a Google Cloud billing account needs a card. In India it also needs an
identity check (PAN/passport and address proof) and a Visa or Mastercard; RuPay cards are not accepted.

Why this and not a "free web app" platform: the app keeps users and prep kits in a SQLite file, runs the agent in
the background for minutes, and sends email over SMTP. Render's free tier wipes the disk on every restart and
blocks SMTP; Railway allows SMTP only on Pro; Hugging Face Spaces blocks SMTP and has no persistent storage for new
Spaces; Koyeb's free instance can't attach a volume; Fly.io no longer has a free tier.

## 1. Create the server (about 10 minutes)

1. Sign in to [Google Cloud](https://console.cloud.google.com) and create a billing account (the free trial is fine;
   the e2-micro stays free after the trial). Then **Billing → Budgets & alerts → Create budget** for a small amount
   (for example ₹100) with email alerts, so any charge is noticed straight away.
2. **Compute Engine → VM instances → Create instance**:
   - Region: `us-west1`, `us-central1` or `us-east1` (only these are free).
   - Machine configuration: series **E2**, machine type **e2-micro**.
   - OS and storage → Change: **Ubuntu 24.04 LTS** (x86/64), boot disk type **Standard persistent disk**, **30 GB**.
   - Data protection, if offered: **No backups** (snapshots are billed; the app backs itself up daily).
   - Networking → Firewall: tick **Allow HTTP traffic** and **Allow HTTPS traffic**.
   - Create, then note the VM's **External IP**.
3. At [duckdns.org](https://www.duckdns.org), sign in, add a sub domain (for example `instantprep`), paste the VM's
   external IP into *current ip* and click *update ip*. Copy your **token** from the top of the page.

## 2. Install the app (about 15 minutes, mostly waiting)

Open the VM's terminal with the **SSH** button in the VM list, then:

```bash
curl -fsSL https://raw.githubusercontent.com/himanshut2512-web/instant_interview_prep/develop/deploy/setup-server.sh | bash
nano ~/instant_interview_prep/deploy/.env
```

In `.env` set at least `DOMAIN`, `PREP_APP_URL` (`https://` + the same name) and `DUCKDNS_TOKEN`; add the Google
client ID and secret, the Gmail address and app password, and `ANTHROPIC_API_KEY` for AI mode. Save with
`Ctrl+O`, `Enter`, `Ctrl+X`. Then start everything:

```bash
cd ~/instant_interview_prep/deploy
sudo docker compose up -d --build        # first build takes 5-15 minutes on an e2-micro
sudo docker compose logs -f              # wait for "certificate obtained", then Ctrl+C
sudo docker compose exec app python -m app.setup_auth --check
```

The check should show **OK** for Google sign-in and password-reset email. Open `https://yourname.duckdns.org`.

## 3. Point Google sign-in at the server

In Google Cloud → **Google Auth Platform** (the project that holds your OAuth client):

- **Clients** → your web client → **Authorized redirect URIs** → add
  `https://yourname.duckdns.org/api/auth/google/callback` → Save.
- **Branding** → home page `https://yourname.duckdns.org`, privacy policy
  `https://yourname.duckdns.org/privacy.html`, and add `yourname.duckdns.org` under **Authorized domains**.
- **Audience** → **Publish app**, so any Google account can sign in (while it's in *Testing*, only the test users
  listed there can). Sign-in with only `openid`, `email` and `profile` needs no Google review.

Changes can take a few minutes to apply.

## Everyday use

All commands run in `~/instant_interview_prep/deploy` (after you reconnect once, `sudo` isn't needed):

| Task | Command |
|---|---|
| Deploy the latest code from `develop` | `./update.sh` (backs up first) |
| Follow the logs | `docker compose logs -f app` |
| Restart the app | `docker compose restart app` |
| Change settings | edit `.env`, then `docker compose up -d` |
| Back up now | `./backup.sh` (also runs daily at 03:00; the 14 newest are kept in the data volume) |
| Download a backup | `docker compose cp app:/app/data/backups/<file> ~/` then download it from the SSH window's menu |
| Check sign-in settings | `docker compose exec app python -m app.setup_auth --check` |

The app runs as a single process on purpose: the agent works in the background and the sign-in rate limits are
kept in memory, so don't run several copies behind a load balancer.

## Alternative: Oracle Cloud Always Free

The same kit works on an Oracle Cloud Ubuntu VM (an Always Free AMD micro, or the Arm A1 shape, now 2 OCPUs and
12 GB). Differences to know: Oracle's Ubuntu images block ports 80 and 443 in the VM's own firewall as well as in
the VCN security list, so open both; Oracle may reclaim Always Free VMs that stay idle for 7 days unless the
account is upgraded to Pay As You Go (still free within the limits); and sign-up from India often rejects cards.
