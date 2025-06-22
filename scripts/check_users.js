db.users.find({username:{$in:['owner','admin','store_owner','store_admin','test_user']}},{username:1,roles:1,active:1}).forEach(printjson);
