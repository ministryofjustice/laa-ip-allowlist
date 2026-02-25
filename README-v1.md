# LAA Shared IP Allow List

A centrally maintained list of CIDRs for use in IP-restricted ingress configurations across LAA applications. This list should be used as a convenience layer for access control - **it is not a primary security control** and should not be treated as one.

---

## Overview

The `laa-cidrs.yaml` file contains a tagged list of IP ranges covering:

- **Staff access** — MoJ VPN egress IPs, MoJ WiFi, and Global Protect VPN users
- **Cloud Platform** — NAT gateway and VPC ranges for apps hosted on Cloud Platform
- **Modernisation Platform** — NAT gateway and VPC ranges across dev, test, preprod, and prod environments

Each CIDR entry has one or more tags. The `filter_cidrs.py` script lets you query this list using tag logic to produce a filtered list of CIDRs suitable for use in a Kubernetes `ingress.yaml` or similar.

---

## Querying the list

### Tag logic

Tags within a `--group` are combined with **AND**. Multiple `--group` arguments are combined with **OR**.

**Available tags:**

| Tag | Description |
|---|---|
| `external` | Publicly routable IPs (egress/NAT) |
| `internal` | Private/RFC1918 ranges (VPCs, internal networks) |
| `staff` | MoJ staff access (VPN egress, MoJ WiFi, Global Protect) |
| `nat` | NAT gateway IPs for Cloud Platform or Modernisation Platform |
| `cp` | Cloud Platform |
| `mp` | Modernisation Platform |
| `mp-live` | Modernisation Platform — PreProd and Production environments |
| `mp-nonlive` | Modernisation Platform — Dev and Test environments |
| `dev` | Modernisation Platform Development VPC |
| `test` | Modernisation Platform Test VPC |
| `preprod` | Modernisation Platform Pre-Production VPC |
| `prod` | Modernisation Platform Production VPC |

---

## Integrating with your application

There are two ways to generate a CIDR list: using the provided **GitHub Actions reusable workflow** (recommended), or running the **Python script** directly in your own pipeline.

In either case, pull the list at **deployment time**, not at application runtime. If the script fails or produces malformed output, your deployment should fail safely without affecting the currently running application.

---

### Option 1: GitHub Actions reusable workflow (recommended)

This repository provides a reusable workflow you can call from your own GitHub Actions pipelines. It accepts tag groups as input and outputs a comma-separated CIDR list you can pass directly to your Helm chart or ingress configuration. There is a test.yml workflow example similar to below.

**Calling the workflow:**

```yaml
jobs:
  get-allowlist:
    uses: ministryofjustice/laa-ip-allowlist/.github/workflows/generate-allowlist.yml@v1.0.0
    with:
      # Separate tags within a group with spaces, separate groups with semicolons
      groups: "external staff;external mp-live"

  deploy:
    needs: get-allowlist
    runs-on: ubuntu-latest
    steps:
      - name: Deploy with allowlist
        run: |
          helm upgrade my-app ./chart \
            --set ingress.allowList="${{ needs.get-allowlist.outputs.allowlist }}"
```

**Workflow inputs:**

| Input | Required | Description | Example |
|---|---|---|---|
| `groups` | Yes | Semicolon-separated tag groups. Tags within a group are space-separated. | `"external staff;external mp-live"` |

**Workflow outputs:**

| Output | Description | Example |
|---|---|---|
| `allowlist` | Comma-separated list of matching CIDRs | `"51.149.249.0/29,194.33.249.0/29,..."` |

**Example group combinations:**

| Scenario | `groups` input |
|---|---|
| Staff-accessible app on Cloud Platform | `"external staff;external mp-live"` |
| Internal app: CP VPC and MP production only | `"internal cp;internal mp prod"` |
| All external NAT gateways | `"external nat"` |

---

### Option 2: Python script directly

If you are not using GitHub Actions, you can run `filter_cidrs.py` directly in your pipeline.

```bash
python filter_cidrs.py --group <tag1> [tag2 ...] [--group <tag3> ...]
```

To produce a comma-separated list suitable for a Helm value:

```bash
CIDRS=$(python filter_cidrs.py --group external staff --group external mp-live | paste -sd, -)
helm upgrade my-app ./chart --set ingress.allowList="$CIDRS"
```

**Kubernetes NGINX ingress annotation:**
```yaml
nginx.ingress.kubernetes.io/whitelist-source-range: "51.149.249.0/29,194.33.249.0/29,..."
```

---

## Maintenance

This list is maintained by the **LAA SRE Team**. If you need a new IP range added, have a query about an existing entry, or spot something that looks wrong, please reach out on the Slack channel **#ask-laa-sre**.

When adding a new CIDR to `laa-cidrs.yaml`, ensure it has:
- A clear `description` explaining what network it represents and who owns it
- Appropriate tags so teams can query for it correctly
- A PR reviewed by the LAA SRE team before merging