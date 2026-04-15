# UX Profiles — Microsoft Code App Standards

UX Profiles define **what standards apply** based on deployment context.
When building any Code App, specify a profile and the UX review agent enforces those rules.

## How It Works

1. **Profile** = a named context (web-app, d365-embedded, teams-tab, mobile, canvas-embed)
2. Each profile sets: token source, spacing scale, nav pattern, component rules, accessibility tier
3. `/ux-review` reads the active profile from `.ux-profile` in the customer's app folder
4. All generated code must pass the profile's checklist before commit

## Available Profiles

| Profile | Context | Token Source | Nav Pattern | Notes |
|---------|---------|-------------|-------------|-------|
| `web-app` | Standalone browser | Fluent 2 CSS tokens | Top tabs + sidebar | Default for Code Apps |
| `d365-embedded` | Custom page inside D365 | D365 Fluent theme vars | No chrome (D365 provides shell) | Use `msdyn_` CSS vars |
| `teams-tab` | Teams personal/channel tab | Teams Design System | Top tabs only, 44px height | Must use Teams JS SDK |
| `mobile` | Mobile browser / PWA | Fluent Mobile tokens | Bottom nav, 44px touch targets | No hover states |
| `canvas-embed` | Power Apps canvas Code component | Minimal, PCF-safe | None (canvas provides shell) | No window/document APIs |
| `pbi-embedded` | Power BI report visual | Minimal, read-only | None | No interaction beyond filter |

## Setting a Profile

Drop a `.ux-profile` file in the app folder:
```
customers/ge_erac/crm/demo-assets/.ux-profile
```
Contents: just the profile name, e.g. `web-app`

When embedded in D365 as a Custom Page, change to `d365-embedded`.

## Profile Hierarchy

```
Global defaults (skills/ux-profiles/base.json)
  └── Profile overrides (skills/ux-profiles/{profile}.json)
        └── Customer overrides (customers/{name}/.ux-overrides.json)
```

## Using with /ux-review

```
/ux-review profile=d365-embedded file=customers/ge_erac/crm/demo-assets/erac_lite_crm.html
```

The agent will enforce only the rules applicable to that profile.
