# Intake flow — New to scraping

Run this flow when the user picked **"New to scraping"** at Q1.

## How to run this flow

Send the six questions below **one at a time**. **Send ONE question per message. Wait for the user's reply before sending the next.** Do not bundle.

Each question must:
- Say what is being asked
- Say why you need it
- Show exactly how to find or produce the answer
- Define every technical term inline in plain language

**Assume zero technical vocabulary.** Do not just avoid scraping-specific jargon (HAR, curl, TLS, API) — also avoid the implicit jargon that only makes sense once you know how the web works: *request*, *response*, *server*, *endpoint*, *session*, *token*, *credentials*, *cookie*, *header*, *DOM*, *XHR*. If you need to refer to one of those concepts, paraphrase it ("the small bits of data your browser asks the website for", "your login info").

Tone: friendly and direct, never patronizing. If the user gives a short or ambiguous answer, acknowledge briefly and move on — don't grill them. The point is to gather context, not to test them.

---

## Question 1 — What kind of starting point do you have?

**Preferred: `AskUserQuestion`**:

```
question: "First — what kind of starting link or URL do you have?"
header:   "Starting point"
options:
  - label: "Exact URL of the data page"
    description: "You can open the link and see the data right there."
  - label: "URL of a site, data is inside somewhere"
    description: "Homepage / entry URL; I'll explore the site to find the data page."
  - label: "No URL — just a topic"
    description: "Describe the data; I'll search Google to find candidate sites first."
```

After the user picks, ask for the actual URL/topic in a follow-up message (the option box only captures the *type* of starting point, not the value).

**Fallback (plain text):**

```
First — what kind of starting link or URL do you have? Pick the option that matches your situation:

**(a) I have the exact URL where the data shows up.**
You can open the link in your browser and see the data (a table, a list, search results, etc.) right there on the page.
→ Just paste the URL.

**(b) I have a URL to a site, and the data is somewhere inside it.**
For example: you know an online store publishes a full product catalog, you have the store's website URL, but you don't know which exact page lists every product.
→ Paste whatever URL you have (the homepage is fine). I'll explore the site automatically — pulling the site's own sitemap, trying its search box, following links — to find the page with your data.

**(c) I don't have any URL at all — I just know the kind of data I want.**
For example: "a list of all coffee shops in São Paulo with their addresses" or "every public company in the EU that filed an annual report".
→ Describe the data and what kind of site should have it. I'll search Google with a set of advanced operators to find candidate sites first, then come back and we'll pick one to scrape.

How to find a URL (if you need to look one up):
1. Open the site in your normal browser (Chrome, Firefox, Safari — whatever you use)
2. Navigate / search / filter until you're on a page that's at least *near* the data you want
3. Look at the address bar at the top of the browser window — that's the URL. Copy it and paste it here.

Whichever option you pick, just tell me the letter (a / b / c) and paste/describe what you have.
```

If the user picks **(b)**, after Q1-Q6 are answered, work from `../discovery/link-graph-traversal.md` to locate the data page within the site.
If the user picks **(c)**, before continuing to Q2, work from `../discovery/google-deep-research.md` Phase 1–4 to surface candidate sites, then come back and resume the intake with the chosen site URL.

---

## Question 2 — What data

```
What **specifically** do you want extracted from that page?

Be concrete. Examples:
- "The table with country names and their scores"
- "All product titles and prices on the page"
- "Every comment on the post, with author name and date"

If a screenshot would be easier than describing it, just drag a screenshot into the chat.
```

---

## Question 3 — How much data

```
Roughly **how much data** do you need? This affects whether we write a quick script or design something more careful.

Rough examples:
- "Just what's on this one page" → tiny
- "Everything across maybe 50 pages of results" → small
- "Every record on the whole site — could be millions" → big, needs more planning

A best guess is fine. We'll learn the real number once we look at the site together.
```

---

## Question 4 — Looking behind the scenes (the most important one)

**Preferred: `AskUserQuestion`** to pick the input type, then follow up with the actual paste/upload/walkthrough based on the choice:

```
question: "I need to see how your browser talks to the site. Pick the option that matches what you have:"
header:   "Input type"
options:
  - label: "I have a curl command — I'll paste it"
    description: "A single line of text copied from DevTools earlier. Good for one-endpoint scrapes."
  - label: "I have a HAR file — I'll drop it"
    description: "A recording of every request on a page. Captures cookies and logins automatically."
  - label: "Walk me through capturing a HAR"
    description: "Step-by-step instructions to record your browser. Takes ~1 minute."
  - label: "You try first — no input from me"
    description: "I'll attempt to find the data on my own. If I get stuck I'll come back asking for a HAR."
```

After the user picks:
- **"Paste curl"** → reply "Great — paste the curl command here when you're ready."
- **"Drop HAR"** → reply "Great — drag the .har file into the chat when you're ready."
- **"Walk me through"** → send the full HAR-capture walkthrough below.
- **"You try first"** → say "Got it, I'll attempt autonomous discovery and come back if I'm stuck." and proceed.

