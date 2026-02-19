# Newsletter Application User Guide

A complete guide to using the AI-powered newsletter generation platform with human-in-the-loop approval workflow.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Generating a Newsletter (Workflow Mode)](#generating-a-newsletter-workflow-mode)
4. [Manual Mode](#manual-mode)
5. [Managing Campaigns](#managing-campaigns)
6. [Managing Subscribers](#managing-subscribers)
7. [Managing Templates](#managing-templates)
8. [Analytics](#analytics)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Application

1. Open your browser and navigate to the application URL
2. Log in with your credentials
3. From the main dashboard, click **Apps** in the sidebar
4. Select **Newsletter** from the available applications

You'll land on the Newsletter Dashboard, your central hub for all newsletter activities.

---

## Dashboard Overview

The Newsletter Dashboard provides a quick overview of your newsletter platform:

### Stats Cards (Top Row)

| Card | Description |
|------|-------------|
| **Total Newsletters** | Number of newsletters created, with growth rate vs last month |
| **Campaigns Sent** | Campaigns sent this month |
| **Active Subscribers** | Current active subscriber count with new additions |
| **Avg Open Rate** | Average email open rate across campaigns |

### Active Workflows Panel

Shows newsletters currently in progress:
- **Status indicators**: Running (spinner), Awaiting Approval (amber), Completed (green)
- **Current step**: Which stage the workflow is at
- **Last updated**: Time since last activity
- Click any workflow to resume or review it

### Recent Newsletters Panel

Lists your most recent newsletters:
- Newsletter title and creation date
- Status badge (draft, sent, archived)
- Click "View all" to see complete history

### Quick Actions

Four shortcut buttons:
- **Generate Newsletter** - Start a new AI-powered newsletter
- **Create Campaign** - Set up an email campaign
- **Manage Subscribers** - View and edit subscriber list
- **View Analytics** - See performance metrics

---

## Generating a Newsletter (Workflow Mode)

This is the recommended way to create newsletters. The AI handles research and writing while you maintain control through approval checkpoints.

### Step 1: Start Generation

1. Click the **Generate** tab (or "Generate Newsletter" quick action)
2. You'll see the Generation Panel with these options:

#### Topics
- Type a topic (e.g., "Artificial Intelligence") and press Enter or click +
- Add multiple topics to cover different areas
- Remove topics by clicking the X on each tag
- **Tip**: Be specific. "AI in Healthcare" works better than just "AI"

#### Custom Prompt (Optional)
- Toggle "Use custom prompt" if you want to provide specific research instructions
- Example: "Find articles about renewable energy breakthroughs in the last week, focusing on solar and wind innovations"

#### Writing Tone
Select one of four tones:
| Tone | Best For |
|------|----------|
| **Professional** | Business newsletters, B2B communications |
| **Casual** | Community updates, personal newsletters |
| **Formal** | Academic, government, traditional audiences |
| **Enthusiastic** | Product launches, exciting announcements |

#### Max Articles
- Use the slider to set how many articles to include (3-20)
- More articles = longer newsletter but more comprehensive coverage
- Recommended: 5-8 for most newsletters

#### Use RAG Examples
- Keep this ON to let the AI learn from your previous successful newsletters
- Turn OFF only if you want a completely fresh approach

3. Click **Start Generation**

### Step 2: Research Phase (Automatic)

The AI now searches for relevant articles:
- The workflow tracker shows "Research" as the current step
- A spinning indicator shows progress
- This typically takes 30-60 seconds depending on topics

**What happens behind the scenes:**
- AI searches multiple sources using Tavily
- Articles are scored for relevance, quality, and recency
- Results are filtered and ranked

### Step 3: Article Review Checkpoint

Once research completes, you'll see the **Article Review** panel:

#### What You See
- List of discovered articles with:
  - Title and source
  - Relevance score (0-100%)
  - Brief summary
  - Expand button for full details

#### Actions Available

**Select Articles:**
- Check/uncheck articles to include or exclude
- Selected articles will be used to generate the newsletter
- Aim for 5-10 well-matched articles

**Review Details:**
- Click the expand icon on any article to see:
  - Full summary
  - Key takeaways
  - Published date
  - Original source link

**Provide Feedback (Optional):**
- Click "Add feedback" to expand the feedback textarea
- Enter suggestions like "Include more technical articles" or "Focus on practical applications"

#### Making Your Decision

| Button | What It Does |
|--------|--------------|
| **Approve** | Accept selected articles, proceed to content generation |
| **Reject** | Discard results, AI will research again with your feedback |

**Tips:**
- Don't select too many articles - quality over quantity
- Check that articles are recent and from reputable sources
- If results are poor, reject with specific feedback

### Step 4: Content Generation (Automatic)

After approving articles:
- The workflow tracker shows "Generate" as current step
- AI writes the newsletter using selected articles
- This takes 1-2 minutes depending on content length

**What happens:**
- AI synthesizes articles into cohesive newsletter content
- Multiple subject line options are generated
- Content is formatted in HTML, text, and markdown

### Step 5: Content Review Checkpoint

You'll see the **Content Review** panel:

#### Preview Modes
Switch between three formats using the tabs:
- **HTML** - Formatted preview (how it will look in email)
- **Text** - Plain text version
- **Markdown** - Source format

#### Content Stats
- **Word count** - Total words in the newsletter
- **Reading time** - Estimated time to read

#### Edit Mode
1. Click **Edit** to enable editing
2. Modify the content directly in the textarea
3. Your changes are preserved when you approve

#### Actions Available

| Button | What It Does |
|--------|--------------|
| **Approve** | Accept content as-is, proceed to final review |
| **Edit** | Save your modifications and proceed |
| **Reject** | Discard content, AI will rewrite with your feedback |

**Tips:**
- Always read through the content for accuracy
- Check that key points from articles are covered
- Verify tone matches your selection
- Add personal touches or calls-to-action if needed

### Step 6: Final Review Checkpoint

The last checkpoint before sending:

#### Summary View
- **Subject line** - The AI-generated subject
- **Article count** - Number of source articles
- **Word count** - Newsletter length
- **Recipient count** - How many subscribers will receive it

#### Full Preview
- See the complete newsletter as recipients will see it
- Scroll through to verify formatting

#### Schedule Options
- **Send Now** - Immediately queue for sending
- **Schedule** - Pick a specific date and time
  - Click the calendar icon to select date
  - Choose optimal send time for your audience

#### Actions Available

| Button | What It Does |
|--------|--------------|
| **Approve & Send** | Finalize and send (or schedule) the newsletter |
| **Reject** | Go back to make changes |

### Step 7: Completion

After final approval:
- Newsletter is queued for sending (or scheduled)
- You're redirected to the Dashboard
- A success notification confirms completion
- The newsletter appears in "Recent Newsletters"

---

## Manual Mode

For users who prefer step-by-step control without the automated workflow.

### Accessing Manual Mode

1. Go to the Newsletter app
2. Click the **Manual Mode** tab

### Research Panel

1. **Enter Topics** - Add topics you want to research
2. **Custom Prompt** (Optional) - Write specific research instructions
3. **Max Results** - Set how many articles to find (5-20)
4. **Include Summaries** - Toggle to get AI-generated summaries
5. Click **Research**

### Review Results

Articles appear in the results panel:
- Click checkboxes to select articles
- Use "Select All" or "Clear Selection" buttons
- Review article details before selecting

### Writing Panel

Once articles are selected:
1. **Selected Articles** - Shows count of chosen articles
2. **Tone Selection** - Pick your writing style
3. Click **Generate Newsletter**

### Preview

After generation:
- Review the generated content
- Click **Regenerate** if you want a different version
- Copy content or proceed to create a campaign

---

## Managing Campaigns

Navigate to **Campaigns** from the dashboard or sidebar.

### Campaign List

- **Search** - Find campaigns by name or subject
- **Filter** - Filter by status (Draft, Scheduled, Sending, Sent, Failed)
- **Pagination** - Navigate through campaign history

### Campaign Statuses

| Status | Meaning |
|--------|---------|
| **Draft** | Created but not sent |
| **Scheduled** | Queued for future sending |
| **Sending** | Currently being delivered |
| **Sent** | Successfully delivered |
| **Failed** | Delivery encountered errors |

### Creating a Campaign

1. Click **New Campaign**
2. Enter campaign details:
   - **Name** - Internal name for tracking
   - **Subject** - Email subject line
   - **Newsletter** - Select content to send
   - **Template** - Choose email template
3. Preview and send or schedule

### Campaign Details

Click any campaign to view:
- **Stats** - Sent, opened, clicked, bounced counts
- **Open/Click Rates** - Engagement percentages
- **Preview** - See the email content
- **Activity Log** - Timeline of events

---

## Managing Subscribers

Navigate to **Subscribers** from the dashboard or sidebar.

### Subscriber List

- **Search** - Find by email or name
- **Filter** - Filter by status (Active, Unsubscribed, Bounced)
- **Multi-select** - Check multiple subscribers for bulk actions

### Adding Subscribers

#### Single Subscriber
1. Click **Add Subscriber**
2. Enter email address
3. Optionally add name
4. Click **Add**

#### Bulk Import
1. Click **Import CSV**
2. Upload a CSV file with columns: email, name (optional)
3. Review import results
4. Confirm import

### Subscriber Statuses

| Status | Meaning |
|--------|---------|
| **Active** | Receiving emails |
| **Unsubscribed** | Opted out |
| **Bounced** | Email address invalid |
| **Pending** | Awaiting confirmation |

### Bulk Actions

1. Select multiple subscribers using checkboxes
2. Available actions:
   - **Delete** - Remove selected subscribers
   - **Export** - Download as CSV

---

## Managing Templates

Navigate to **Templates** from the dashboard or sidebar.

### Template Gallery

Templates are displayed as cards showing:
- Preview thumbnail
- Template name
- Category
- Last updated date
- Default badge (if applicable)

### Template Categories

| Category | Use Case |
|----------|----------|
| **Newsletter** | Regular newsletter content |
| **Promotional** | Sales and marketing emails |
| **Announcement** | Important updates |
| **Digest** | Curated content roundups |

### Using Templates

1. Browse templates or use search/filter
2. Click **Use Template** on the desired template
3. Template is applied to your campaign

### Template Actions

- **Preview** - See full template
- **Edit** - Modify template content
- **Duplicate** - Create a copy
- **Set as Default** - Use for new campaigns
- **Delete** - Remove template

---

## Analytics

Navigate to **Analytics** from the dashboard or sidebar.

### Overview Tab

- **Key Metrics** - Newsletters, campaigns, subscribers, rates
- **Campaign Performance** - Open/click trends over time
- **Top Campaigns** - Best performing by open rate

### Engagement Tab

- **Open Rate Trend** - How open rates change over time
- **Click Rate Trend** - Link click patterns
- **Best Days** - Which days get highest engagement

### Subscribers Tab

- **Growth Chart** - Subscriber count over time
- **Status Breakdown** - Active vs unsubscribed vs bounced
- **Acquisition Sources** - Where subscribers come from

### Time Period Selection

Use the dropdown to change the analysis period:
- Last 7 days
- Last 30 days
- Last 90 days
- This year

---

## Troubleshooting

### Workflow Issues

**"Workflow stuck on Research"**
- Check your internet connection
- Verify API keys are configured
- Try with different/simpler topics

**"No articles found"**
- Topics may be too specific or niche
- Try broader topic terms
- Check if topics are spelled correctly

**"Content generation failed"**
- Selected articles may have issues
- Try selecting different articles
- Reduce number of selected articles

### Campaign Issues

**"Campaign failed to send"**
- Check subscriber list for invalid emails
- Verify email service configuration
- Check sending limits

**"Low open rates"**
- Review subject line effectiveness
- Check send time optimization
- Verify emails aren't going to spam

### General Tips

1. **Start small** - Test with a few topics before complex newsletters
2. **Use feedback** - When rejecting, always provide specific feedback
3. **Save drafts** - The system auto-saves, but export important content
4. **Check previews** - Always preview before final approval
5. **Monitor analytics** - Track what works and adjust

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Add topic (when in topic input) |
| `Escape` | Close dialogs/modals |
| `Tab` | Navigate between form fields |

---

## Getting Help

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review error messages for specific guidance
3. Contact support with:
   - Steps to reproduce the issue
   - Any error messages shown
   - Browser and device information
