# CARA Adaptation Workshop Guide: Replit Edition

## Customizing CARA Using Conversational Prompts in Replit

This guide walks non-technical workshop participants through adapting CARA (Comprehensive Automated Risk Assessment) for their jurisdiction using Replit's AI-assisted development environment. Instead of editing code by hand, participants use plain-language prompts to instruct Replit to make changes on their behalf.

No coding experience is required. Each section provides ready-to-use prompts that participants can copy, customize with their local details, and paste into Replit.

---

## Before the Workshop

### What You Need

- A GitHub account (free) -- sign up at https://github.com
- A Replit account -- sign up at https://replit.com
- An internet connection
- A projector or shared screen for live demonstration
- Printed or digital copies of this guide for each participant

### Facilitator Preparation

1. Fork the CARA repository on GitHub and import it into Replit yourself before the workshop
2. Walk through the full prompt sequence at least once so you understand the flow and can troubleshoot
3. Have the CARA demo site open in a browser tab to show participants the finished product
4. Prepare any locally-relevant context you want participants to include in their prompts (jurisdiction names, known data sources, etc.)

---

## How This Guide Works

Each section below contains one or more **prompts** -- plain-language instructions you type (or paste) into Replit's chat. Replit reads the prompt, understands what needs to change in the code, and makes the changes for you. You review what it did, and if it looks right, you move on.

**Tips for working with prompts:**

- You can copy a prompt exactly as written and fill in the blanks, or you can rephrase it in your own words -- Replit understands natural language
- If Replit asks a clarifying question, answer it conversationally
- If something does not look right, tell Replit what is wrong and ask it to fix it
- You can always say "undo that last change" if something goes wrong
- Be as specific as possible -- the more detail you provide, the better the result

---

## Workshop Day 1: Understanding CARA and Planning Your Adaptation

### Session 1: What is CARA? (1 hour)

This session does not involve any prompts. The facilitator walks participants through the live CARA demo, showing:

- The home page with jurisdiction selection
- A sample jurisdiction dashboard with risk scores
- The risk score breakdown and how domains contribute to the overall score
- The Download Data tab
- The methodology page

Key concepts to cover:
- **Risk domains** are categories of risk (e.g., Natural Hazards, Health Metrics). Each domain gets a weight reflecting its importance.
- **The overall risk score** uses a formula that gives extra emphasis to domains with higher individual risk scores.
- **Jurisdictions** are the subnational geographic areas being assessed (counties, districts, governorates, etc.).

### Session 2: Planning Your Adaptation (2 hours)

Before using any prompts, the group works together to make four key decisions. Write down the answers -- you will use them in later prompts.

**Decision 1: What are your jurisdictions?**

List every subnational unit you want to assess. For each one, write down:
- Its name
- What region or parent area it belongs to (if applicable)

**Decision 2: What risk domains matter for your context?**

Discuss which of CARA's existing domains apply and what new ones you need. For reference, Wisconsin's CARA uses: Natural Hazards, Health Metrics, Active Shooter, Air Quality, and Extreme Heat.

**Decision 3: What data sources might be available?**

For each domain, brainstorm what data exists. Do not worry about finding the perfect sources yet -- Replit can help you research options.

**Decision 4: How should the domains be weighted?**

Decide how much each domain should contribute to the overall score. Weights must add up to 100%.

---

## Workshop Day 2: Setup, Adaptation, Data Integration, and Dashboard Refinement

### Session 3: Getting Started (20 minutes)

**Step 1: Fork the CARA repository**

1. Go to the CARA GitHub repository URL (provided by the facilitator)
2. Sign in to GitHub
3. Click the "Fork" button in the top-right corner
4. Name your fork something meaningful (e.g., `cara-libya`)
5. Click "Create fork"

**Step 2: Import into Replit**

1. Go to https://replit.com and sign in
2. Click "Create Repl" or the + button
3. Select "Import from GitHub"
4. Paste the URL of your forked repository
5. Click "Import from GitHub" and wait for the import
6. Set up the database when prompted

**Step 3: Confirm it runs**

1. Click the "Run" button
2. Wait for the application to start
3. You should see the Wisconsin version of CARA in the preview window -- this means setup is working

### Session 4: Orientation (10 minutes)

Before making changes, use this prompt to get oriented:

**Prompt:**

