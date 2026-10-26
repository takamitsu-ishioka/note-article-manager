---
title: "Abstractions above the OS level hide design failures."
guid: "n7ad1f5970ece"
url: "https://note.com/kisaburo_y/n/n7ad1f5970ece"
published: "2026-02-10 12:22:26"
modified: "2026-02-10 12:22:26"
---

# Abstractions above the OS level hide design failures.

Abstractions above the OS level hide design failures.  
With that in mind, the development environment that maximizes both speed and quality looks like this:

- Dev environment: A low-spec, "bare" remote Linux VM.
- Production environment: Identical to dev.
- Workflow: Persistent SSH sessions.
- Tools: WinSCP and a lightweight text editor.
- No IDEs.
- No Serverless.
- Minimal Managed Services.
- Manual Scaling (even ChatGPT was manual in the beginning).  
  By adopting this configuration:  
  Development and operational costs drop by an order of magnitude.
- Every team member occupies an environment exactly the same as the Alpha/Production environment.
- The individual's dev environment becomes a literal sandbox.
- Failing becomes safe and fast.
- Development becomes synonymous with learning.
- Development speed and quality skyrocket.
- Simultaneously, subscription profit margins skyrocket.
- Customers, executives, developers, and managers—everyone is happy.  
  This setup immediately reflects a developer's mistakes back at them. That is the ultimate kindness.  
  A "bad development environment" spoils the developer by hiding design failures.  
  A "good development environment" trains the developer by exposing design failures.
