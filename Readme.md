## Overview

R3IT is a free and open-source web application that allows utilities to automate the processing of solar interconnection requests.

It handles request submission, request review workflows, payment and signature collection, and optionally an automated engineering screening and approval process.

For full details on the application, please see our [presentation on automated interconnection screening](https://drive.google.com/file/d/1zsBoV4a9BIVMQWoLtOgYsDeK3V_T8Y7-/view?usp=sharing).

## Installation

1. Bring up an [Ubuntu 18.04 LTS](https://releases.ubuntu.com/18.04/) machine.
2. Configure DNS to point to new VM (needed for TLS cert creation).
3. Ensure ports 443 and 80 are open (e.g., on hosting provider's firewall).
4. Clone the repo: `git clone https://github.com/dpinney/r3it`
5. Edit r3it/config.py to add API keys, domain name, emails, etc. as appropriate.
6. Run the install script `cd r3it; sudo bash install.sh`