> I just imported the CARA risk assessment platform. Can you give me a brief overview of how the project is organized? Specifically, which files control: (1) the list of jurisdictions, (2) the risk domain weights, (3) the demographic data, (4) the vulnerability index data, and (5) the text and branding that appears on the home page? I am going to be adapting this for a different country, so I want to understand what I will need to change.

This gives you a guided tour of the project without changing anything.

### Session 5: Replace Jurisdictions and Branding (45 minutes)

This is the most important step. Use the following prompt, filling in your actual jurisdiction information:

**Prompt:**

> I need to adapt CARA for [YOUR COUNTRY/REGION]. Please make the following changes:
>
> 1. Replace all Wisconsin jurisdictions with these [NUMBER] jurisdictions for [YOUR COUNTRY/REGION]:
>    - [Name 1]
>    - [Name 2]
>    - [Name 3]
>    - [... continue for all jurisdictions]
>
> 2. Update the home page text to describe this as a risk assessment tool for [YOUR COUNTRY/REGION] healthcare emergency preparedness, replacing all references to Wisconsin, tribal nations, and U.S.-specific context.
>
> 3. Update the page header and footer to say "[YOUR PROJECT NAME]" instead of "CARA" and remove any Wisconsin-specific branding or disclaimers.
>
> 4. Remove or rename the "HERC Regions" tab. [Either: "Remove it entirely" OR "Rename it to [YOUR REGIONAL GROUPING NAME] and group the jurisdictions as follows: Region 1: [list], Region 2: [list], ..."]
>
> Please make sure every jurisdiction has a unique ID and that the jurisdiction names are consistent everywhere they appear.

**Example filled in for Libya:**

> I need to adapt CARA for Libya. Please make the following changes:
>
> 1. Replace all Wisconsin jurisdictions with these 22 jurisdictions for Libya:
>    - Tripoli
>    - Benghazi
>    - Misrata
>    - Sabha
>    - Zawiya
>    - Zliten
>    - Ajdabiya
>    - Al Khums
>    - Derna
>    - Sirte
>    - Tobruk
>    - Murzuq
>    - Zintan
>    - Gharyan
>    - Tarhuna
>    - Bani Walid
>    - Al Marj
>    - Ubari
>    - Ghat
>    - Nalut
>    - Yafran
>    - Al Jabal al Akhdar
>
> 2. Update the home page text to describe this as a risk assessment tool for Libyan healthcare emergency preparedness, replacing all references to Wisconsin, tribal nations, and U.S.-specific context.
>
> 3. Update the page header and footer to say "Libya Health Emergency Risk Assessment" instead of "CARA" and remove any Wisconsin-specific branding or disclaimers.
>
> 4. Remove the "HERC Regions" tab entirely since we do not have equivalent regional groupings yet.
>
> Please make sure every jurisdiction has a unique ID and that the jurisdiction names are consistent everywhere they appear.

After Replit makes the changes, click "Run" and verify that your jurisdiction names appear in the dropdown.

### Session 6: Update Risk Domains and Weights (20 minutes)

**Prompt:**

> I need to update the risk domains and their weights for [YOUR COUNTRY/REGION]. Here are the domains we want to use and how much each should contribute to the overall risk score:
>
> - [Domain 1]: [weight as percentage]% -- [brief rationale]
> - [Domain 2]: [weight as percentage]% -- [brief rationale]
> - [Domain 3]: [weight as percentage]% -- [brief rationale]
> - [... continue for all domains]
>
> The weights must add up to 100%.
>
> For existing CARA domains we are keeping, please update their weights. For domains we are removing (like [domain name]), set their weight to zero or remove them. For any new domains we are adding, please create placeholder calculation functions that return a default score of 0.5 for now -- we will connect real data later.
>
> Also update the methodology page to reflect these new domains, weights, and rationale.

**Example filled in for Libya:**

> I need to update the risk domains and their weights for Libya. Here are the domains we want to use and how much each should contribute to the overall risk score:
>
> - Conflict/Security: 25% -- primary driver of healthcare disruption in Libya
> - Health System Capacity: 25% -- healthcare infrastructure and workforce availability
> - Natural Hazards: 20% -- flooding, drought, and sandstorms
> - Infrastructure: 15% -- damage to roads, power, water systems
> - Extreme Heat: 10% -- seasonal heat stress on population and systems
> - Displacement: 5% -- internally displaced populations creating healthcare demand
>
> The weights add up to 100%.
>
> Please remove the Active Shooter and Air Quality domains (these are U.S.-specific). Remove Winter Storm and Tornado as natural hazard sub-types and replace them with Drought and Sandstorm. Keep Flood.
>
> For the new domains (Conflict/Security, Infrastructure, Displacement), create placeholder calculation functions that return a default score of 0.5 for now. We will connect real data later.
>
> Also update the methodology page to reflect these new domains, weights, and rationale.

