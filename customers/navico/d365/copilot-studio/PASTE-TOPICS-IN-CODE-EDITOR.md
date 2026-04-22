# Navico Custom Topics — Paste into Copilot Studio Code Editor

> **Why this file exists:** Custom topics cannot be created via the Dataverse API — they must be created in the Copilot Studio web editor. For each topic below, follow the steps then paste the YAML into the Code Editor.

## How to Create Each Topic

1. Go to **https://copilotstudio.microsoft.com**
2. Select **Navico Self-Service Assistant**
3. Go to **Topics** (left nav)
4. Click **+ Add a topic** → **From blank**
5. At the top, click **⋯ (More)** → **Open code editor**
6. **Select all** and **replace** with the YAML below
7. Click **Save**
8. Repeat for each topic

---

## Topic 1: Product Troubleshoot

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Product Troubleshoot
    triggerQueries:
      - troubleshoot
      - not working
      - broken
      - my product isn't working
      - won't turn on
      - screen is black
      - firmware issue
      - update failed
      - NMEA not connecting
      - devices not talking
      - radar not showing
      - connectivity problem
      - error message
      - product fault

  actions:
    - kind: SendActivity
      id: sendMessage_pt1
      activity:
        text:
          - "I'd be happy to help troubleshoot your Navico product. Could you provide the **serial number**? You can find it on the product label or in **Settings > About**."

    - kind: Question
      id: question_serial
      property: Topic.SerialNumber
      interruptionPolicy:
        allowInterruption: true
      prompt:
        text: "What is the serial number?"

    - kind: SendActivity
      id: sendMessage_pt2
      activity:
        text:
          - "Thanks! Let me guide you through diagnostics:\n\n1️⃣ **Check power supply** — verify input voltage (10-35V DC for most MFDs)\n2️⃣ **Inspect wiring** — check for corrosion (common in marine environments)\n3️⃣ **Check fuses** — a blown fuse is the most common cause\n4️⃣ **Hard reset** — hold power button 15 seconds, wait 10 seconds, power on\n5️⃣ **Disconnect peripherals** — remove NMEA 2000, Ethernet, test standalone\n\nDid any of these steps help?"

    - kind: Question
      id: question_resolved
      property: Topic.Resolved
      interruptionPolicy:
        allowInterruption: true
      prompt:
        text: "Did that resolve the issue?"

    - kind: ConditionGroup
      id: conditionGroup_1
      conditions:
        - id: conditionItem_yes
          condition: =Topic.Resolved = "Yes"
          actions:
            - kind: SendActivity
              id: sendMessage_done
              activity:
                text:
                  - "Great, glad I could help! 🎉 Is there anything else I can assist you with?"

      elseActions:
        - kind: SendActivity
          id: sendMessage_esc
          activity:
            text:
              - "I'm sorry the troubleshooting steps didn't resolve the issue. Let me connect you with a Navico support specialist. They'll have our full conversation so you won't need to repeat anything."
        - kind: BeginDialog
          id: beginDialog_esc1
          dialog: cra1f_agentLrdu6W.topic.Escalate
```

---

## Topic 2: Warranty Check

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Warranty Check
    triggerQueries:
      - check warranty
      - warranty status
      - is my product under warranty
      - warranty expired
      - still covered
      - when does warranty end
      - how long is my warranty

  actions:
    - kind: SendActivity
      id: sendMessage_wc1
      activity:
        text:
          - "I can help check your warranty status. I'll need your **product serial number** — you can find it on the product label or in **Settings > About**."

    - kind: Question
      id: question_serial
      property: Topic.SerialNumber
      interruptionPolicy:
        allowInterruption: true
      prompt:
        text: "What is the serial number?"

    - kind: SendActivity
      id: sendMessage_wc2
      activity:
        text:
          - "Looking up serial **{Topic.SerialNumber}**...\n\n📋 **Standard Warranty:** 2 years from purchase/registration\n🔒 **Covers:** Manufacturing defects and component failure\n❌ **Not covered:** Physical damage, misuse, unauthorized modifications\n\nFor exact warranty dates, I'll connect you with a specialist. Would you like to:\n\n1️⃣ **Connect with a specialist** for exact warranty details\n2️⃣ **Learn about extended warranty options**\n3️⃣ **Start a return or exchange request**"

    - kind: SendActivity
      id: sendMessage_wc3
      activity:
        text:
          - "Let me connect you with a specialist who can help."
    - kind: BeginDialog
      id: beginDialog_esc2
      dialog: cra1f_agentLrdu6W.topic.Escalate
```

