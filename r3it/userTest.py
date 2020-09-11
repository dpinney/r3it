# userTest.def

from user import *

print('users()',users())
print('privilegedUsers() \n',privilegedUsers())
print('utilityUsers() \n',utilityUsers())
print('userRoles("engineer@electric.coop") \n',userRoles('engineer@electric.coop'))
print('userHasRole("engineer@electric.coop", "engineer") \n',userHasRole("engineer@electric.coop", 'engineer'))
print('userHasRole("engineer@electric.coop", "solarDeveloper") \n',userHasRole("engineer@electric.coop", 'solarDeveloper'))
print('userHasUtilityRole("engineer@electric.coop") \n',userHasUtilityRole("engineer@electric.coop"))
print('userHasUtilityRole("installer@solar.com") \n',userHasUtilityRole("installer@solar.com"))
print('userHomeDir("engineer@electric.coop") \n',userHomeDir('engineer@electric.coop'))
print('userAccountDict("engineer@electric.coop") \n',userAccountDict('engineer@electric.coop'))
print('passwordHash("engineer@electric.coop") \n',passwordHash('engineer@electric.coop'))
