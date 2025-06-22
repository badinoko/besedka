db.rocketchat_room.find({t:{$in:['c','p']}},{_id:1,name:1,t:1,fname:1}).forEach(printjson);
