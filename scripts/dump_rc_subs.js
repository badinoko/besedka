// Dump Rocket.Chat users and subscriptions
print("=== ROCKET.CHAT USERS ===");
db.users.find({username:{$in:['owner','admin','store_owner','store_admin','test_user']}},{username:1,roles:1,active:1}).forEach(printjson);

print("\n=== CHANNEL SUBSCRIPTIONS BY USER ===");
db.subscriptions.aggregate([
  { $match: {'u.username': {$in:['owner','admin','store_owner','store_admin','test_user']}} },
  { $group: {_id:'$u.username', channels:{$addToSet:'$rid'}} }
]).forEach(printjson);

print("\n=== ALL CHANNELS ===");
db.rocketchat_room.find({t:{$in:['c','p']}},{_id:1,name:1,t:1,fname:1}).forEach(printjson);

print("\n=== OAUTH SETTINGS ===");
db.rocketchat_settings.find({_id:/Accounts_OAuth_Custom-besedka/},{_id:1,value:1}).forEach(printjson);