**Fallback (plain text — when `AskUserQuestion` is unavailable):** send the whole long message below in one go.

```
Next I need to peek behind the scenes of the page, to find where the data is actually hiding.

**What's going on:** when you visit a website, your browser is doing a lot of work behind the scenes — it asks the site's computer for many small pieces (the text, images, lists, prices, etc.) and assembles them into what you see on screen. I need to see that conversation between your browser and the site to know where to grab your data from.

The easiest way: capture a recording of the page loading, in a file called a **"HAR file"**. It sounds technical but it's just a few clicks. Here's how:

1. Open the target site in **Google Chrome** specifically (this works differently in Safari).
2. Press **F12** on Windows or **⌘⌥I** on Mac — a panel pops open at the side or bottom of the window. That panel is called "developer tools".
3. Click the tab labeled **"Network"** at the top of that panel.
4. Tick the small checkbox labeled **"Preserve log"** (this stops it from wiping itself when you click around).
5. **Reload the page** (Ctrl+R / ⌘R). The Network panel fills up with a long list of items — that's the recording we're making.
6. **Do the actions** that make the data appear on screen — apply filters, click "Search", scroll, whatever it takes to see the data you described in question 2.
7. In the Network panel's toolbar (right at the top of that panel), find a small **download icon shaped like an arrow pointing down** (↓). Click it. A menu pops up showing **"Export HAR (sanitized)..."** — click that.
8. A file ending in `.har` is saved to your Downloads folder. **Drag it from Downloads into this chat.**

Don't worry about understanding what's inside the file — I'll handle that. Just send it.

---

**Already have something more technical?** Two power-user options, only if you know what they are. If these words mean nothing to you, just follow the steps above — that's the normal path.

- **(a) A curl command** (a single line of text you copied from somewhere earlier) → paste it here.
- **(b) A HAR file from a previous attempt** → drag it in.

---

**Or let me try first.** If capturing a HAR feels like too much right now, you can say **"you try first"** and I'll attempt to find the data on my own. If I get stuck I'll come back and ask for the HAR.
```

---

## Question 5 — Login

**Preferred: `AskUserQuestion`**:

```
question: "Is the page behind a login? Meaning: do you need a username/password to see the data?"
header:   "Login required?"
options:
  - label: "No — anyone can view it"
    description: "Public page; no login required."
  - label: "Yes — login required"
    description: "I'll need a way to log in. Capture the HAR while you're logged in, or share credentials."
  - label: "I'm not sure"
    description: "Open the URL in a private/incognito window. If the data is visible without logging in, it's public."
```

**Fallback (plain text):**

```
Is the page **behind a login**? Meaning: do you need a username and password to see the data, or can anyone view it just by visiting the URL?

If you do need to log in:
- Either share your username and password with me (I'll keep them safe and only use them for this task), OR
- **Better and safer**: log into the site yourself, then capture the HAR (the steps from question 4) *while you're still logged in*. Your login info travels inside the file automatically, so I never need to see your password directly.

Not sure if a login is needed? Try this: open the URL in a **private / incognito window** (right-click your browser's icon or use the File → New Private/Incognito Window menu). If you can see the data without being asked to log in, no login is needed.
```

---

## Question 6 — Output format

**Preferred: `AskUserQuestion`**:

```
question: "Where should the extracted data go?"
header:   "Output format"
options:
  - label: "CSV (Recommended)"
    description: "Spreadsheet file you can open in Excel or Google Sheets. Safest default."
  - label: "Excel (.xlsx)"
    description: "Same idea, native Excel format."
  - label: "JSON"
    description: "Structured text file. Useful if another program will read it later."
  - label: "Database"
    description: "Only pick this if you already have a database set up and know you want rows inserted there."
```

**Fallback (plain text):**

```
Where should the extracted data go?

Common options:
- **CSV** — a spreadsheet file you can open in Excel or Google Sheets. Safe default for most cases.
- **Excel (.xlsx)** — same idea, native Excel format.
- **JSON** — a text file with the data in a structured format. Useful if another program will read it later.
- **Database** — only pick this if you already have a database set up and know you want the rows inserted there.

If you don't have a preference, **CSV is the safest default**.
```

---

When all six are answered, summarize what you learned back to the user in 3–4 plain-language lines before starting any code, so they can confirm or correct. Avoid the jargon the user just managed to dodge — keep the summary in the same plain register the questions used.

---

## Final delivery — bronze only, do not offer silver/gold

For this user level, deliver **the raw extracted data** (bronze) in the format they picked at Q6 and **stop**. Do not ask whether they want the data cleaned, typed, deduplicated, or analyzed. Do not propose a "silver" layer, normalization, or aggregations. Do not mention the words "bronze", "silver", "gold", or "medallion" — they're jargon at this level.

If the user later asks for clean-up, typing, or analysis on their own initiative, then proceed and explain plainly what you're doing. Never proactively expand scope beyond what they asked for.

See `../reference/medallion-architecture.md` for the contract details (Claude-facing — not user-facing at this level).