### Session 7: Research Data Sources (30 minutes)

This is where Replit's research capabilities are especially useful. Use prompts like these to explore what data might be available for your jurisdiction:

**Prompt (general research):**

> What publicly available data sources exist for subnational risk assessment in [YOUR COUNTRY]? I am looking for data that covers topics like [list your domains]. The data needs to be broken down by district or municipality, not just national-level. Please search for international sources like INFORM, OCHA HDX, WHO, World Bank, ACLED, EM-DAT, and any [COUNTRY]-specific government or NGO data portals.

**Prompt (specific domain):**

> For the [DOMAIN NAME] domain of our risk assessment, what specific datasets could we use for [YOUR COUNTRY]? We need data that covers our [NUMBER] jurisdictions: [list a few]. What format is the data in? How often is it updated? Is it freely accessible? Can you find download links?

**Prompt (help evaluating a source):**

> I found a dataset from [SOURCE NAME] about [TOPIC] for [YOUR COUNTRY]. It is available at [URL]. Can you look at this data source and tell me: (1) Does it cover all of our jurisdictions? (2) What format is it in? (3) How could we use it in our risk assessment? (4) What are its limitations?

### Session 8: Add Demographic Data (30 minutes)

Once you have gathered population and demographic data for your jurisdictions, use this prompt:

**Prompt:**

> Please replace the Wisconsin demographic data with data for [YOUR COUNTRY/REGION]. Here is our population data:
>
> | Jurisdiction | Total Population | Population 65+ | Pct Aged 65+ |
> |---|---|---|---|
> | [Name 1] | [number] | [number] | [percentage] |
> | [Name 2] | [number] | [number] | [percentage] |
> | [... continue for all jurisdictions] |
>
> Make sure the jurisdiction names in the demographic data exactly match the jurisdiction names we set up earlier. If we do not have population aged 65+ data, use a reasonable estimate based on [YOUR COUNTRY]'s national demographics and note in the methodology page that these are estimates.

If you do not have exact data yet, you can use this alternative prompt:

**Prompt (estimated data):**

> We do not have exact demographic data for each of our [NUMBER] jurisdictions in [YOUR COUNTRY] yet. Can you research approximate population figures for each of our jurisdictions and create the demographic data files using the best available estimates? Please note in the data files and methodology page that these are preliminary estimates to be replaced with official data. Our jurisdictions are: [list all names].

### Session 9: Add Vulnerability Indicators (20 minutes)

**Prompt:**

> The original CARA uses the U.S. CDC Social Vulnerability Index (SVI) which does not apply to [YOUR COUNTRY]. Please replace it with vulnerability indicators appropriate for our context. For each of our [NUMBER] jurisdictions, we need scores between 0 and 1 (where higher means more vulnerable) for these categories:
>
> - Socioeconomic vulnerability (poverty, unemployment, income)
> - Healthcare access (distance to facilities, provider availability)
> - Infrastructure condition (roads, power, water reliability)
> - Housing vulnerability (building quality, overcrowding)
>
> [Option A:] Here is our data: [provide a table with values for each jurisdiction]
>
> [Option B:] We do not have this data yet. Please create reasonable placeholder values (all set to 0.5, which means neutral/unknown) and note in the methodology that these need to be populated with real data. The important thing is that the system works with placeholder data so we can test it while we gather real information.

### Session 10: Connect a Real Data Source (1 hour)

When you have actual data for one of your domains, use prompts like this to integrate it:

**Prompt (CSV data):**

> I have data for our [DOMAIN NAME] domain. Here is the data in CSV format:
>
> ```
> jurisdiction_name,indicator_1,indicator_2,indicator_3
> [Name 1],[value],[value],[value]
> [Name 2],[value],[value],[value]
> [... continue for all jurisdictions]
> ```
>
> Please:
> 1. Save this data to an appropriate file in the data/ folder
> 2. Create a calculation function that reads this data and produces a risk score between 0 and 1 for each jurisdiction
> 3. Connect this score to the main risk calculation so it contributes to the overall risk score using the weight we already set for this domain
> 4. Add a section on the dashboard that displays this domain's score and its component indicators
> 5. Update the methodology page with a description of this data source and how the score is calculated

