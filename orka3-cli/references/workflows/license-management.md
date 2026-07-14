# License Management Reference

## Overview

Orka Engine uses floating licenses with concurrent seat limits. Licenses are managed through the **LicenseSpring customer portal**, separate from the MacStadium portal.

**Portal URL:** macstadium.users.licensespring.com

## Authentication

Your account is auto-created during license provisioning.
- **Email:** Your MacStadium account email
- **Password:** The generated password sent in your license delivery email
- **Note:** Portal password is separate from your MacStadium portal password
- **Reset:** Contact support@macstadium.com

## License Information

The portal displays:
- License key
- License classification (trial or commercial)
- Current seat usage vs. maximum allowance
- Expiration date
- Activation history

## Node Activation Management

Each Orka node consumes a concurrent seat. To release a seat from a decommissioned or replaced node:
1. Locate the activation in your activation history in the portal
2. Select the revocation option — the seat releases immediately

On AWS, you can override a node's license key via Ansible without a full upgrade:
```bash
ansible-playbook -i arm.ssh.aws_ec2.yml configure-arm.yml \
  --private-key ~/.ssh/id_rsa -e override_orka_engine_license_key=<new-key>
```

## Automated Notifications

LicenseSpring sends email alerts for:
- 30-day expiration warnings
- License expiration
- New node activations
- Approaching seat limits
- Reached seat limits

## Support

Contact support@macstadium.com for:
- License questions
- Seat count increases
- Renewals
