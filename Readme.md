## Overview

R3IT is a free and open-source web application that allows utilities to automate the processing of solar interconnection requests.

It handles request submission, request review workflows, payment collection, signature collection, email notifications for any status changes, and optionally an automated engineering screening and approval process.

For full details on the application, please see our [presentation on automated interconnection screening](https://drive.google.com/file/d/1zsBoV4a9BIVMQWoLtOgYsDeK3V_T8Y7-/view?usp=sharing) or try out the app on our [R3IT public demonstration server](https://demo.r3it.ghw.io).

## Application Deployment

#### Installation

1. Bring up an [Ubuntu 20.04 LTS](https://releases.ubuntu.com/18.04/) machine.
2. Configure DNS to point to new VM (needed for TLS cert creation).
3. Ensure ports 443 and 80 are open (e.g., on hosting provider's firewall).
4. Clone the repo: `git clone https://github.com/dpinney/r3it`to /opt/
5. Edit r3it/config.py to add API keys, domain name, emails, etc. as appropriate.
6. Run the install script `cd /opt/r3it; sudo bash install.sh`

#### Configuration

The application can be configured to match your utility branding and integrate with services you use. Configuration is optional--you can deploy with defaults, or change them. Some of the things that can be configured:

1. A domain (or subdomain) for the app.
1. A [Stripe account and API key](https://stripe.com/payments) for payment integration.
1. Email addresses for the system admin, engineers, and member services staff.
1. SMTP credentials and an email address for automated emails from application.
1. Branding: a Co-op logo, background image, and text that should be shown on the home screen.

#### Updating the Application

In the main r3it directory, run a `git pull`. Updated code will be installed, while the database and configuration values will be preserved.

## Acknowledgments

This material is based upon work supported by the U.S. Department of Energy's Office of Energy Efficiency and Renewable Energy (EERE) under the Solar Energy Technologies Office Award Number DE-EE0009011.