**Prompt (API data):**

> I found that [ORGANIZATION] provides data on [TOPIC] through an API at [URL]. Can you:
> 1. Look at this API and understand what data it provides
> 2. Write code to fetch data for our [NUMBER] jurisdictions in [YOUR COUNTRY]
> 3. Cache the data in our database so we are not calling the API every time someone views the dashboard
> 4. Calculate a risk score between 0 and 1 from this data
> 5. Connect it to our [DOMAIN NAME] domain in the risk calculation

**Prompt (manual/qualitative data):**

> For our [DOMAIN NAME] domain, we do not have quantitative data from a database. Instead, our team has assessed each jurisdiction using a qualitative scale based on expert knowledge. Here are our assessments:
>
> | Jurisdiction | Risk Level | Notes |
> |---|---|---|
> | [Name 1] | High | [brief reason] |
> | [Name 2] | Medium | [brief reason] |
> | [Name 3] | Low | [brief reason] |
> | [... continue] |
>
> Please convert these qualitative assessments into numerical scores (High = 0.8, Medium = 0.5, Low = 0.2) and integrate them into the risk calculation for this domain. Store the notes as well so they appear on the dashboard as context. Note in the methodology that these scores are based on expert assessment rather than quantitative data.

### Session 11: Refine the Dashboard Display (20 minutes)

Once your domains are connected, you may want to adjust how information is displayed:

**Prompt:**

> Please update the dashboard to better reflect our [YOUR COUNTRY/REGION] context:
>
> 1. [Any specific display changes, e.g., "Show the Conflict/Security domain card at the top since it is our highest-weighted domain"]
> 2. [Any labels to change, e.g., "Change 'County' to 'District' everywhere it appears"]
> 3. [Any sections to remove, e.g., "Remove the NOAA Storm Events and OpenFEMA data sections since these are U.S.-specific data sources"]
> 4. [Any sections to add, e.g., "Add a map of Libya showing our districts, if possible"]
>
> Keep the overall layout and color scheme the same -- just update the content and labels.

---

## Workshop Day 3: Data Integrity, Testing, and Deployment

These sessions are essential. A risk assessment tool is only as valuable as its data is trustworthy and its methods are transparent. These prompts help you build a tool that is honest about what it knows, what it does not know, and how it arrives at its conclusions.

### Session 12: Data Transparency Audit (30 minutes)

Every score in CARA should be traceable back to a specific, citable data source. This prompt helps ensure nothing is fabricated or opaque:

**Prompt (full audit):**

> Please conduct a data transparency audit of our adapted CARA application. For every risk score and data point displayed on the dashboard, I need to know:
>
> 1. Where does the underlying data come from? Is it from a real, citable source (a government agency, international organization, published dataset) or is it a placeholder, estimate, or synthetic value?
> 2. For any data that is real: What is the source name, URL, and date of the data? Is this documented on the methodology page?
> 3. For any data that is placeholder or estimated: Is it clearly labeled as such on the dashboard and methodology page so users know it is not verified data?
> 4. Are there any scores being generated by the system that could appear to be real data but are actually calculated from assumptions or defaults?
>
> Please give me a complete inventory organized by domain, and flag anything that needs a source citation or a transparency disclaimer.

**Prompt (placeholder labeling):**

> For every domain or indicator where we are still using placeholder data (default values of 0.5 or estimates), please:
>
> 1. Add a visible notice on the dashboard next to that score that says "Preliminary estimate -- awaiting verified data" or similar language
> 2. Add a note on the methodology page listing which domains use verified data and which use placeholder values
> 3. Make sure no placeholder data can be mistaken for a real measurement or observation
>
> It is important that anyone using this tool can immediately tell the difference between scores backed by real data and scores that are temporary placeholders.

**Prompt (synthetic data check):**

> Please check whether any part of our application generates synthetic, simulated, or randomly generated data. In the original CARA, historical trend data was generated synthetically for research purposes. If any synthetic data generation exists in our adapted version:
>
> 1. List every place where synthetic data is created or used
> 2. Make sure each instance is clearly labeled with a warning like "SYNTHETIC DATA -- FOR ILLUSTRATION ONLY, NOT FOR OPERATIONAL DECISIONS"
> 3. Explain the difference between synthetic data and real data on the methodology page
>
> Our tool should never present made-up numbers as if they were real observations.

