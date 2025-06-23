db.subscriptions.aggregate([
  { $match: {'u.username': {$in:['owner','admin','store_owner','store_admin','test_user']}} },
  { $group: {_id:'$u.username', channels:{$addToSet:'$rid'}} }
]).forEach(printjson);
