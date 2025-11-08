// Package config provides configuration management for Hive.
package config

import (
	"os"
	"path/filepath"
	"time"

	"github.com/spf13/viper"
)

type Config struct {
	v *viper.Viper
}

func New(name string) *Config {
	v := viper.New()

	if dir := os.Getenv("CREDENTIALS_DIRECTORY"); dir != "" {
		v.AddConfigPath(dir)
	}

	if dir, err := os.UserConfigDir(); err == nil {
		v.AddConfigPath(filepath.Join(dir, "hive"))
	}
	v.AddConfigPath("/etc/hive")
	v.AddConfigPath("/run/secrets")

	v.SetConfigName(name)
	v.SetEnvPrefix(name)

	return &Config{v}
}

func (c *Config) Read() error {
	if err := c.v.ReadInConfig(); err == nil {
		return nil
	} else if _, ok := err.(viper.ConfigFileNotFoundError); ok {
		return nil
	} else {
		return err
	}
}

func (c *Config) GetBool(key string) bool {
	return c.v.GetBool(key)
}

func (c *Config) GetDuration(key string) time.Duration {
	return c.v.GetDuration(key)
}

func (c *Config) GetInt(key string) int {
	return c.v.GetInt(key)
}

func (c *Config) GetString(key string) string {
	return c.v.GetString(key)
}

func (c *Config) GetStringMap(key string) map[string]any {
	return c.v.GetStringMap(key)
}

func (c *Config) RegisterAlias(alias, key string) {
	c.v.RegisterAlias(alias, key)
}

func (c *Config) SetDefault(key string, value any) {
	c.v.SetDefault(key, value)
}