### Session 13: Validation and Accuracy (30 minutes)

These prompts help verify that the risk scores make sense and that the math is working correctly:

**Prompt (sanity check):**

> Please help me validate that our risk scores are reasonable by doing the following:
>
> 1. Show me the overall risk score and all domain scores for each of our [NUMBER] jurisdictions in a single table
> 2. Identify the highest-risk and lowest-risk jurisdictions for each domain
> 3. Based on what we know about [YOUR COUNTRY/REGION], do the rankings make sense? For example, is [JURISDICTION KNOWN TO BE HIGH-RISK] scoring higher than [JURISDICTION KNOWN TO BE LOWER-RISK]?
> 4. Are there any jurisdictions where all domain scores are identical? That would suggest the system is using default values instead of real data
> 5. Are there any scores at exactly 0.0 or exactly 1.0? These extremes are suspicious and may indicate a data problem
>
> Please flag any results that look unexpected and explain what might be causing them.

**Prompt (formula verification):**

> Please verify that the overall risk score calculation is working correctly:
>
> 1. Pick three jurisdictions and manually walk through the PHRAT formula step by step, showing the domain scores, the weights, the squaring, the weighted sum, and the final square root
> 2. Confirm that the calculated result matches what the dashboard displays
> 3. Confirm that all domain weights add up to exactly 1.0
> 4. Check that removing a domain (setting its weight to zero) does not break the calculation
>
> Show me the math for each jurisdiction so I can follow the logic.

**Prompt (data consistency):**

> Please check that our data is internally consistent:
>
> 1. Does every jurisdiction in our jurisdiction list have a corresponding entry in the demographic data, vulnerability data, and all domain data files?
> 2. Are there any jurisdiction names that are spelled slightly differently across different data files (which would cause mismatches)?
> 3. Are there any data files that have fewer jurisdictions than our full list?
> 4. Are all numerical values within expected ranges (populations are positive numbers, percentages are between 0 and 100, risk scores are between 0 and 1)?
>
> Fix any inconsistencies you find.

### Session 14: Ethical Data Use and Responsible Disclosure (30 minutes)

Risk assessment tools carry real responsibility. Scores can influence resource allocation, emergency response priorities, and public perception. These prompts address the ethical dimensions:

**Prompt (bias review):**

> Please review our risk assessment for potential bias:
>
> 1. Are any of our data sources or scoring methods likely to systematically score certain types of jurisdictions (e.g., rural, urban, ethnically diverse, economically disadvantaged) as higher or lower risk in ways that do not reflect actual risk?
> 2. Are we using any socioeconomic indicators (like poverty or income) as proxies for risk in ways that could stigmatize lower-income communities?
> 3. Does our vulnerability index unfairly penalize jurisdictions for demographic characteristics that are not actually risk factors?
> 4. Are there any domains where data availability is uneven across jurisdictions, meaning some areas get scored based on real data while others get scored based on assumptions?
>
> For each concern you identify, suggest how we can either adjust the methodology or add a disclaimer that acknowledges the limitation.

**Prompt (limitations and disclaimers):**

> Please add a "Limitations and Responsible Use" section to the methodology page that clearly states:
>
> 1. What this tool is designed for (strategic planning, preparedness prioritization, resource allocation discussions) and what it should NOT be used for (punitive decisions, public shaming of jurisdictions, sole basis for emergency response)
> 2. The known limitations of our data sources (coverage gaps, timeliness, proxy indicators)
> 3. Which domains use verified data and which use estimates or expert judgment
> 4. That risk scores are relative comparisons across jurisdictions, not absolute measurements of danger
> 5. That this tool is a decision-support aid, not a replacement for local knowledge and professional judgment
> 6. Who to contact with questions about methodology or data
>
> Use clear, non-technical language. This section should be understandable by anyone who uses the tool, not just the people who built it.

**Prompt (data sensitivity):**

> Please review our application for data sensitivity concerns:
>
> 1. Does our tool display any data that could put individuals, communities, or organizations at risk if misused? For example, exact locations of vulnerable facilities, detailed conflict incident data, or identifiable health information?
> 2. Is any of our data subject to restrictions on redistribution or public display?
> 3. Should any of our data be aggregated to a higher level (district instead of municipality, for example) to protect privacy or security?
> 4. Are there any data sources where we need to add attribution or licensing notices?
>
> If you identify concerns, suggest how to address them while still maintaining the tool's usefulness.

