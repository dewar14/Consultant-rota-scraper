# Consultant Rota Sync – Beginner's Setup Guide

About 20 minutes of one-off setup puts your consultant rota shifts into your own calendar, updated automatically every morning. You do not need to know anything about coding – every step is clicking and copy-pasting in a web browser.

**What you end up with:** all-day events for each of your shifts, colour-coded orange (Service), red (On Call) and yellow (CoMET), with "(Locum)" added for locum shifts. If the rota changes, your calendar follows within a day.

**How it works, in one sentence:** a small program, kept on a free website called GitHub, reads the rota spreadsheet each morning, finds your name and writes your shifts into a Google calendar. If you use Outlook or an iPhone calendar, you then "subscribe" to that Google calendar so the shifts show up there too (Step 6).

---

## Before you start

You will need:

- A computer with a web browser (a phone is possible but fiddly).
- A Google account. A free Gmail address is fine, even if you normally use Outlook – it is only used to hold the rota calendar.
- Two things from Alex: a **key file** (a small text file ending in `.json`) and the **robot email address** that goes with it (it ends in `.iam.gserviceaccount.com`). Message Alex to ask for these, and keep the key file private – treat it like a password.
- Your first name **exactly as it is written in the rota** (for example "Charlotte", not "Charlie").

---

## Steps 1–2: Get your own copy on GitHub

GitHub is a website that stores programs and can run them on a timer for free, so the sync works even when your computer is off. You are going to make your own copy (GitHub calls this a **fork**) of Alex's program.

### Step 1 – Create a free GitHub account

1. Go to **https://github.com/signup**.
2. Enter any email address, choose a password and pick a username (for example `jane-smith`).
3. Complete the puzzle and type in the code GitHub emails you.
4. If asked to choose a plan, choose **Free**. Skip any other questions.

### Step 2 – Make your copy (fork)

1. While logged in, go to **https://github.com/dewar14/consultant-rota-scraper**.
2. Near the top right, click **Fork**.
3. On the "Create a new fork" page, leave everything as it is and click the green **Create fork** button.
4. After a few seconds you land on your copy. Check the web address now starts with `github.com/` followed by **your** username, not `dewar14`. Keep this tab open.

---

## Steps 3–4: Put in your own details

This is where your details replace Alex's. You make a separate "Consultant rota" calendar for the shifts, let Alex's robot write to it, then tell your GitHub copy your name and which calendar to use.

### Step 3 – Make a rota calendar and let the robot write to it

Use a separate calendar rather than your main one. It keeps the shifts apart from your personal events, it means the robot can only ever see the rota, and it is the only safe way to share the shifts with Outlook or an iPhone later.

1. Go to **https://calendar.google.com**, signed in to your Google account.
2. On the left, next to **Other calendars**, click the **+** and choose **Create new calendar**.
3. Name it `Consultant rota` and click **Create calendar**.
4. On the left, under **Settings for my calendars**, click **Consultant rota**.
5. Scroll to **Share with specific people or groups** and click **Add people and groups**.
6. Paste the **robot email address** from Alex (ending `.iam.gserviceaccount.com`).
7. Change **Permissions** to **Make changes to events**, then click **Send**. If warned it is outside your organisation, confirm.
8. Scroll further down to **Integrate calendar** and copy the **Calendar ID**. It is a long jumble ending in `@group.calendar.google.com`. Paste it into a note – you need it in a moment.

### Step 4 – Add your three secrets on GitHub

"Secrets" are private settings that your copy of the program can read but nobody else can see, including Alex.

1. Back in your GitHub tab, click **Settings** (top row of tabs, far right).
2. In the left menu, click **Secrets and variables**, then **Actions**.
3. Click the green **New repository secret** button. Type the **Name** exactly as below (capitals and underscores matter), paste the value into **Secret**, and click **Add secret**. Repeat for all three.

| Name (type exactly) | What to paste in |
| --- | --- |
| `MY_NAME` | Your first name exactly as written in the rota, e.g. `Charlotte` |
| `CALENDAR_ID` | The Calendar ID you copied in Step 3, ending `@group.calendar.google.com` |
| `GOOGLE_CREDENTIALS_JSON` | The whole contents of Alex's key file (see below) |

To copy the key file: right-click it and open it with **Notepad** (Windows) or **TextEdit** (Mac). Select everything (Ctrl+A, or Cmd+A on a Mac), copy, and paste. It should start with `{` and end with `}`.

When finished, the page lists all three names. The values show as hidden – that is normal.

---

## Step 5: Switch it on and run a test

GitHub keeps the timer switched off on new copies as a safety measure, so you switch it on once and run a test straight away.

