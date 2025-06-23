db.createRole({
  role: "eventIngester",
  privileges: [{
    resource: {
      db: process.env.MONGO_INITDB_DATABASE,
      collection: "events",
    },
    actions: ["insert"],
  }],
  roles: [],
});

db.createUser({
  user: process.env.MONGO_INITDB_USERNAME,
  pwd: process.env.MONGO_INITDB_PASSWORD,
  roles: [
    {role: "eventIngester", db: process.env.MONGO_INITDB_DATABASE},
  ],
});

db.createCollection("events", {
  storageEngine: {
    wiredTiger: {
      configString: "block_compressor=zlib"
    },
  },
});

db.events.createIndex({"digest": 1}, {unique: true});