**Prompt (citation and attribution):**

> Please make sure every data source used in our tool is properly cited. For each domain on the methodology page:
>
> 1. List the exact name of each data source
> 2. Include the organization that produces it
> 3. Include the URL where the data can be accessed or verified
> 4. Include the date or version of the data we are using
> 5. Note any license or terms of use requirements
>
> Also add a general data attribution section to the footer or about page that lists all sources in one place. Anyone should be able to look at our tool and independently verify every number.

### Session 15: Ongoing Data Governance (15 minutes)

These prompts help set up practices for maintaining data quality after the workshop:

**Prompt (data freshness tracking):**

> Please add a "Data Sources and Freshness" page to our application that shows:
>
> 1. A table listing every data source, when it was last updated in our system, and how often it should be refreshed
> 2. Visual indicators (like color coding) for data that is current versus data that is overdue for an update
> 3. For each data source, a note about who is responsible for updating it and where to get fresh data
>
> This helps our team know when data needs to be refreshed and prevents the tool from silently becoming outdated.

**Prompt (update procedures):**

> Please create a simple data update guide (as a page in the application or a document in the docs/ folder) that explains:
>
> 1. How to update each data source -- where to download new data and what format it should be in
> 2. What to check after updating data to make sure nothing broke
> 3. How to verify that updated data is reflected in the risk scores
> 4. A recommended schedule for updating each data source
>
> Write this for a non-technical person who will be maintaining the tool after the workshop.

### Session 16: Comprehensive Testing (30 minutes)

Use this prompt for a thorough final check that covers both functionality and data integrity:

**Prompt:**

> Please conduct a final comprehensive test of our adapted CARA application:
>
> **Functionality:**
> 1. Does the home page load correctly with our jurisdiction names?
> 2. Can you click through to a dashboard for each jurisdiction without errors?
> 3. Are all risk scores within the expected 0 to 1 range?
> 4. Are there any remaining references to Wisconsin, U.S. counties, tribal nations, or other Wisconsin-specific content anywhere in the application?
> 5. Do the domain weights on the methodology page match what we configured?
> 6. Are there any broken links or missing images?
>
> **Data integrity:**
> 7. Is every data source cited on the methodology page?
> 8. Are placeholder values clearly labeled as preliminary estimates?
> 9. Is there any synthetic or generated data that is not clearly marked as such?
> 10. Does the "Limitations and Responsible Use" section accurately reflect the current state of the tool?
>
> **Transparency:**
> 11. Can a user trace any risk score back to its underlying data and methodology?
> 12. Is the PHRAT formula explained in language a non-technical user can understand?
> 13. Are domain weights and their rationale documented?
>
> Please fix anything you find and give me a summary of the tool's overall readiness, including what is complete, what uses placeholder data, and what still needs real data.

### Session 17: Refinement (30 minutes)

After testing, you may want to make adjustments. Here are some common refinement prompts:

**Adjusting weights:**

> After reviewing the test results, we think [DOMAIN] is weighted too [high/low]. Can you change its weight from [current]% to [new]% and redistribute the difference [equally among the other domains / to DOMAIN X]? Make sure all weights still add up to 100%.

**Adjusting scores:**

> The risk scores for [JURISDICTION NAME] seem [too high / too low / about the same as JURISDICTION 2 when they should be different]. Can you look at the input data and calculation for this jurisdiction and explain what is driving the score? Then suggest what we could adjust to make the scores better reflect reality.

**Adding context:**

> Can you add explanatory text to the dashboard that helps users understand what each risk score means in practical terms? For example, what does a score of 0.7 for [DOMAIN] mean in terms of real-world impact? Use language appropriate for [public health officials / emergency managers / government planners] in [YOUR COUNTRY].

### Session 18: Deployment (20 minutes)

**Prompt:**

> Our adapted CARA is ready to share. Can you help me deploy it so other people in our organization can access it through a web browser? Please walk me through the deployment process step by step.

After deployment, use this prompt to save your work:

**Prompt:**

> Can you help me push all of our changes back to our GitHub repository so our work is saved and backed up? The repository is at [YOUR GITHUB FORK URL].

---

## Quick Reference: Prompt Sequence Checklist

Use this checklist to track which prompts you have completed:

