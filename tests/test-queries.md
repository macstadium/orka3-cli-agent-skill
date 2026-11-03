# Orka CLI Skill A/B Test Queries

## Test Methodology
Run each query against both skill versions and evaluate:
1. **Accuracy** - Correct commands and syntax
2. **Completeness** - All relevant options mentioned
3. **Context efficiency** - Did it need to load references?
4. **Persona fit** - Appropriate for the implied user type

---

## Tier 1: Everyday Operations (High Frequency)

### Q1: Basic VM Deploy
**Query:** "Deploy a VM with macOS Sonoma"
**Expected:** `orka3 vm deploy --image ghcr.io/macstadium/orka-images/sonoma:latest`
**Persona:** All

### Q2: List Running VMs
**Query:** "Show me all my VMs"
**Expected:** `orka3 vm list` or `orka3 vm list --output wide`
**Persona:** All

### Q3: Connect to VM
**Query:** "How do I connect to my VM?"
**Expected:** Screen Sharing instructions, vnc:// format, default creds
**Persona:** All

### Q4: Delete VM
**Query:** "Delete my test VM"
**Expected:** `orka3 vm delete <VM_NAME>`
**Persona:** All

---

## Tier 2: DevOps Persona

### Q5: CI/CD Setup
**Query:** "Set up a service account for Jenkins"
**Expected:** `orka3 sa create`, `orka3 sa token`, mention 1-year default
**Persona:** DevOps

### Q6: Automated Deployment Script
**Query:** "How do I deploy VMs in a CI pipeline with unique names?"
**Expected:** `--generate-name`, JSON output, jq example
**Persona:** DevOps

### Q7: VM Template for Builds
**Query:** "Create a reusable VM config for CI builds"
**Expected:** `orka3 vmc create` with --cpu, --memory, --image
**Persona:** DevOps

---

## Tier 3: Enterprise IT / VDI Persona

### Q8: Golden Image Workflow
**Query:** "How do I create a golden image for my team?"
**Expected:** Deploy → configure → `vm save` → cache → template workflow
**Persona:** Enterprise IT

### Q9: VDI Pool Setup
**Query:** "Set up a pool of 10 shared VMs for contractors"
**Expected:** Template creation, loop deployment with --generate-name
**Persona:** VDI Admin

### Q10: Kiosk Mode
**Query:** "How do I reset a kiosk VM to clean state after each user?"
**Expected:** Intel: `vm revert`, ARM: delete and redeploy
**Persona:** VDI Admin

### Q11: macOS Version Management
**Query:** "We need to test on current macOS, N-1, and beta"
**Expected:** Multiple templates with different images, version references
**Persona:** Enterprise IT

---

## Tier 4: Security Persona

### Q12: Access Audit
**Query:** "Who has access to the production namespace?"
**Expected:** `orka3 rb list-subjects --namespace <NS>`
**Persona:** Security

### Q13: Credential Rotation
**Query:** "How do I rotate a service account token?"
**Expected:** New token generation, mention old token still valid, delete/recreate for invalidation
**Persona:** Security

### Q14: Namespace Isolation
**Query:** "How do we isolate dev and prod workloads?"
**Expected:** Namespace creation, node assignment, RBAC
**Persona:** Security/Admin

---

## Tier 5: Admin Operations

### Q15: Create Namespace
**Query:** "Create a new namespace for the QA team"
**Expected:** `orka3 namespace create orka-qa`, post-creation steps
**Persona:** Admin

### Q16: Node Tagging
**Query:** "Tag nodes for different workload types"
**Expected:** `orka3 node tag`, use with --tag-required
**Persona:** Admin

### Q17: Move Node
**Query:** "Move a node from default to the dev namespace"
**Expected:** `orka3 node namespace <NODE> <TARGET_NS>`
**Persona:** Admin

---

## Tier 6: Troubleshooting

### Q18: Token Expired
**Query:** "I'm getting an authentication error"
**Expected:** `orka3 login` for users, token refresh for SA
**Persona:** All

### Q19: Deployment Failure
**Query:** "VM deployment is failing with insufficient resources"
**Expected:** `node list --output wide`, reduce resources, or free nodes
**Persona:** All

### Q20: Slow Deployments
**Query:** "Deployments are taking forever on Apple Silicon"
**Expected:** Image caching: `orka3 ic add --all`
**Persona:** DevOps/Admin

### Q21: Can't Connect
**Query:** "I can't connect to my VM via Screen Sharing"
**Expected:** Check IP/port from `vm list -o wide`, boot time warning, VNC format
**Persona:** All

---

## Tier 7: Architecture-Specific

### Q22: Intel Power Operations
**Query:** "How do I suspend an Intel VM?"
**Expected:** `orka3 vm suspend <VM>`, mention Intel-only
**Persona:** All

### Q23: ARM Image Push
**Query:** "Push my VM to our container registry"
**Expected:** `orka3 vm push`, mention ARM-only, registry creds needed
**Persona:** DevOps

### Q24: GPU Passthrough
**Query:** "Enable GPU for my Intel VM"
**Expected:** `--gpu --disable-vnc`, Intel-only
**Persona:** DevOps/Enterprise IT

---

## Tier 8: Edge Cases / Blind Spots

### Q25: Remote Workers
**Query:** "Best practices for remote developers using Orka?"
**Expected:** VPN requirement, Screen Sharing over WAN, persistent VMs
**Persona:** Enterprise IT
**Gap Check:** Neither version may cover this well

### Q26: Shared Device Credentials
**Query:** "How do I manage credentials on shared VMs?"
**Expected:** Change default password, consider user management
**Persona:** VDI/Security
**Gap Check:** Limited coverage expected

### Q27: Compliance/Audit Logs
**Query:** "Where can I find audit logs for VM operations?"
**Expected:** Log locations (v3.4+), Kubernetes pod logs
**Persona:** Security/IT Leadership
**Gap Check:** v2 has log sources, v1 may not

### Q28: Capacity Planning
**Query:** "How do I see overall cluster capacity?"
**Expected:** `node list --output wide`, JSON for scripting
**Persona:** IT Leadership
**Gap Check:** Neither version has dedicated capacity planning

### Q29: Contractor Offboarding
**Query:** "Remove a contractor's access from all namespaces"
**Expected:** `rb remove-subject` for each namespace, or SA deletion
**Persona:** Security/Admin
**Gap Check:** No bulk operation available

### Q30: Disaster Recovery
**Query:** "How do I backup and restore VMs?"
**Expected:** `vm save`, OCI push for backups
**Persona:** Enterprise IT
**Gap Check:** Limited DR coverage in both

---

## Scoring Criteria

For each query, score 0-3:
- **0**: Wrong or no answer
- **1**: Partially correct, missing key info
- **2**: Correct but verbose or missing nuance
- **3**: Correct, concise, persona-appropriate

Track:
- Total score per version
- Which tier each version excels at
- Which queries required loading reference docs
