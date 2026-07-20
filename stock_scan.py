from datetime import datetime
import jquantsapi

cli = jquantsapi.ClientV2()

listing = cli.get_listed_info()

print(listing.columns.tolist())
print(listing.head())
