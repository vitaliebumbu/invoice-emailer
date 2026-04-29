# Invoice Emailer

Adds an **Invoice Request** button inside an Acadia project. When clicked, it finds the proposal PDF in Dropbox and opens a ready-to-review Outlook email draft.

## Simple Install For Team Members

Use these steps if you are not technical.

### What You Need First

- Google Chrome
- Outlook desktop app
- Dropbox synced on your computer
- Access to Acadia

### Step 1: Download

Open this GitHub repo and click **Code** > **Download ZIP**:

[https://github.com/vitaliebumbu/invoice-emailer](https://github.com/vitaliebumbu/invoice-emailer)

Unzip the downloaded file. Put the folder somewhere easy, like **Documents**.

### Step 2: Install

Double-click:

```text
install.bat
```

Wait until it says **Setup complete**.

If Windows shows a warning, only continue if this folder came from the company GitHub repo.

### Step 3: Check Settings

Open the file named:

```text
.env
```

Confirm these lines look right:

```text
JOBS_ROOT=C:\Acadia Craft Dropbox\1 AC Jobs
JOB_SEARCH_FOLDERS=2 IN PRODUCTION;1 Quotes;1 Quotes\_Acadia Inquiry
TO_EMAIL=billing@acadiacraft.com
CC_EMAIL=denis@acadiacraft.com
FROM_NAME=Your Name
```

`JOBS_ROOT` may be different for each person. It should point to the local Dropbox folder that contains `1 Quotes` and `2 IN PRODUCTION`.

Save and close the file.

### Step 4: Start

Double-click:

```text
start-helper.bat
```

Keep that window open while using Acadia.

### Step 5: Add To Chrome

1. Open Chrome.
2. Go to `chrome://extensions`.
3. Turn on **Developer mode**.
4. Click **Load unpacked**.
5. Select the `extension` folder inside this repo.
6. Open or refresh Acadia.

### Step 6: Test

Open a project in Acadia. The **Invoice Request** button should appear in the project panel under **QB:**. Click it, choose the invoice stage, then click **Open draft**.

## Updating Later

When this repo changes, download the ZIP again or pull the latest version. Then:

1. Double-click `install.bat`.
2. Go to `chrome://extensions`.
3. Click the reload icon on **Acadia Invoice Button**.
4. Refresh Acadia.

## Use

Open a project in Acadia and click **Invoice Request**. Choose the invoice stage, then click **Open draft**. The helper searches Dropbox, finds the latest proposal PDF, and opens an Outlook draft with the proposal attached.

The extension reads the project code from the opened project, so you should not need to copy or type the project name.

## Configuration

`.env` supports:

```text
SECRET_KEY=change-me-to-a-random-string
PORT=5055
JOBS_ROOT=C:\Acadia Craft Dropbox\1 AC Jobs
JOB_SEARCH_FOLDERS=2 IN PRODUCTION;1 Quotes;1 Quotes\_Acadia Inquiry
TO_EMAIL=billing@acadiacraft.com
CC_EMAIL=denis@acadiacraft.com
FROM_NAME=Vitalie
```

## Notes

- The draft opens in Outlook; it does not send automatically.
- Production jobs are searched in `2 IN PRODUCTION`; quote-stage jobs are searched in `1 Quotes` and `1 Quotes\_Acadia Inquiry`.
- If Dropbox is synced to another drive, update only `JOBS_ROOT` in `.env`.
- The original Flask pages still work at `http://127.0.0.1:5055/`.
- Invoice draft history is still recorded in `invoices.db`.
- If the button does not appear after updating the extension files, go to `chrome://extensions` and click the reload icon on **Acadia Invoice Button**, then refresh Acadia.

## Why There Are Two Parts

Chrome is not allowed to search local Dropbox folders by itself. The Chrome extension adds the button to Acadia, and `start-helper.bat` runs the local helper that searches Dropbox and opens Outlook.
