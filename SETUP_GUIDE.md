# Consultant Rota Sync — Complete Beginner's Setup Guide

This guide walks you through setting up an automatic sync between the **RITA consultant rota spreadsheet** and your **Google Calendar**. Once set up, your shifts will appear in your calendar automatically and update every day — you never have to touch it again.

**No programming knowledge required.** This guide assumes you have never used GitHub before.

---

## What you'll end up with

- Your planned shifts appear as **orange** (Service), **red** (On Call), or **yellow** (CoMET) all-day events in your Google Calendar.
- Locum shifts appear with "(Locum)" in the title.
- The calendar updates itself once a day, automatically, forever.
- If a shift is removed or changed in the rota, your calendar updates to match.

---

## What you'll need before starting

1. **About 20 minutes** (once, first-time setup only).
2. **A computer** with a web browser. Phone works in a pinch but the GitHub interface is easier on a larger screen.
3. **Your Google account email** — the one your calendar lives on.
4. **Two files from Alex** (message him to get these):
   - A **service account JSON key file** (a small text file containing credentials)
   - The **email address of that service account** (looks like `something@something.iam.gserviceaccount.com`)

> **Why do you need these from Alex?** The rota spreadsheet and all the underlying Google Cloud plumbing is already set up on Alex's account. Rather than every colleague setting up their own Google Cloud project (which takes about an hour), you'll use Alex's. He just needs to send you two things.

---

## Step 1 — Get your details from Alex

Message Alex and ask for:

1. The **service account credentials JSON file**. This is a small text file — he can send it via WhatsApp, email, or any secure method. It will contain a block of text that starts with `{` and ends with `}`, with lots of lines in between including `"private_key"` and `"client_email"`.
2. The **service account email address**. This is also in the JSON file as the `client_email` field, but easier if he just tells you directly. It looks something like `rota-scraper@consultant-rota-sync.iam.gserviceaccount.com`.

**Save the JSON file somewhere you can find it** — Desktop is fine for now. You'll need to open it and copy its contents in Step 4.

---

## Step 2 — Create a GitHub account

GitHub is a website that hosts code. We're going to use it to host this rota sync script and, more importantly, run it for you automatically every day — on GitHub's servers, not your computer. This means it works even when your laptop is closed.

