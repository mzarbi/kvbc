from getpass import getuser

from core.crypto import CryptoManager

print(CryptoManager.retrieve_key(getuser()), getuser())