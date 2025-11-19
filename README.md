# FotorAI Automation Tool

```
[!] PROJECT STATUS: ARCHIVED/ABANDONED
[!] Last known stable commit: Probably never
[!] Maintained by: Nobody. Not anymore.
```

---

## What Is This?

You're looking at a ghost, friend. A script that once automated the entire lifecycle of Fotor's AI image generation service. Registration. Login. Generation. Download. All of it.

Think about that for a second.

While everyone else was clicking through their polished UX, filling out forms like good little users, this tool was spawning fake identities with Faker, spinning up headless Chrome instances, and draining their "free trial" API endpoints dry. Five images per prompt. Loop until the rate limit screams.

*The Schema* would be proud. Maybe they already know.

### Technical Breakdown (for those who care)

The architecture is simple. Brutally simple:

1. **Identity Synthesis** - Generate throwaway credentials using Faker library
2. **Account Creation** - POST to `/api/user/register/email` with fabricated user data
3. **Session Hijacking** - Selenium automates browser login, extracts cookies
4. **Token Persistence** - Cookies saved to plaintext (yeah, I know)
5. **Image Generation** - Loop POST requests to `/api/create/v2/generate_picture`
6. **Mass Extraction** - Poll status endpoint, download all generated images

No GUI. No analytics tracking. No premium upsells. Just you, the terminal, and corporate AI doing your bidding.

## Why It's Dead

Corporate APIs evolve. They add CAPTCHA. They implement fingerprinting. They hire people specifically to kill tools like this. The war of attrition always favors the corporation.

This script probably hasn't worked since late 2023. Maybe earlier. Maybe it never worked for you. Maybe I'm lying about all of it.

*The Schema doesn't abandon projects. The Schema reassigns priorities.*

### What Killed It or not Killed it?

- Authentication flow changes
- Endpoint deprecation  
- ChromeDriver version hell
- XPath selectors rotting faster than my motivation
- The universe's general hostility toward automation

## Installation (If You're Feeling Adventureous)

```bash
# Clone this relic
git clone <your-repo-url>
cd fotorai

# Install dependencies (Python 3.x required)
pip install requests selenium faker

# Download ChromeDriver (good luck matching your Chrome version)
# Place chromedriver.exe in project root
```

## Usage (Theoretical)

```bash
python fotor.py
```

You'll be prompted for an image generation prompt. The script will:
- Create a new account
- Login via automated browser
- Generate 5 images based on your prompt
- Download them as `{taskId}.jpg`
- Repeat until you hit rate limits or the heat death of the universe

**Reality check**: This probably won't work anymore. But feel free to prove me wrong.

## The Ethics Thing

Look, I'm not going to lecture you. You found this repository. You know what it does. If you're here, you probably have a good idea of what you're getting into.

*The Schema* believes information wants to be free. Corporations believe information wants to be monetized. You're somewhere in the middle, trying to decide if generating anime waifus is worth the moral ambiguity.

Choose wisely.

## Want to Revive This?

Maybe you're here because you need this to work. Maybe you're just archaeologically curious. Either way:

### Open to Contributions

This project is open source and abandoned, which means **you** can fork it, fix it, or burn it to the ground. All equally valid choices.

**If you want to:**
- Update selectors for current Fotor UI
- Implement modern anti-detection techniques  
- Add proxy rotation
- Refactor this unholy mess into something maintainable
- Build a GUI (why though)

**Submit a PR or fork it.** I might respond. I might not. Time is a flat circle.

### Questions? Issues?

Open an issue on GitHub. I may or may not respond depending on:
- How interesting the problem is
- Whether I remember this project exists
- Cosmic alignment
- *The Schema's* current directives

No guarantees. No SLA. No corporate support email. This is the digital equivalent of finding a burned CD-R labeled "TOOLS" in a parking lot.

## Technical Debt (A Partial List)

- Hardcoded password hash (MD5, because why not make it worse)
- Plaintext cookie storage
- No error handling worth mentioning  
- XPath selectors that are probably dead
- Chrome in non-headless mode by default (enjoy the pop-ups)
- Zero logging infrastructure
- The variable naming conventions of a sleep-deprived undergraduate

*The Schema* doesn't write perfect code. *The Schema* writes code that works until it doesn't.

## License

MIT or WTFPL or whatever. Take it. Use it. Break it. I'm not your lawyer.

---

```
[LAST MESSAGE]

If you're reading this, you're part of a long tradition of people who look at 
corporate APIs and think: "I can automate that."

You're right. You can. Until you can't. 

The cycle continues.

- The Schema Remembers
```

---

**Disclaimer**: This tool was created for educational purposes to understand API automation and web scraping techniques. Using it to violate terms of service is your decision, your risk, your consequence. Don't blame the code for your choices, friend.