---

## Topic 3: Product Registration

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Product Registration
    triggerQueries:
      - register my product
      - product registration
      - activate warranty
      - register new product
      - I just bought a new
      - register serial
      - new product setup

  actions:
    - kind: SendActivity
      id: sendMessage_pr1
      activity:
        text:
          - "Great — registering your product activates your warranty. I'll need:\n\n1. **Serial number** (product label or Settings > About)\n2. **Purchase date**\n3. **Installation details** (professional or self-installed)"

    - kind: Question
      id: question_serial
      property: Topic.SerialNumber
      interruptionPolicy:
        allowInterruption: true
      prompt:
        text: "What is the serial number?"

    - kind: Question
      id: question_date
      property: Topic.PurchaseDate
      interruptionPolicy:
        allowInterruption: true
      prompt:
        text: "When did you purchase it? (approximate date is fine)"

    - kind: Question
      id: question_installer
      property: Topic.InstallerType
      interruptionPolicy:
        allowInterruption: true
      prompt:
        text: "Was this professionally installed or self-installed?"

    - kind: SendActivity
      id: sendMessage_pr2
      activity:
        text:
          - "Thanks! Here's a summary:\n\n📝 **Registration Details**\n• Serial: **{Topic.SerialNumber}**\n• Purchase Date: **{Topic.PurchaseDate}**\n• Installation: **{Topic.InstallerType}**\n\nI'll connect you with a specialist to finalize. They'll create your asset record and activate your warranty."

    - kind: BeginDialog
      id: beginDialog_esc3
      dialog: cra1f_agentLrdu6W.topic.Escalate
```

---

## Topic 4: Certification Inquiry

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: Certification Inquiry
    triggerQueries:
      - certification status
      - dealer certification
      - am I certified
      - installer certification
      - certification program
      - get certified
      - renew certification
      - certification expired
      - training program

  actions:
    - kind: SendActivity
      id: sendMessage_ci1
      activity:
        text:
          - "I can help with the Navico Dealer Certification Program!\n\n🎓 **Check existing certification status**\n📝 **Enroll in a new certification**\n🔄 **Renew an expiring certification**\n❓ **Learn about the program**\n\nWhich would you like help with?"

    - kind: Question
      id: question_action
      property: Topic.CertAction
      interruptionPolicy:
        allowInterruption: true
      prompt:
        text: "Which would you like help with?"

    - kind: ConditionGroup
      id: conditionGroup_cert
      conditions:
        - id: conditionItem_learn
          condition: =contains(Topic.CertAction, "learn") || contains(Topic.CertAction, "about") || contains(Topic.CertAction, "program")
          actions:
            - kind: SendActivity
              id: sendMessage_learn
              activity:
                text:
                  - "The **Navico Certification Program** has 3 levels:\n\n🥉 **Basic Certified** — online training + exam (80% to pass)\n→ Dealer pricing, standard support\n\n🥈 **Advanced Certified** — product-specific training (85% to pass)\n→ Priority support, advanced exchange\n\n🥇 **Expert Certified** — multi-brand + field assessment (90% to pass)\n→ Tier 4 direct access, System Assembly Assurance, beta firmware\n\nAll training is on the Navico Certification Portal. Would you like to know anything else?"

      elseActions:
        - kind: SendActivity
          id: sendMessage_connect
          activity:
            text:
              - "I'll connect you with a specialist who can help with your certification inquiry."
        - kind: BeginDialog
          id: beginDialog_esc4
          dialog: cra1f_agentLrdu6W.topic.Escalate
```

---

## After Creating All 4 Topics

1. Go back to **Overview** → click **Publish** (top right)
2. Test each topic in the **Test your agent** panel:
   - Type `my product won't turn on` → should trigger Product Troubleshoot
   - Type `is my product under warranty` → should trigger Warranty Check
   - Type `register my product` → should trigger Product Registration
   - Type `certification status` → should trigger Certification Inquiry