1. In your GitHub tab, click the **Actions** tab at the top.
2. You will see a message that workflows are not running on this fork. Click the green **I understand my workflows, go ahead and enable them** button.
3. In the left-hand list, click **Daily Rota Sync**.
4. On the right, click **Run workflow**, then the green **Run workflow** button in the small box that appears.
5. Wait about a minute and refresh the page. A new line appears with a spinning circle, which turns into a **green tick** (worked) or a **red cross** (something is wrong – see Troubleshooting).

With a green tick, open Google Calendar and switch on **Consultant rota** in the left-hand list. Your shifts for the next 16 weeks should be there. From now on it runs by itself every morning at about 07:00 in winter and 08:00 in summer (GitHub runs on GMT all year, and can be up to an hour late at busy times).

---

## Step 6: See the shifts in Google, Outlook or iPhone

The shifts always land in your Google "Consultant rota" calendar first. Pick the option below for wherever you actually look at your diary.

### Google Calendar (including Android phones)

Nothing more to do. Make sure **Consultant rota** is ticked in the left-hand list, and on your phone open the Google Calendar app, go to **Settings** and switch the calendar on if it is hidden.

### Outlook, or any other calendar app (the "iCal link")

Outlook cannot read Google calendars directly, but it can follow a private web link to one. This is one-way and read-only: changes flow from the rota into Outlook, and Outlook may take several hours to pick them up.

1. In Google Calendar, open **Settings for my calendars** → **Consultant rota** → **Integrate calendar**.
2. Copy the link labelled **Secret address in iCal format** (it ends in `.ics`). Treat it like a password – anyone with it can see your rota.
3. In Outlook (web or new Outlook), go to the calendar view, click **Add calendar** on the left, then **Subscribe from web**. Paste the link, name it `Consultant rota` and click **Import**. In classic Outlook the same option is under **File** → **Account Settings** → **Internet Calendars** → **New**.

If you use an NHS.net or work account and the subscribe option is missing or refuses the link, your IT department may have blocked internet calendars. Use a personal Outlook or the Google option instead.

### iPhone, iPad or Mac (Apple Calendar)

The simplest route is to add your Google account to the device: on iPhone, **Settings** → **Calendar** (or **Apps** → **Calendar**) → **Calendar Accounts** → **Add Account** → **Google**, sign in, and leave **Calendars** switched on. The rota then updates quickly.

If you would rather not add your Google account, use the iCal link from the Outlook steps instead: **Add Account** → **Other** → **Add Subscribed Calendar** on iPhone, or **File** → **New Calendar Subscription** on a Mac (set **Auto-refresh** to every hour or every day).

Menu names shift between versions. Google's and Microsoft's own instructions are here: [Google – sync your calendar with other programs](https://support.google.com/calendar/answer/37648) and [Microsoft – see your Google Calendar in Outlook](https://support.microsoft.com/office/098ed60c-936b-41fb-83d6-7e3786437330).

---

## Troubleshooting

To see why a run failed, click the red cross in the **Actions** tab, then **sync**, then the step with the red cross, and look near the bottom for the error.

| What you see | Likely cause and fix |
| --- | --- |
| Error mentioning **404** or **403** | The calendar is not shared with the robot, or the Calendar ID is wrong. Redo Step 3 (permission must be **Make changes to events**) and check the `CALENDAR_ID` secret has no extra spaces. |
| Error mentioning **JSON** or credentials | The key file was not pasted in full. Delete the `GOOGLE_CREDENTIALS_JSON` secret and add it again, from the first `{` to the last `}`. |
| Green tick but "Found 0 shifts" | Your `MY_NAME` does not match the rota spelling, or you genuinely have no shifts in the next 16 weeks. |
| Green tick but nothing in your calendar | Check you are looking at the **Consultant rota** calendar and it is ticked. Outlook and iCal subscriptions can lag by several hours. |
| Stopped updating after a couple of months | GitHub pauses timers on copies with no activity for 60 days. Go to **Actions** → **Daily Rota Sync** → **Run workflow** once to restart it. |
| A shift is missing or wrong after a re-run | Message Alex with your name, the date and a screenshot of that part of the rota. |

## Good to know

- Do not edit or delete the rota events by hand – the next run puts them back. Fix the rota instead, and the calendar follows.
- Your own events are never touched. The sync only manages events whose description reads "Scraped from RITA rota".
- To change a detail later (new name, different calendar), go to **Settings** → **Secrets and variables** → **Actions**, click the pencil next to the secret, update it, then run the workflow once from the **Actions** tab.
- Stuck? Message Alex with the step number, a screenshot and your GitHub username.

A printable PDF version of this guide is in [`docs/Rota_Calendar_Setup_Guide.pdf`](docs/Rota_Calendar_Setup_Guide.pdf).
