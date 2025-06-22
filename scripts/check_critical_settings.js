db.rocketchat_settings.find({
  _id: {$in: ['Site_Url', 'Iframe_Restrict_Access', 'Show_Setup_Wizard']}
}, {_id: 1, value: 1}).forEach(printjson);
