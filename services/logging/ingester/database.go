package ingester

import (
	"context"
	net_url "net/url"

	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"

	"gbenson.net/go/logger"
	"gbenson.net/hive/config"
	"gbenson.net/hive/util"
)

// Client is a handle representing a pool of connections to a MongoDB
// deployment. It is safe for concurrent use by multiple goroutines.
type Client struct {
	client     *mongo.Client
	db         *mongo.Database
	Collection *mongo.Collection
}

var configKeys = []string{
	"mongodb_host",
	"mongodb_username",
	"mongodb_password",
	"mongodb_database",
}

// Dial returns a new Client.
func Dial(ctx context.Context) (*Client, error) {
	cfg := config.New("log-ingester")

	for _, k := range configKeys {
		cfg.RegisterAlias(k, "log_ingester_"+k)
	}

	if err := cfg.Read(); err != nil {
		return nil, err
	}

	dbname := cfg.GetString("mongodb_database")
	creds := net_url.UserPassword(
		cfg.GetString("mongodb_username"),
		cfg.GetString("mongodb_password"),
	)

	url := net_url.URL{
		Scheme:   "mongodb",
		Host:     cfg.GetString("mongodb_host"),
		User:     creds,
		Path:     dbname,
		RawQuery: "appname=hive-" + util.ServiceName(),
	}

	opts := options.Client().ApplyURI(url.String())

	logger.Ctx(ctx).Debug().
		Str("uri", util.RedactURL(opts.GetURI())).
		Msg("Dialling")

	client, err := mongo.Connect(opts)
	if err != nil {
		return nil, err
	}

	db := client.Database(dbname)
	coll := db.Collection("events")
	return &Client{client, db, coll}, nil
}

// Close closes the client.
func (c *Client) Close() error {
	return c.client.Disconnect(context.Background())
}
