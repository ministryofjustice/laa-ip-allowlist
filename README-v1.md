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

Run `filter_cidrs.py` with one or more `--group` arguments. Tags within a group are combined with **AND**, and multiple groups are combined with **OR**.

```bash
python filter_cidrs.py --group <tag1> [tag2 ...] [--group <tag3> ...]
```

**Examples:**

```bash
# Staff accessible app on Cloud Platform: expose to MoJ staff AND to MP live services
python filter_cidrs.py --group external staff --group external mp-live

# Internal facing app in MP: expose to Cloud Platform VPC and MP production VPC only
python filter_cidrs.py --group internal cp --group internal prod

# All external NAT gateways (Cloud Platform + all MP environments)
python filter_cidrs.py --group external nat
```

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

Pull the CIDR list at **deployment time**, not at application runtime. If the script fails or produces malformed output, your deployment should fail safely without affecting the currently running application.

Recommended approaches:

**Helm / GitHub Actions**
Generate the list during your CI pipeline and pass it as a Helm value:

```bash
CIDRS=$(python filter_cidrs.py --group external staff --group external mp-live | paste -sd, -)
helm upgrade my-app ./chart --set ingress.allowList="$CIDRS"
```

**Kubernetes `ingress.yaml` annotation (NGINX)**
```yaml
nginx.ingress.kubernetes.io/whitelist-source-range: "51.149.249.0/29,194.33.249.0/29,..."
```

**CircleCI**
Run the script as a step before your deploy step and export the result as an environment variable or write it to a file consumed by your Helm chart.

The key principle: if fetching or generating this list fails, the deployment should fail — not silently proceed with a broken or empty allow list.

---

## Maintenance

This list is maintained by the **LAA SRE Team**. If you need a new IP range added, have a query about an existing entry, or spot something that looks wrong, please reach out on the Slack channel **#ask-laa-sre**.

When adding a new CIDR to `laa-cidrs.yaml`, ensure it has:
- A clear `description` explaining what network it represents and who owns it
- Appropriate tags so teams can query for it correctly
- A PR reviewed by the LAA SRE team before merging