**Setup and Adaptation:**
- [ ] Orientation prompt (Session 4)
- [ ] Replace jurisdictions and branding (Session 5)
- [ ] Update risk domains and weights (Session 6)
- [ ] Research data sources (Session 7)
- [ ] Add demographic data (Session 8)
- [ ] Add vulnerability indicators (Session 9)
- [ ] Connect real data sources (Session 10, repeat for each domain)
- [ ] Refine dashboard display (Session 11)

**Data Integrity and Ethics:**
- [ ] Data transparency audit (Session 12)
- [ ] Placeholder labeling (Session 12)
- [ ] Synthetic data check (Session 12)
- [ ] Score validation and sanity check (Session 13)
- [ ] Formula verification (Session 13)
- [ ] Data consistency check (Session 13)
- [ ] Bias review (Session 14)
- [ ] Limitations and disclaimers (Session 14)
- [ ] Data sensitivity review (Session 14)
- [ ] Citation and attribution (Session 14)
- [ ] Data freshness tracking (Session 15)
- [ ] Update procedures documented (Session 15)

**Final Steps:**
- [ ] Comprehensive testing (Session 16)
- [ ] Refinements (Session 17)
- [ ] Deploy (Session 18)
- [ ] Save to GitHub (Session 18)

---

## Appendix A: Suggested Workshop Agenda

| Day | Session | Duration | Topic |
|-----|---------|----------|-------|
| 1 | 1 | 1 hour | What is CARA? Live demo walkthrough |
| 1 | 2 | 2 hours | Planning: jurisdictions, domains, data sources, weights |
| 2 | 3 | 20 min | Forking the code and setting up Replit |
| 2 | 4 | 10 min | Orientation prompt |
| 2 | 5 | 45 min | Replace jurisdictions and branding |
| 2 | 6 | 20 min | Update risk domains and weights |
| 2 | 7 | 30 min | Research data sources |
| 2 | 8 | 30 min | Add demographic data |
| 2 | 9 | 20 min | Add vulnerability indicators |
| 2 | 10 | 1 hour | Connect real data sources (facilitator-guided) |
| 2 | 11 | 20 min | Refine dashboard display |
| 3 | 12 | 30 min | Data transparency audit |
| 3 | 13 | 30 min | Validation and accuracy |
| 3 | 14 | 30 min | Ethical data use and responsible disclosure |
| 3 | 15 | 15 min | Ongoing data governance |
| 3 | 16 | 30 min | Comprehensive testing |
| 3 | 17 | 30 min | Refinement |
| 3 | 18 | 20 min | Deployment and saving to GitHub |

---

## Appendix B: Troubleshooting Prompts

If something goes wrong during the workshop, these prompts can help:

**If the application will not start:**

> The application is not starting. Can you check the error messages and fix whatever is wrong?

**If a page shows an error:**

> When I click on [JURISDICTION NAME], the dashboard shows an error. Can you figure out what is causing this and fix it?

**If you want to undo a change:**

> The last change did not work the way I expected. Can you undo it and go back to how it was before?

**If risk scores look wrong:**

> The risk scores for [JURISDICTION NAME] do not look right. The overall score is [value] but we expected it to be [higher/lower]. Can you show me what data and calculations are producing this score and suggest what might need to change?

**If you are not sure what to do next:**

> I am adapting CARA for [YOUR COUNTRY] and I have completed [list what you have done so far]. What should I work on next to get a functioning risk assessment tool?

---

## Appendix C: Glossary

**Risk Domain**: A category of risk that contributes to the overall score. Examples: Natural Hazards, Health Metrics, Conflict/Security.

**Weight**: A percentage that controls how much a domain contributes to the overall score. All weights must add up to 100%.

**Jurisdiction**: A geographic area being assessed. Could be a county, district, governorate, municipality, or other administrative unit.

**Risk Score**: A number between 0 and 1 representing how much risk a jurisdiction faces in a given domain. 0 means no risk; 1 means maximum risk.

**Fork**: Creating your own copy of a project on GitHub so you can modify it independently without affecting the original.

**Deploy**: Making your application accessible online through a web address (URL) so others can use it.

**Placeholder**: A temporary default value (like 0.5) used when real data is not yet available. Placeholders keep the system working while you gather actual data.

**Prompt**: A plain-language instruction you type into Replit's chat to tell it what changes to make.

---

*This guide was developed as part of the CARA open-source project, licensed under AGPLv3.*
*Adapt freely for your workshop context.*
