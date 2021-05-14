# config.py -------------------------------------------------------------------

import os

# import default settings -----------------------------------------------------

from r3it.defaults import *

# Important configuration variables - SET THESE

COOKIE_KEY = 'topsecretvalue' # Secret key for cookies; set this to a securely generated value.
STRIPE_PRIVATE_KEY = 'sk_test_2Mf8zBV1IqZkwtajeeK5lMCj00j0MxxuOu'
STRIPE_PUBLIC_KEY = 'pk_test_LAZ0aEKWMLHbPSFIms7YzLkK00EHoWgCGB'

DOMAIN = 'demo.r3it.ghw.io' # Fully qualified domain name for this site.

# Email configuration
r3itEmailAddress    = 'donotreply@r3it.ghw.io'  # Email address this app uses to send emails.
emailUser           = 'donotreply@r3it.ghw.io'  # Email login.
emailPassword       = 'verysecurepassword'      # Email password.
smtpServer          = 'box.ghw.io'              # SMTP Server for sending emails.

# utility parameters ----------------------------------------------------------

utilityName = 'Example Electric' # Name of the utility.
logo = os.path.join('/',STATIC_DIR,'exampleElectric.png') # Path to your utilities logo.
bg = os.path.join('/',STATIC_DIR,'background.jpg') # Path to the site background image.

# This dictionary sets the email addresses associated with authorized roles.
roles = {
    'engineer' : [
        'engineer@electric.coop',
        'engineer2@electric.coop'
    ],
    'memberServices' : [
        'ms@electric.coop',
        'engineer@electric.coop'
    ],
    'solarDeveloper' : [
        'installer@solar.com',
        'installer@secondsolar.com'
    ]
}

# application processing options ----------------------------------------------

enableAutomaticScreening = False # If True, this runs power flow analysis with the OMF. Requires the OMF.
useMockApplications = True # For testing purposes, this can create dummy interconnection applications.

# Set these if automatic screening is turned on.

sizeThreshold = 10 # Size threshold for for automatic approval, in kW-AC.
netMeteringCapacity = 10000 # Utility-wide net metering limit, in kW-AC. TODO: Should this be optional?
omdFilename = 'Olin Barre Geo Modified DER.omd' # File name for the electric feeder.
GEOCODE_KEY = ''              # Secret key for geocoding API.


# -----------------------------------------------------------------------------
# One should not normally need to change anything below this line. ------------
# -----------------------------------------------------------------------------

# Specifies the user roles which are affiliated with the utility. -------------

utilityRoles = [
    'engineer',
    'memberServices'
]
