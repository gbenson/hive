module gbenson.net/hive

go 1.27.3

require (
	gbenson.net/go/arp v1.0.1
	gbenson.net/go/dfmt v1.0.1
	gbenson.net/go/logger v1.8.0
	github.com/JohannesKaufmann/html-to-markdown/v2 v2.5.2
	github.com/cloudevents/sdk-go/v2 v2.16.2
	github.com/coreos/go-systemd/v22 v22.7.0
	github.com/dnstap/golang-dnstap v0.4.0
	github.com/gertd/go-pluralize v0.2.1
	github.com/google/uuid v1.6.0
	github.com/miekg/dns v1.1.73
	github.com/rabbitmq/amqp091-go v1.16.0
	github.com/rs/zerolog v1.35.1
	github.com/spf13/viper v1.21.0
	go.mongodb.org/mongo-driver/v2 v2.9.2
	golang.org/x/crypto v0.58.0
	golang.org/x/term v0.47.0
	google.golang.org/protobuf v1.36.12
	gotest.tools/v3 v3.5.2
	maunium.net/go/mautrix v0.32.0
)

require (
	filippo.io/edwards25519 v1.2.0 // indirect
	github.com/JohannesKaufmann/dom v0.3.1 // indirect
	github.com/farsightsec/golang-framestream v0.3.0 // indirect
	github.com/fsnotify/fsnotify v1.10.1 // indirect
	github.com/go-viper/mapstructure/v2 v2.5.0 // indirect
	github.com/google/go-cmp v0.7.0 // indirect
	github.com/json-iterator/go v1.1.12 // indirect
	github.com/klauspost/compress v1.20.3 // indirect
	github.com/mattn/go-colorable v0.1.16 // indirect
	github.com/mattn/go-isatty v0.0.24 // indirect
	github.com/mattn/go-sqlite3 v1.14.52 // indirect
	github.com/modern-go/concurrent v0.0.0-20180306012644-bacd9c7ef1dd // indirect
	github.com/modern-go/reflect2 v1.0.2 // indirect
	github.com/pelletier/go-toml/v2 v2.4.3 // indirect
	github.com/petermattis/goid v0.0.0-20260918085751-abfca077860b // indirect
	github.com/sagikazarmark/locafero v0.12.0 // indirect
	github.com/spf13/afero v1.15.0 // indirect
	github.com/spf13/cast v1.10.0 // indirect
	github.com/spf13/pflag v1.0.10 // indirect
	github.com/subosito/gotenv v1.6.0 // indirect
	github.com/tidwall/gjson v1.20.0 // indirect
	github.com/tidwall/match v1.2.0 // indirect
	github.com/tidwall/pretty v1.2.2 // indirect
	github.com/tidwall/sjson v1.2.5 // indirect
	github.com/xdg-go/pbkdf2 v1.0.0 // indirect
	github.com/xdg-go/scram v1.2.0 // indirect
	github.com/xdg-go/stringprep v1.0.4 // indirect
	github.com/youmark/pkcs8 v0.0.0-20240726163527-a2c0da244d78 // indirect
	go.mau.fi/util v0.11.0 // indirect
	go.uber.org/multierr v1.11.0 // indirect
	go.uber.org/zap v1.28.0 // indirect
	go.yaml.in/yaml/v3 v3.0.5 // indirect
	golang.org/x/exp v0.0.0-20261014143641-f0251eb4aa3e // indirect
	golang.org/x/net v0.61.0 // indirect
	golang.org/x/sync v0.24.0 // indirect
	golang.org/x/sys v0.49.0 // indirect
	golang.org/x/text v0.43.0 // indirect
)

retract [v0.0.0, v0.4.1] // Broken module structure
