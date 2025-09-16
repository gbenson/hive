package spooler

import (
	"context"
	"encoding/json"
	"net"
	"net/http"
	net_url "net/url"
	"regexp"
	"strings"
	"sync"
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"

	"gbenson.net/go/logger"
	"gbenson.net/hive/config"
	"gbenson.net/hive/logging/sources/systemd"
	"gbenson.net/hive/util"
)

type Service struct {
	name   string
	log    *logger.Logger
	server *http.Server
	wg     sync.WaitGroup
}

// Start starts the service's goroutines.
func (s *Service) Start(ctx context.Context) (<-chan error, error) {
	s.name = util.ServiceName()
	s.log = logger.Ctx(ctx)

	s.server = &http.Server{
		Addr:         ":5125",
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 5 * time.Minute,
		Handler:      s,
		BaseContext: func(ln net.Listener) context.Context {
			s.log.Debug().
				Str("server_address", ln.Addr().String()).
				Msg("Serving HTTP")
			return ctx
		},
	}

	errC := make(chan error, 1)
	s.wg.Add(1)
	go func() {
		defer s.wg.Done()
		defer s.log.Debug().Msg("Worker exited")

		s.log.Debug().Msg("Starting HTTP server")
		errC <- s.server.ListenAndServe()
	}()

	return errC, nil
}

// Close shuts down the service.
func (s *Service) Close() error {
	if s.server == nil {
		return nil
	}
	defer s.wg.Wait()
	defer s.log.Debug().Msg("Waiting for workers")

	return s.server.Shutdown(context.Background())
}

// authFailedRx matches Mongo authentication errors.
var authFailedRx = regexp.MustCompile(`[Aa]uthentication\s?[Ff]ailed`)

// ServeHTTP handles one HTTP request.
func (s *Service) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	err := s.serveHTTP(w, r)
	if err == nil {
		return
	}

	ctx := r.Context()
	log := logger.Ctx(ctx)

	if mongo.IsNetworkError(err) || mongo.IsTimeout(err) {
		log.Err(err).
			Type("error_type", err).
			Msg("Network error")

		err = HTTPError(http.StatusServiceUnavailable)
	} else if authFailedRx.MatchString(err.Error()) {
		log.Err(err).
			Type("error_type", err).
			Msg("Authentication failed")

		err = HTTPError(http.StatusForbidden)
	}

	if httpError, ok := err.(HTTPError); ok {
		err = httpError.serveHTTP(w, r)
		if err == nil {
			return
		}
	}

	logger.Ctx(r.Context()).
		Err(err).
		Type("type", err).
		Msg("Unhandled error")

	HTTPError(http.StatusInternalServerError).serveHTTP(w, r)
}

func (s *Service) serveHTTP(w http.ResponseWriter, r *http.Request) error {
	ctx := r.Context()
	log := logger.Ctx(ctx)

	if r.Method != "POST" {
		return HTTPError(http.StatusMethodNotAllowed)
	}

	// Get the database credentials.
	creds := net_url.UserPassword(
		r.PostFormValue("u"),
		r.PostFormValue("p"),
	)
	if creds.Username() == "" {
		return HTTPError(http.StatusBadRequest)
	} else if p, _ := creds.Password(); p == "" {
		return HTTPError(http.StatusBadRequest)
	}

	// Get the database configuration.
	const DBHostKey = "mongodb_host"
	const DBNameKey = "mongodb_database"
	prefix := strings.ReplaceAll(s.name, "-", "_") + "_"

	config := config.New(s.name)
	for _, k := range []string{DBHostKey, DBNameKey} {
		config.RegisterAlias(k, prefix+k)
	}

	if err := config.Read(); err != nil {
		return err
	}

	dbname := config.GetString(DBNameKey)

	url := net_url.URL{
		Scheme:   "mongodb",
		Host:     config.GetString(DBHostKey),
		User:     creds,
		Path:     dbname,
		RawQuery: "appname=hive-" + s.name,
	}

	connOpts := options.Client().
		ApplyURI(url.String()).
		SetServerSelectionTimeout(time.Second)

	log.Info().
		Str("uri", util.RedactURL(connOpts.GetURI())).
		Msg("Connecting")

	client, err := mongo.Connect(connOpts)
	if err != nil {
		return err
	}
	defer client.Disconnect(context.WithoutCancel(ctx)) // XXX LoggedClose?

	events := client.Database(dbname).Collection("events")

	findFilter := bson.D{{}}

	findOpts := options.Find().SetSort(bson.D{{
		Key:   "realtime_us",
		Value: 1,
	}})

	cursor, err := events.Find(ctx, findFilter, findOpts)
	if err != nil {
		return err
	}
	defer cursor.Close(context.WithoutCancel(ctx)) // XXX LoggedClose?

	newline := []byte("\n")
	headersSent := false
	for cursor.Next(ctx) {
		var event systemd.JournalEntry
		if err := cursor.Decode(&event); err != nil {
			return err
		}

		b, err := json.Marshal(&event)
		if err != nil {
			return err
		}

		if !headersSent {
			w.Header().Set("Content-Type", "application/jsonl")
			w.WriteHeader(http.StatusOK)
			headersSent = true
		}

		if _, err := w.Write(b); err != nil {
			return err
		} else if _, err := w.Write(newline); err != nil {
			return err
		}
	}
	if err := cursor.Err(); err != nil {
		return err
	}

	return nil
}