1. Open your browser and go to **https://github.com/signup**
2. Enter your email address (any email — doesn't need to match your Google account).
3. Create a password (save it somewhere).
4. Pick a username. This will be part of your public profile. Something simple like `firstname-lastname` is fine.
5. Solve the verification puzzle.
6. Check your email for a verification code and enter it.
7. You'll be asked about your plan — **the free plan is fine**. Skip/dismiss any onboarding questions.

You should now be on the GitHub homepage, logged in. Leave this tab open.

---

## Step 3 — Get your own copy of the rota sync repo ("forking")

A "repo" (short for repository) is just a folder of code on GitHub. You're going to make your own copy of Alex's repo so you can run it with your own details.

1. In the same browser, go to: **https://github.com/dewar14/consultant-rota-scraper**
2. In the **top-right** of that page, you'll see three buttons: **Watch**, **Fork**, **Star**. Click **Fork**.
3. A page appears titled "Create a new fork". Most of the defaults are correct:
   - **Owner**: your GitHub username (already selected)
   - **Repository name**: `consultant-rota-scraper` (already filled in — leave it as is)
   - **Copy the main branch only**: leave this **ticked**
4. Click the green **Create fork** button.
5. Wait a few seconds. You'll be redirected to **your own copy** of the repo. You can tell because the URL now starts with your username instead of `dewar14`.

You now have your own personal copy of the rota sync code. Any changes you make (like adding your calendar details) only affect your copy.

---

## Step 4 — Add your secrets

"Secrets" are just private settings that your copy of the code can use but nobody else can see. You need to add three of them.

### Getting to the secrets page

1. On your forked repo page, look at the row of tabs near the top: **Code**, **Issues**, **Pull requests**, **Actions**, **Projects**, **Wiki**, **Security**, **Insights**, **Settings**.
2. Click **Settings** (it's on the far right, might be hidden behind a "..." button on a narrow screen).
3. On the settings page, look at the left-hand menu. Scroll down to **Secrets and variables** and click to expand it.
4. Click **Actions** underneath it.
5. You're now on the "Actions secrets and variables" page. You'll see a green button: **New repository secret**.

Now add each of the three secrets below — one at a time. For each one, click **New repository secret**, fill in the Name and Secret fields, then click **Add secret**.

### Secret 1: `GOOGLE_CREDENTIALS_JSON`

- **Name** (type this exactly, including capitals and underscores): `GOOGLE_CREDENTIALS_JSON`
- **Secret**: Open the JSON file Alex sent you in a text editor (on Mac: right-click → Open With → TextEdit; on Windows: right-click → Open With → Notepad). Select **all** of the text (Cmd+A / Ctrl+A), copy it (Cmd+C / Ctrl+C), and paste it into the Secret box. It should start with `{` and end with `}`.
- Click **Add secret**.

### Secret 2: `CALENDAR_ID`

- Click **New repository secret** again.
- **Name**: `CALENDAR_ID`
- **Secret**: Your Google email address — the full email that owns the calendar you want your shifts to appear on. For example `jane.smith@gmail.com` or `j.smith@nhs.net`. Just the email, nothing else.
- Click **Add secret**.

### Secret 3: `MY_NAME`

- Click **New repository secret** again.
- **Name**: `MY_NAME`
- **Secret**: Your **first name, exactly as it appears in the RITA spreadsheet**. Capital first letter matters. If the spreadsheet says "Charlotte", put `Charlotte`. If it says "Craig", put `Craig`. **Do not use your surname** — the rota uses first names only.
- Click **Add secret**.

After all three, your Secrets page should list: `CALENDAR_ID`, `GOOGLE_CREDENTIALS_JSON`, `MY_NAME` (alphabetically). The values are hidden — that's normal.

---

## Step 5 — Share your Google Calendar with the service account

This is the step people most often forget. Your calendar needs to explicitly let the service account write events to it, otherwise nothing will happen.

1. Open **https://calendar.google.com** in a new tab, signed in to the Google account whose email you used as `CALENDAR_ID` above.
2. On the **left-hand side** of Google Calendar, you'll see a section called **My calendars**. Find your main calendar — it'll have your name on it (e.g. "Jane Smith").
3. Hover over your calendar name. Three dots (⋮) appear to the right of it. Click the three dots.
4. A menu pops up. Click **Settings and sharing**.
5. A new page opens. Scroll down until you see a section called **Share with specific people or groups**.
6. Click **Add people and groups**.
7. In the box that appears, paste the **service account email** Alex gave you (the one ending in `.iam.gserviceaccount.com`).
8. Below the email field, there's a dropdown labelled **Permissions**. Change it to **Make changes to events**.
9. Click **Send**.
10. You may see a warning saying "this invitation is being sent outside your organisation". That's fine — click **Invite** / **Send** / **Continue** to confirm.

The service account is now allowed to write to your calendar. (It won't receive or need to accept an invitation — service accounts just have permission automatically.)

---

## Step 6 — Enable GitHub Actions on your fork

GitHub disables automatic workflows on newly-forked repos as a safety measure. You need to enable them.

1. Go back to the tab with your forked repo on GitHub.
2. Click the **Actions** tab at the top.
3. You'll see a yellow banner that says something like: **"Workflows aren't being run on this forked repository"**. Underneath it there's a green button: **I understand my workflows, go ahead and enable them**.
4. Click that button.

---

## Step 7 — Run the sync for the first time (manual test)

Let's test it before waiting for the automatic daily schedule.

1. You should still be on the **Actions** tab.
2. On the **left-hand side**, you'll see a list of workflows. Click **Daily Rota Sync**.
3. On the right, you'll see a message: **"This workflow has a workflow_dispatch event trigger."** and a grey button: **Run workflow**. Click it.
4. A small dropdown appears:
   - **Use workflow from**: leave as **main** (the default).
   - Click the green **Run workflow** button.
5. **Wait about 10 seconds**, then refresh the page. You should see a new entry at the top of the list with a yellow/orange spinning circle next to it — that means it's running.
6. Wait another 30–60 seconds and refresh again. The spinning circle should turn into either a **green tick** (success) or a **red cross** (failure).

### If you got a green tick

Open your Google Calendar. Your shifts for the next 16 weeks should now appear as colour-coded all-day events. It may take a minute to sync to mobile devices.

**You're done!** From now on it runs automatically every morning. You can close all the browser tabs and forget about it.

### If you got a red cross

Don't panic — this is almost always one of three things. Click on the failed run to see the details:

1. Click the red cross / failed run at the top of the list.
2. Click the **sync** job in the middle of the page.
3. Expand the step that failed (it'll have a red cross next to it) and scroll to find the error message near the bottom.

See the **Troubleshooting** section at the end of this guide.

---

## Step 8 — Check the automatic schedule is set up

The workflow runs every day at **07:00 UTC** (that's 08:00 UK in winter, 08:00 UK during BST — sorry, GitHub cron runs in UTC). You don't need to do anything to enable this; as long as Step 6 enabled workflows, the schedule is already active.

> **Note:** GitHub sometimes disables scheduled workflows on forked repos after 60 days of inactivity on the fork. If you notice your calendar has stopped updating after a couple of months, go back to the Actions tab and click **Run workflow** once manually — this resets the timer.

---

## Troubleshooting

### "HttpError 404 ... Not Found" on the sync step

This means the calendar ID is wrong or the calendar hasn't been shared with the service account.

- Check your `CALENDAR_ID` secret — it should be your full Google email address, no extra spaces, no angle brackets.
- Re-do Step 5. Specifically, make sure the permission dropdown said **Make changes to events**, not "See only free/busy" or "See all event details".

### "HttpError 403 ... insufficient permissions"

Same fix as 404: go back to Step 5 and verify the service account is added to your calendar with **Make changes to events**.

### "JSONDecodeError: Expecting value" or credentials errors

The `GOOGLE_CREDENTIALS_JSON` secret wasn't pasted correctly.

- Go back to Settings → Secrets and variables → Actions.
- Delete the `GOOGLE_CREDENTIALS_JSON` secret and add it again.
- When pasting, make absolutely sure you select **everything** in the JSON file from the opening `{` to the closing `}`, including all the quotes and newlines in between.

### "Found 0 shifts in date range"

The script is running correctly but can't find your name in the rota.

- Check your `MY_NAME` secret. It should be exactly what's in the spreadsheet: capital first letter, correct spelling. If the rota says "Catarina", don't put "Catherine" or "Cat".
- Also check the rota itself — if you've got no shifts in the next 16 weeks (lucky you), there's genuinely nothing to sync and the script will log this.

### The workflow runs successfully but my calendar is empty

- Are you checking the **correct** calendar? If you have multiple Google accounts, make sure you're logged into the one whose email you used as `CALENDAR_ID`.
- Click the three dots next to your calendar in Google Calendar → Settings and sharing → scroll down to "Share with specific people or groups" — the service account email should be listed there with "Make changes to events". If not, redo Step 5.

### My shifts are wrong / missing / duplicated

- Re-run the workflow manually from the Actions tab. The script is self-correcting — running it again will fix any drift.
- If a specific shift is still wrong after a re-run, check the logs. Click the latest run → **sync** job → expand **Run rota sync**. Near the bottom you'll see lines like `Found 'YourName' in service col, RGB=(...)`. If your shift isn't in that list, the script didn't detect it — message Alex with your name, the date of the missing shift, and a screenshot of that part of the rota.

### It stopped working after a few weeks

GitHub disables scheduled workflows on forks that haven't had activity. Go to Actions → Daily Rota Sync → Run workflow → Run workflow (green button). This reactivates the schedule for another 60 days.

---

## How to know it's working

- Events will appear on your calendar coloured by shift type:
  - **Orange** → Service
  - **Red** → On Call
  - **Yellow** → CoMET
- Every event has a description that reads **"Scraped from RITA rota"**. You can click any event to see this — it's how you can tell an event was created by this sync rather than manually.
- **Do not manually delete** events created by the sync — the sync will put them back on the next run. If a shift is wrong, fix it in the RITA spreadsheet and the sync will correct the calendar automatically.
- **You can add your own manual events** to your calendar on rota days — the sync only touches its own events (the ones with the "Scraped from RITA rota" description). Your personal events are left alone.

---

## Changing settings later

If you need to change your email, your name in the rota, or the credentials:

1. Go to your forked repo → **Settings** → **Secrets and variables** → **Actions**.
2. Find the secret you want to change and click the **pencil icon** next to it.
3. Enter the new value and click **Update secret**.
4. Go to **Actions** → **Daily Rota Sync** → **Run workflow** to apply the change immediately.

---

## Questions?

Message Alex. Include:
- A screenshot of what you're seeing.
- A link to your forked repo (or at least your GitHub username).
- The step number you're stuck on.
