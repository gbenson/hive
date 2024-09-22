package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

func init() {
	if dir, err := os.UserConfigDir(); err == nil {
		addConfigDir(dir)
	}
	addConfigDir("/etc")
}

func addConfigDir(dir string) {
	viper.AddConfigPath(filepath.Join(dir, "hive"))
}

func Read(name string) error {
	viper.SetConfigName(name)
	return viper.ReadInConfig()
}

func GetString(key string) string {
	return viper.GetString(key)
}

func MustGetString(key string) (value string, err error) {
	if value = GetString(key); value == "" {
		err = fmt.Errorf("%s: not set", key)
	}
	return
}

func GetStringSlice(key string) []string {
	return viper.GetStringSlice(key)
}
